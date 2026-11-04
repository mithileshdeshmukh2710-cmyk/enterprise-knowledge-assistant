import os
import re
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

_shared_client = None
_shared_collection = None


class VectorStore:

    def __init__(self):
        global _shared_client, _shared_collection

        # Persistent database directory
        db_path = Path(
            os.getenv("CHROMA_DB_PATH", "data/chroma_db")
        )
        db_path.mkdir(parents=True, exist_ok=True)

        if _shared_client is None:
            # Create persistent ChromaDB client
            _shared_client = chromadb.PersistentClient(
                path=str(db_path)
            )

            # Create or retrieve collection
            _shared_collection = _shared_client.get_or_create_collection(
                name="enterprise_documents",
                metadata={"hnsw:space": "cosine"}
            )

            print("ChromaDB initialized successfully!")

        self.client = _shared_client
        self.collection = _shared_collection

    def add_chunks(self, chunks, embeddings):

        ids = []
        documents = []
        metadatas = []

        for item in chunks:

            source_name = Path(item["source"]).stem

            chunk_id = (
                f"{source_name}_"
                f"p{item['page']}_"
                f"c{item['chunk']}"
            )

            ids.append(chunk_id)
            documents.append(item["text"])

            metadatas.append({
                "source": item["source"],
                "page": item["page"],
                "chunk": item["chunk"]
            })

        # Insert or update records
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(f"Stored {len(ids)} chunks successfully!")

    def search(self, query_embedding, top_k=3):

        total = self.collection.count()

        # Handle empty database
        if total == 0:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

        # Validate top_k
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, total),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        return results

    STOP_WORDS = {
        "the", "is", "are", "was", "were", "a", "an",
        "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "as",
        "who", "what", "when", "where", "why", "how",
        "which", "find", "show", "tell", "me",
        "can", "could", "would", "should", "does",
        "do", "did", "has", "have", "had"
    }

    @staticmethod
    def tokenize(text):
        """Tokenize text and remove common stop words."""
        tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
        return [
            token for token in tokens
            if token not in VectorStore.STOP_WORDS
        ]

    def hybrid_search(self, query, query_embedding, top_k=3):
        """
        Combine semantic vector search and BM25 keyword search
        using Reciprocal Rank Fusion (RRF).
        """
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        # Fetch all indexed chunks for keyword search.
        stored = self.collection.get(
            include=["documents", "metadatas"]
        )

        ids = stored["ids"]
        documents = stored["documents"] or []
        metadatas = stored["metadatas"] or []

        if not ids:
            return []

        # -------------------------------
        # 1. Semantic vector search
        # -------------------------------
        candidate_k = min(top_k * 3, len(ids))

        vector_results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=candidate_k,
            include=["documents", "metadatas", "distances"]
        )

        vector_ids = vector_results["ids"][0]
        vector_distances = vector_results["distances"][0]
        vector_ranks = {
            doc_id: rank
            for rank, doc_id in enumerate(vector_ids, start=1)
        }
        distance_map = dict(zip(vector_ids, vector_distances))

        # -------------------------------
        # 2. BM25 keyword search
        # -------------------------------
        doc_map = {
            doc_id: (doc, meta)
            for doc_id, doc, meta in zip(ids, documents, metadatas)
        }

        tokenized_documents = [self.tokenize(doc) for doc in documents]
        bm25 = BM25Okapi(tokenized_documents)

        # Floor non-positive IDFs for small corpora so terms in >=50% of docs still match
        for word, val in bm25.idf.items():
            if val <= 0:
                bm25.idf[word] = bm25.epsilon * (bm25.average_idf or 0.25)

        query_tokens = self.tokenize(query)
        scores = bm25.get_scores(query_tokens)

        # Only consider documents containing at least
        # one actual query token.
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )

        matched_documents = []
        for index in ranked_indices:
            document_tokens = set(tokenized_documents[index])
            # Check actual keyword overlap.
            has_keyword_match = any(
                token in document_tokens
                for token in query_tokens
            )
            if has_keyword_match and scores[index] > 0:
                matched_documents.append(index)

        # Assign ranks only to matching documents.
        bm25_ranks = {}
        for rank, index in enumerate(matched_documents[:candidate_k], start=1):
            bm25_ranks[ids[index]] = rank

        # -------------------------------
        # 3. Reciprocal Rank Fusion (RRF)
        # -------------------------------
        rrf_k = 60
        all_candidate_ids = set(vector_ranks.keys()) | set(bm25_ranks.keys())
        rrf_scores = {}

        for doc_id in all_candidate_ids:
            score = 0.0
            if doc_id in vector_ranks:
                score += 1.0 / (rrf_k + vector_ranks[doc_id])
            if doc_id in bm25_ranks:
                score += 1.0 / (rrf_k + bm25_ranks[doc_id])
            rrf_scores[doc_id] = score

        ranked_doc_ids = sorted(
            rrf_scores.keys(),
            key=lambda doc_id: rrf_scores[doc_id],
            reverse=True
        )[:top_k]

        results = []
        for doc_id in ranked_doc_ids:
            doc, meta = doc_map[doc_id]
            results.append({
                "id": doc_id,
                "text": doc,
                "document": doc,
                "metadata": meta,
                "score": rrf_scores[doc_id],
                "rrf_score": rrf_scores[doc_id],
                "vector_rank": vector_ranks.get(doc_id),
                "bm25_rank": bm25_ranks.get(doc_id),
                "vector_distance": distance_map.get(doc_id),
                "bm25_score": scores[ids.index(doc_id)]
                if query_tokens and any(tokenized_documents)
                else 0.0,
            })

        return results

    def count(self):

        return self.collection.count()

    def delete_source(self, source: str):
        self.collection.delete(
            where={"source": source}
        )

    def list_sources(self):
        result = self.collection.get(
            include=["metadatas"]
        )

        documents = {}

        for metadata in result["metadatas"] or []:
            source = metadata["source"]

            if source not in documents:
                documents[source] = {
                    "filename": source,
                    "chunks": 0,
                    "pages": set()
                }

            documents[source]["chunks"] += 1
            documents[source]["pages"].add(metadata["page"])

        return [
            {
                "filename": item["filename"],
                "chunks": item["chunks"],
                "pages": len(item["pages"])
            }
            for item in documents.values()
        ]

    def get_source_content(self, source: str):
        """Retrieve all indexed chunks for one document."""
        result = self.collection.get(
            where={"source": source},
            include=["documents", "metadatas"]
        )
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []
        chunks = []
        for document, metadata in zip(documents, metadatas):
            chunks.append({
                "text": document,
                "page": metadata["page"],
                "chunk": metadata["chunk"]
            })
        # Preserve original document order.
        chunks.sort(
            key=lambda item: (item["page"], item["chunk"])
        )
        return chunks
