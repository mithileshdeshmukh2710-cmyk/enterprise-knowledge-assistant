from backend.app.embeddings import EmbeddingGenerator
from backend.app.vector_store import VectorStore
from experiments.evaluation_dataset import EVALUATION_DATASET


def evaluate_retrieval(top_k=3):

    embedding_generator = EmbeddingGenerator()
    vector_store = VectorStore()

    total_precision = 0
    total_recall = 0
    total_hit_rate = 0
    total_reciprocal_rank = 0

    evaluated_questions = 0

    for test_case in EVALUATION_DATASET:

        question = test_case["question"]
        relevant_sources = test_case["relevant_sources"]

        query_embedding = embedding_generator.generate_embeddings(
            [question]
        )[0]

        results = vector_store.search(
            query_embedding,
            top_k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        retrieved = [
            {
                "source": metadata["source"],
                "page": metadata["page"]
            }
            for metadata in metadatas
        ]

        relevant_set = {
            (item["source"], item["page"])
            for item in relevant_sources
        }

        retrieved_set = {
            (item["source"], item["page"])
            for item in retrieved
        }

        relevant_count = sum(
            1 for item in retrieved
            if (item["source"], item["page"]) in relevant_set
        )

        precision = relevant_count / top_k

        recall = (
            relevant_count / len(relevant_set)
            if relevant_set else 0
        )

        hit_rate = 1 if relevant_count > 0 else 0

        reciprocal_rank = 0

        for rank, item in enumerate(retrieved, start=1):
            if (item["source"], item["page"]) in relevant_set:
                reciprocal_rank = 1 / rank
                break

        total_precision += precision
        total_recall += recall
        total_hit_rate += hit_rate
        total_reciprocal_rank += reciprocal_rank

        evaluated_questions += 1

        print(f"\nQuestion: {question}")
        print(f"Retrieved: {retrieved}")
        print(f"Precision@{top_k}: {precision:.2f}")
        print(f"Recall@{top_k}: {recall:.2f}")
        print(f"Hit Rate: {hit_rate}")
        print(f"Reciprocal Rank: {reciprocal_rank:.2f}")

    if evaluated_questions == 0:
        print("No evaluation questions found.")
        return

    print("\n========== FINAL RESULTS ==========")

    print(
        "Average Precision@K:",
        round(total_precision / evaluated_questions, 3)
    )

    print(
        "Average Recall@K:",
        round(total_recall / evaluated_questions, 3)
    )

    print(
        "Hit Rate@K:",
        round(total_hit_rate / evaluated_questions, 3)
    )

    print(
        "MRR:",
        round(total_reciprocal_rank / evaluated_questions, 3)
    )


if __name__ == "__main__":
    evaluate_retrieval(top_k=3)