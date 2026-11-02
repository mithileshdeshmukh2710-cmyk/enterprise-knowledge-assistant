from sklearn.metrics.pairwise import cosine_similarity

from backend.app.embeddings import EmbeddingGenerator


sentences = [
    "Employees can work remotely.",
    "Staff members are allowed to work from home.",
    "The company provides health insurance."
]

generator = EmbeddingGenerator()

embeddings = generator.generate_embeddings(sentences)

similarity_matrix = cosine_similarity(embeddings)

print("\nCOSINE SIMILARITY MATRIX\n")

for i in range(len(sentences)):

    for j in range(len(sentences)):

        print(
            f"{similarity_matrix[i][j]:.4f}",
            end="     "
        )

    print()

print("\nSentence 1:", sentences[0])
print("Sentence 2:", sentences[1])
print("Sentence 3:", sentences[2])