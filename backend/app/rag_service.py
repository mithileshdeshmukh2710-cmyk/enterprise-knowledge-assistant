try:
    from app.embeddings import EmbeddingGenerator
    from app.vector_store import VectorStore
    from app.gemini_client import GeminiClient
    from app.prompts import SYSTEM_PROMPT
except ImportError:
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

        results = self.vector_store.hybrid_search(
            query=retrieval_query,
            query_embedding=query_embedding,
            top_k=top_k
        )

        MAX_DISTANCE = 0.55
        MAX_BM25_RANK = 2

        relevant_chunks = []

        for item in results:
            distance = item["vector_distance"]
            bm25_rank = item["bm25_rank"]
            bm25_score = item["bm25_score"]

            semantic_match = (
                distance is not None
                and distance <= MAX_DISTANCE
            )

            keyword_match = (
                bm25_rank is not None
                and bm25_rank <= MAX_BM25_RANK
                and bm25_score > 0
            )

            if semantic_match or keyword_match:
                relevant_chunks.append({
                    "text": item["text"],
                    "metadata": item["metadata"],
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
                "distance": round(item["distance"], 4) if item["distance"] is not None else None
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
