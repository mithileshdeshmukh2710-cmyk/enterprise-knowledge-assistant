from backend.app.vector_store import VectorStore

store = VectorStore()
print("\nTotal records:", store.count())

data = store.collection.get(
    include=["documents", "metadatas"]
)

print("\nSTORED DOCUMENTS\n")

for i, document in enumerate(data["documents"]):
    metadata = data["metadatas"][i]
    print(f"Record {i + 1}")
    print("Text:", document)
    print("Source:", metadata["source"])
    print("Page:", metadata["page"])
    print("Chunk:", metadata["chunk"])
    print("-" * 40)

