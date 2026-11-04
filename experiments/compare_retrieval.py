import sys
from pathlib import Path

# Ensure backend can be imported
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.embeddings import EmbeddingGenerator
from backend.app.vector_store import VectorStore

EVALUATION_DATASET = [
    {
        "question": "How many days can employees work remotely?",
        "expected_page": 1
    },
    {
        "question": "Who approves annual leave?",
        "expected_page": 2
    },
    {
        "question": "What health insurance benefits are available?",
        "expected_page": 3
    },
    {
        "question": "What technical training is available?",
        "expected_page": 4
    }
]

K = 3


def get_unique_pages(results):
    """Extract unique (source, page) pairs in ranking order."""
    pages = []
    for item in results:
        key = (
            item["metadata"]["source"],
            item["metadata"]["page"]
        )
        if key not in pages:
            pages.append(key)
    return pages


def calculate_metrics(retrieved_pages, expected_page, k=K):
    """Calculate Precision@K, Recall@K, Hit Rate, and Reciprocal Rank."""
    top_pages = [page for _, page in retrieved_pages[:k]]
    hit = 1 if expected_page in top_pages else 0
    precision = hit / k
    recall = float(hit)
    hit_rate = float(hit)

    rr = 0.0
    if expected_page in top_pages:
        rank = top_pages.index(expected_page) + 1
        rr = 1.0 / rank

    return {
        "retrieved_pages": top_pages,
        "precision": precision,
        "recall": recall,
        "hit_rate": hit_rate,
        "mrr": rr
    }


def run_comparison():
    embedder = EmbeddingGenerator()
    store = VectorStore()

    vector_metrics = {
        "precision": [],
        "recall": [],
        "hit_rate": [],
        "mrr": []
    }
    hybrid_metrics = {
        "precision": [],
        "recall": [],
        "hit_rate": [],
        "mrr": []
    }

    print("=" * 80)
    print(f"RETRIEVAL EVALUATION: VECTOR SEARCH vs HYBRID SEARCH (K={K})")
    print("=" * 80)

    for idx, test_case in enumerate(EVALUATION_DATASET, start=1):
        q = test_case["question"]
        expected_page = test_case["expected_page"]
        embedding = embedder.generate_embeddings([q])[0]

        # 1. Vector Search
        raw_vector_results = store.search(embedding, top_k=K)
        vector_items = [
            {"metadata": meta}
            for meta in raw_vector_results["metadatas"][0]
        ]
        v_pages = get_unique_pages(vector_items)
        v_eval = calculate_metrics(v_pages, expected_page, k=K)

        # 2. Hybrid Search
        hybrid_results = store.hybrid_search(
            query=q,
            query_embedding=embedding,
            top_k=K
        )
        h_pages = get_unique_pages(hybrid_results)
        h_eval = calculate_metrics(h_pages, expected_page, k=K)

        for metric in ["precision", "recall", "hit_rate", "mrr"]:
            vector_metrics[metric].append(v_eval[metric])
            hybrid_metrics[metric].append(h_eval[metric])

        print(f"\nQuestion {idx}: {q}")
        print(f"Expected Page: {expected_page}")
        print(f"  Vector Search: Pages={v_eval['retrieved_pages']} | P@{K}={v_eval['precision']:.3f} | R@{K}={v_eval['recall']:.3f} | RR={v_eval['mrr']:.3f}")
        print(f"  Hybrid Search: Pages={h_eval['retrieved_pages']} | P@{K}={h_eval['precision']:.3f} | R@{K}={h_eval['recall']:.3f} | RR={h_eval['mrr']:.3f}")

    num_q = len(EVALUATION_DATASET)
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY COMPARISON")
    print("=" * 80)
    print(f"{'Metric':<28} | {'Vector Search':<16} | {'Hybrid Search':<16} | Difference")
    print("-" * 75)

    for metric, name in [
        ("precision", f"Precision@{K}"),
        ("recall", f"Recall@{K}"),
        ("hit_rate", "Hit Rate"),
        ("mrr", "Mean Reciprocal Rank (MRR)")
    ]:
        v_avg = sum(vector_metrics[metric]) / num_q
        h_avg = sum(hybrid_metrics[metric]) / num_q
        diff = h_avg - v_avg
        diff_str = f"+{diff:.3f}" if diff > 0 else f"{diff:.3f}"
        print(f"{name:<28} | {v_avg:<16.3f} | {h_avg:<16.3f} | {diff_str}")

    print("=" * 80)


if __name__ == "__main__":
    run_comparison()

