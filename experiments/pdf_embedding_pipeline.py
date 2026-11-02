import fitz

from backend.app.chunking import create_chunks
from backend.app.embeddings import EmbeddingGenerator


PDF_PATH = "sample_documents/company_policy.pdf"


def main():

    # Step 1: Extract PDF text
    document = fitz.open(PDF_PATH)

    all_chunks = []

    for page_number, page in enumerate(document):

        text = page.get_text()

        if not text.strip():
            continue

        # Step 2: Create chunks for each page
        chunks = create_chunks(
            text,
            chunk_size=1000,
            overlap=150
        )

        # Step 3: Preserve metadata
        for chunk_number, chunk in enumerate(chunks):

            all_chunks.append({
                "text": chunk,
                "page": page_number + 1,
                "chunk": chunk_number + 1,
                "source": PDF_PATH
            })

    document.close()

    if not all_chunks:
        print("No extractable text found.")
        return

    print("Total chunks:", len(all_chunks))

    # Step 4: Generate embeddings
    generator = EmbeddingGenerator()

    texts = [
        item["text"]
        for item in all_chunks
    ]

    embeddings = generator.generate_embeddings(texts)

    # Step 5: Display results
    print("\nEmbedding shape:", embeddings.shape)

    print("\nFirst chunk metadata:")
    print(all_chunks[0])

    print("\nFirst chunk vector:")
    print(embeddings[0])

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    main()