from backend.app.vector_store import VectorStore

store = VectorStore()

print("Stored records:", store.count())