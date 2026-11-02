import fitz

from backend.app.chunking import create_chunks
from backend.app.embeddings import EmbeddingGenerator
from backend.app.vector_store import VectorStore


PDF_PATH = "sample_documents/company_policy.pdf"


def main():

    # 1. Extract PDF text
    document = fitz.open(PDF_PATH)

    all_chunks = []

    for page_number, page in enumerate(document):

        text = page.get_text()

        if not text.strip():
            continue

        # 2. Create chunks
        chunks = create_chunks(
            text,
            chunk_size=1000,
            overlap=150
        )

        # 3. Preserve metadata
        for chunk_number, chunk in enumerate(chunks):

            all_chunks.append({
                "text": chunk,
                "page": page_number + 1,
                "chunk": chunk_number + 1,
                "source": PDF_PATH
            })

    document.close()

    if not all_chunks:
        print("No text found in PDF.")
        return

    print("Total chunks:", len(all_chunks))

    # 4. Generate embeddings
    generator = EmbeddingGenerator()

    texts = [item["text"] for item in all_chunks]

    embeddings = generator.generate_embeddings(texts)

    # 5. Store in ChromaDB
    store = VectorStore()

    store.add_chunks(all_chunks, embeddings)

    print("PDF successfully indexed!")


if __name__ == "__main__":
    main()