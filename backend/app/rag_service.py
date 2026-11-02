from backend.app.embeddings import EmbeddingGenerator
from backend.app.vector_store import VectorStore
from backend.app.gemini_client import GeminiClient
from backend.app.prompts import SYSTEM_PROMPT


class RAGService:

    def __init__(self):

        print("Initializing RAG service...")

        self.embedding_generator = EmbeddingGenerator()

        self.vector_store = VectorStore()

        self.gemini = GeminiClient()

        print("RAG service initialized!")

    def ask_question(self, question: str, top_k: int = 3):

        # Step 1: Generate question embedding
        query_embedding = (
            self.embedding_generator
            .generate_embeddings([question])[0]
        )

        # Step 2: Retrieve relevant chunks
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        if not documents:
            return {
                "answer": (
                    "No documents have been indexed yet. "
                    "Please upload a document first."
                ),
                "sources": []
            }

        # Step 3: Build context
        context_parts = []
        sources = []

        for document, metadata in zip(documents, metadatas):

            source = metadata.get("source", "Unknown")
            page = metadata.get("page", "Unknown")

            context_parts.append(
                f"""
                <document_chunk>
                Source: {source}
                Page: {page}
                Content:
                {document}
                </document_chunk>
                """
            )

            source_info = {
                "source": source,
                "page": page
            }

            if source_info not in sources:
                sources.append(source_info)

        context = "\n".join(context_parts)

        # Step 4: Build final prompt
        prompt = SYSTEM_PROMPT.format(
            context=context,
            question=question
        )

        # Step 5: Generate answer using Gemini
        answer = self.gemini.generate_answer(prompt)

        # Step 6: Return answer and sources
        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }