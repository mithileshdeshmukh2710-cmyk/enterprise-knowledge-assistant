from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load a pretrained embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Sentences to compare
sentences = [
    "I love programming in Python",
    "I enjoy writing code",
    "The weather is very cold today"
]

# Convert sentences into embeddings
embeddings = model.encode(sentences)

# Calculate cosine similarity
similarity = cosine_similarity(embeddings)

print("Similarity Matrix:\n")

for i in range(len(sentences)):
    for j in range(len(sentences)):
        print(
            f"Sentence {i+1} vs Sentence {j+1}: "
            f"{similarity[i][j]:.4f}"
        )