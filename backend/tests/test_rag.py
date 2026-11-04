import pytest

def test_distance_cutoff_logic():
    MAX_DISTANCE = 0.55
    MAX_BM25_RANK = 2

    # Case 1: Semantic match within cutoff (distance <= 0.55)
    distance = 0.35
    bm25_rank = 5
    bm25_score = 0.5
    semantic_match = distance is not None and distance <= MAX_DISTANCE
    keyword_match = bm25_rank is not None and bm25_rank <= MAX_BM25_RANK and bm25_score > 0
    assert (semantic_match or keyword_match) is True

    # Case 2: Semantic match too distant (> 0.55), but top BM25 keyword match
    distance = 0.75
    bm25_rank = 1
    bm25_score = 2.1
    semantic_match = distance is not None and distance <= MAX_DISTANCE
    keyword_match = bm25_rank is not None and bm25_rank <= MAX_BM25_RANK and bm25_score > 0
    assert (semantic_match or keyword_match) is True

    # Case 3: Distant semantic match (> 0.55) AND poor BM25 rank (> 2) -> excluded
    distance = 0.82
    bm25_rank = 4
    bm25_score = 0.2
    semantic_match = distance is not None and distance <= MAX_DISTANCE
    keyword_match = bm25_rank is not None and bm25_rank <= MAX_BM25_RANK and bm25_score > 0
    assert (semantic_match or keyword_match) is False

    # Case 4: No keyword match (score <= 0) and distant vector
    distance = 0.65
    bm25_rank = 1
    bm25_score = 0
    semantic_match = distance is not None and distance <= MAX_DISTANCE
    keyword_match = bm25_rank is not None and bm25_rank <= MAX_BM25_RANK and bm25_score > 0
    assert (semantic_match or keyword_match) is False

