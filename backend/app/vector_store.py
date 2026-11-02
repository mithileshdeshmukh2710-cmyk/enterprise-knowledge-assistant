
import chromadb
from pathlib import Path


class VectorStore:

    def __init__(self):

        # Persistent database directory
        db_path = Path("data/chroma_db")
        db_path.mkdir(parents=True, exist_ok=True)

        # Create persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(db_path)
        )

        # Create or retrieve collection
        self.collection = self.client.get_or_create_collection(
            name="enterprise_documents",
            metadata={"hnsw:space": "cosine"}
        )

        print("ChromaDB initialized successfully!")

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

    def count(self):

        return self.collection.count()
