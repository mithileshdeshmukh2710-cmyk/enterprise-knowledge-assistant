import torch
from sentence_transformers import SentenceTransformer

# Limit PyTorch threads to reduce container memory footprint on Render free tier (512MB RAM)
torch.set_num_threads(1)

_shared_model = None


class EmbeddingGenerator:

    def __init__(self):
        global _shared_model
        if _shared_model is None:
            print("Loading embedding model...")
            _shared_model = SentenceTransformer(
                "all-MiniLM-L6-v2",
                device="cpu"
            )
            print("Embedding model loaded!")

        self.model = _shared_model

    def generate_embeddings(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )


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
