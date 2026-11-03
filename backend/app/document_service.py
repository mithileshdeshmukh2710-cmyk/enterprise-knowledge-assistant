import fitz
from pathlib import Path

from app.chunking import create_chunks
from app.embeddings import EmbeddingGenerator
from app.vector_store import VectorStore


class DocumentService:

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()

    def index_pdf(self, pdf_path: str, filename: str):

        pdf = fitz.open(pdf_path)

        all_chunks = []

        for page_number, page in enumerate(pdf, start=1):

            text = page.get_text()

            if not text.strip():
                continue

            page_chunks = create_chunks(
                text,
                chunk_size=1000,
                overlap=150
            )

            for chunk_number, chunk_text in enumerate(page_chunks):

                all_chunks.append({
                    "text": chunk_text,
                    "source": filename,
                    "page": page_number,
                    "chunk": chunk_number
                })

        pdf.close()

        if not all_chunks:
            raise ValueError(
                "No readable text found in this PDF."
            )

        # Generate embeddings
        texts = [item["text"] for item in all_chunks]

        embeddings = self.embedding_generator.generate_embeddings(
            texts
        )

        # Replace old version of this document
        self.vector_store.delete_source(filename)

        # Save chunks and embeddings
        self.vector_store.add_chunks(
            all_chunks,
            embeddings
        )

        return {
            "filename": filename,
            "pages": len(set(item["page"] for item in all_chunks)),
            "chunks_indexed": len(all_chunks)
        }
