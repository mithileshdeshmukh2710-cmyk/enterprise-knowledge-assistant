import fitz
from app.chunking import create_chunks
from app.embeddings import EmbeddingGenerator
from app.vector_store import VectorStore


class DocumentService:

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()

    def index_pdf(self, pdf_path: str, filename: str):
        pdf = fitz.open(pdf_path)

        try:
            total_pages = 0
            total_chunks = 0
            batch_size = 32
            batch = []

            # Replace the previous version of this document.
            self.vector_store.delete_source(filename)

            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text()
                if not text.strip():
                    continue

                total_pages += 1

                page_chunks = create_chunks(
                    text,
                    chunk_size=1000,
                    overlap=150
                )

                for chunk_number, chunk_text in enumerate(page_chunks):
                    batch.append({
                        "text": chunk_text,
                        "source": filename,
                        "page": page_number,
                        "chunk": chunk_number
                    })
                    total_chunks += 1

                    if len(batch) >= batch_size:
                        texts = [item["text"] for item in batch]
                        embeddings = self.embedding_generator.generate_embeddings(texts)
                        self.vector_store.add_chunks(batch, embeddings)
                        batch = []

            # Process any remaining chunks in the last batch
            if batch:
                texts = [item["text"] for item in batch]
                embeddings = self.embedding_generator.generate_embeddings(texts)
                self.vector_store.add_chunks(batch, embeddings)
                batch = []

            if total_chunks == 0:
                raise ValueError("No readable text found in this PDF.")

            return {
                "filename": filename,
                "pages": total_pages,
                "chunks_indexed": total_chunks
            }

        finally:
            pdf.close()
