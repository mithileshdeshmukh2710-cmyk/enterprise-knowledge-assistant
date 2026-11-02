def clean_text(text: str) -> str:
    """
    Clean extracted document text.
    """

    # Remove unnecessary whitespace
    text = " ".join(text.split())

    return text


def create_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150
):
    """
    Divide text into overlapping chunks.
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size"
        )

    text = clean_text(text)

    chunks = []

    start = 0

    while start < len(text):

        end = min(start + chunk_size, len(text))

        chunk = text[start:end]

        chunks.append(chunk)

        if end == len(text):
            break

        start += chunk_size - overlap

    return chunks