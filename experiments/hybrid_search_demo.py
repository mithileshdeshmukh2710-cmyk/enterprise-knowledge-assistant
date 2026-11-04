from backend.app.embeddings import EmbeddingGenerator
from backend.app.vector_store import VectorStore

QUERIES = [
    "Who gives permission for working remotely?",
    "Find the exact term manager approval",
    "How many days can employees work from home?",
    "What medical coverage does the company provide?",
    "Which training programs help employees improve their skills?"
]


def main():
    store = VectorStore()
    embedder = EmbeddingGenerator()

    for query in QUERIES:
        embedding = embedder.generate_embeddings([query])[0]

        # Vector-only search
        vector_results = store.search(embedding, top_k=3)

        # Hybrid search
        hybrid_results = store.hybrid_search(
            query=query,
            query_embedding=embedding,
            top_k=3
        )

        print("\n" + "=" * 75)
        print("QUERY:", query)

        print("\nVECTOR SEARCH:")
        for i, metadata in enumerate(vector_results["metadatas"][0]):
            dist = vector_results["distances"][0][i]
            print(f"  Rank {i + 1}: {metadata['source']} - Page {metadata['page']} (Distance: {dist:.4f})")

        print("\nHYBRID SEARCH:")
        for i, result in enumerate(hybrid_results):
            print(
                f"  Rank {i + 1}: {result['metadata']['source']} - Page {result['metadata']['page']} "
                f"(RRF: {result['rrf_score']:.5f}, Vector: {result['vector_rank']}, BM25: {result['bm25_rank']})"
            )


if __name__ == "__main__":
    main()
