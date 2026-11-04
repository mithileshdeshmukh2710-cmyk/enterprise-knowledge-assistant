import pytest

try:
    from app.chunking import clean_text, create_chunks
except ImportError:
    from backend.app.chunking import clean_text, create_chunks


def test_clean_text():
    raw = "  Hello   world!\n\nThis is a   test. \t"
    cleaned = clean_text(raw)
    assert cleaned == "Hello world! This is a test."


def test_create_chunks_small_text():
    text = "Short policy text."
    chunks = create_chunks(text, chunk_size=100, overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == "Short policy text."


def test_create_chunks_overlapping():
    text = "A" * 150
    chunks = create_chunks(text, chunk_size=100, overlap=30)
    assert len(chunks) == 2
    assert len(chunks[0]) == 100
    # Next chunk starts at 100 - 30 = 70, ends at min(70+100, 150) = 150
    assert len(chunks[1]) == 80


def test_create_chunks_invalid_parameters():
    with pytest.raises(ValueError, match="Chunk size must be positive"):
        create_chunks("test", chunk_size=0, overlap=0)

    with pytest.raises(ValueError, match="smaller than chunk size"):
        create_chunks("test", chunk_size=100, overlap=100)

    with pytest.raises(ValueError, match="smaller than chunk size"):
        create_chunks("test", chunk_size=100, overlap=120)

    with pytest.raises(ValueError, match="smaller than chunk size"):
        create_chunks("test", chunk_size=100, overlap=-5)

