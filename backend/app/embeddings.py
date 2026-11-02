
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:

    def __init__(self):
        print("Loading embedding model...")

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("Embedding model loaded!")

    def generate_embeddings(self, texts):

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return embeddings


# Testing the embedding generator
if __name__ == "__main__":

    print("Starting embedding test...")

    generator = EmbeddingGenerator()

    texts = [
        "Employees are entitled to annual leave.",
        "Employees can apply for medical leave.",
        "The company provides health insurance."
    ]

    embeddings = generator.generate_embeddings(texts)

    print("\nEmbedding shape:", embeddings.shape)
    print("\nFirst embedding:", embeddings[0])
    print("\nEmbedding generation successful!")
