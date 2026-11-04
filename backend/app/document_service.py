import logging
import fitz
try:
    from app.chunking import create_chunks
    from app.embeddings import EmbeddingGenerator
    from app.vector_store import VectorStore
    from app.gemini_client import GeminiClient
    from app.document_metadata import DocumentMetadataStore
except ImportError:
    from backend.app.chunking import create_chunks
    from backend.app.embeddings import EmbeddingGenerator
    from backend.app.vector_store import VectorStore
    from backend.app.gemini_client import GeminiClient
    from backend.app.document_metadata import DocumentMetadataStore

logger = logging.getLogger(__name__)


class DocumentService:

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.gemini = GeminiClient()
        self.metadata_store = DocumentMetadataStore()

    def index_pdf(self, pdf_path: str, filename: str):
        pdf = fitz.open(pdf_path)
        all_chunks = []
        document_text_parts = []
        total_pages = 0

        try:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text()
                if not text.strip():
                    continue

                document_text_parts.append(text)
                total_pages += 1

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

            if not all_chunks:
                raise ValueError("No readable text found in this PDF.")

            # Generate document summary first
            summary = None
            summary_status = "failed"
            try:
                full_document_text = "\n\n".join(document_text_parts)
                summary = self.gemini.generate_document_summary(full_document_text)
                summary_status = "completed"
            except Exception as error:
                logger.warning("Document summarization failed for %s: %s", filename, error)
                summary = f"Summary could not be generated: {error}"
                summary_status = "failed"

            # Replace previous version of this document in vector store
            self.vector_store.delete_source(filename)

            # Index chunks in batches of 32 to preserve memory
            batch_size = 32
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                texts = [item["text"] for item in batch]
                embeddings = self.embedding_generator.generate_embeddings(texts)
                self.vector_store.add_chunks(batch, embeddings)

            # Save persistent document metadata
            metadata = {
                "summary": summary,
                "summary_status": summary_status,
                "pages": len(set(item["page"] for item in all_chunks)),
                "chunks_indexed": len(all_chunks)
            }
            self.metadata_store.save(filename, metadata)

            return {
                "filename": filename,
                "pages": total_pages,
                "chunks_indexed": len(all_chunks),
                "summary": summary,
                "summary_status": summary_status
            }

        finally:
            pdf.close()

    def list_documents(self):
        documents = self.vector_store.list_sources()
        all_metadata = self.metadata_store.get_all()
        for document in documents:
            saved = all_metadata.get(document["filename"], {})
            document["summary"] = saved.get("summary")
            document["summary_status"] = saved.get(
                "summary_status", "unavailable"
            )
            document["updated_at"] = saved.get("updated_at")
        return documents

    def get_summary(self, filename):
        return self.metadata_store.get(filename)

    def delete_document(self, filename):
        self.vector_store.delete_source(filename)
        self.metadata_store.delete(filename)
