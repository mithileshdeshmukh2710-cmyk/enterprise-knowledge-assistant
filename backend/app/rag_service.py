from app.embeddings import EmbeddingGenerator
from app.vector_store import VectorStore
from app.gemini_client import GeminiClient
from app.prompts import SYSTEM_PROMPT


class RAGService:

    def __init__(self):

        print("Initializing RAG service...")

        self.embedding_generator = EmbeddingGenerator()

        self.vector_store = VectorStore()

        self.gemini = GeminiClient()

        print("RAG service initialized!")

    def ask_question(self, question, top_k=3, history=None):
        history = history or []

        previous_user_questions = [
            message["content"]
            for message in (history or [])[-6:]
            if message.get("role") == "user"
            and isinstance(message.get("content"), str)
        ]
        retrieval_query = " ".join(
            previous_user_questions[-2:] + [question]
        )
        query_embedding = self.embedding_generator.generate_embeddings(
            [retrieval_query]
        )[0]

        results = self.vector_store.search(
            query_embedding,
            top_k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Keep only sufficiently relevant chunks.
        MAX_DISTANCE = 0.55

        relevant_chunks = []

        for document, metadata, distance in zip(
            documents, metadatas, distances
        ):
            if distance <= MAX_DISTANCE:
                relevant_chunks.append({
                    "text": document,
                    "metadata": metadata,
                    "distance": distance
                })

        if not relevant_chunks:
            return {
                "question": question,
                "answer": (
                    "I could not find sufficiently relevant information "
                    "in the uploaded documents to answer this question."
                ),
                "sources": []
            }

        context_parts = []
        sources = []

        for item in relevant_chunks:

            metadata = item["metadata"]

            context_parts.append(
                f"""
            Source: {metadata['source']}
            Page: {metadata['page']}
            Content: {item['text']}
            """
            )

            source = {
                "source": metadata["source"],
                "page": metadata["page"],
                "distance": round(item["distance"], 4)
            }

            if source not in sources:
                sources.append(source)

        context = "\n".join(context_parts)

        history_text = ""
        for message in history[-6:]:
            role = message.get("role", "")
            content = message.get("content", "")
            if role in ["user", "assistant"] and isinstance(content, str):
                history_text += f"{role.upper()}: {content[:2000]}\n"

        prompt = SYSTEM_PROMPT.format(
            context=context,
            question=question
        )

        prompt += f"""
Recent conversation:
{history_text}
Use the recent conversation only to understand references
and follow-up questions. Answer factual questions using
the retrieved document context. If the documents do not
support the answer, say that the information could not
be found."""

        answer = self.gemini.generate_answer(prompt)

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }
