
from backend.app.embeddings import EmbeddingGenerator
from backend.app.vector_store import VectorStore


# Sample documents
chunks = [
    {
        "text": "Employees can work remotely two days per week.",
        "page": 1,
        "chunk": 1,
        "source": "company_policy.pdf"
    },
    {
        "text": "Annual leave requires manager approval.",
        "page": 2,
        "chunk": 1,
        "source": "company_policy.pdf"
    },
    {
        "text": "Employees receive health insurance benefits.",
        "page": 3,
        "chunk": 1,
        "source": "company_policy.pdf"
    },
    {
        "text": "The company provides technical training to employees.",
        "page": 4,
        "chunk": 1,
        "source": "company_policy.pdf"
    }
]


def main():

    # Step 1: Generate embeddings
    generator = EmbeddingGenerator()

    texts = [item["text"] for item in chunks]

    embeddings = generator.generate_embeddings(texts)

    # Step 2: Initialize vector database
    store = VectorStore()

    # Step 3: Store chunks
    store.add_chunks(chunks, embeddings)

    print("\nTotal records:", store.count())

    # Step 4: Search
    questions = [
        "How many days can employees work from home?",
        "Who approves annual leave?",
        "What health benefits are available?",
        "Does the company provide employee training?"
    ]

    # Step 5: Search each question
    for question in questions:

        print("\nQUESTION:", question)

        query_embedding = generator.generate_embeddings(
            [question]
        )[0]

        results = store.search(
            query_embedding,
            top_k=3
        )

        # Step 6: Display results
        for i, document in enumerate(results["documents"][0]):

            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            print(f"\nResult {i + 1}")
            print("Text:", document)
            print("Source:", metadata["source"])
            print("Page:", metadata["page"])
            print("Distance:", round(distance, 4))
            print("-" * 40)


if __name__ == "__main__":
    main()
