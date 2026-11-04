import pytest
try:
    from app.main import build_visual_diff
except ImportError:
    from backend.app.main import build_visual_diff


def test_identical_chunks():
    chunks_a = [{"page": 1, "chunk": 0, "text": "This is a policy. Employees must adhere to it."}]
    chunks_b = [{"page": 1, "chunk": 0, "text": "This is a policy. Employees must adhere to it."}]

    result = build_visual_diff(chunks_a, chunks_b)
    assert result["total_items"] == 2
    assert result["truncated"] is False
    assert all(item["type"] == "unchanged" for item in result["items"])


def test_added_content():
    chunks_a = [{"page": 1, "chunk": 0, "text": "This is a policy."}]
    chunks_b = [
        {"page": 1, "chunk": 0, "text": "This is a policy."},
        {"page": 2, "chunk": 0, "text": "Dental coverage is included."}
    ]

    result = build_visual_diff(chunks_a, chunks_b)
    types = [item["type"] for item in result["items"]]
    assert "unchanged" in types
    assert "added" in types
    added_item = next(item for item in result["items"] if item["type"] == "added")
    assert "Dental coverage is included" in added_item["text"]
    assert added_item["page"] == 2


def test_removed_content():
    chunks_a = [
        {"page": 1, "chunk": 0, "text": "Old obsolete policy rule."},
        {"page": 1, "chunk": 1, "text": "Standard work hours apply."}
    ]
    chunks_b = [
        {"page": 1, "chunk": 0, "text": "Standard work hours apply."}
    ]

    result = build_visual_diff(chunks_a, chunks_b)
    types = [item["type"] for item in result["items"]]
    assert "removed" in types
    assert "unchanged" in types
    removed_item = next(item for item in result["items"] if item["type"] == "removed")
    assert "Old obsolete policy rule" in removed_item["text"]


def test_chunk_overlap_deduplication():
    # Simulating RAG chunk overlap where the same sentence appears at the end of chunk 0 and start of chunk 1
    chunks = [
        {"page": 1, "chunk": 0, "text": "First sentence. Overlapping sentence."},
        {"page": 1, "chunk": 1, "text": "Overlapping sentence. Next sentence."}
    ]

    result = build_visual_diff(chunks, chunks)
    texts = [item["text"] for item in result["items"]]
    # "Overlapping sentence." should only appear once
    assert texts.count("Overlapping sentence.") == 1


def test_truncation():
    chunks_a = [{"page": i, "chunk": 0, "text": f"Sentence number {i} in document A."} for i in range(1, 15)]
    chunks_b = [{"page": i, "chunk": 0, "text": f"Sentence number {i} in document B."} for i in range(1, 15)]

    result = build_visual_diff(chunks_a, chunks_b, max_items=5)
    assert len(result["items"]) == 5
    assert result["truncated"] is True
    assert result["total_items"] > 5


def test_modified_content_detection():
    chunks_a = [{"page": 1, "chunk": 0, "text": "Employees can work remotely up to two days per week."}]
    chunks_b = [{"page": 1, "chunk": 0, "text": "Employees can work remotely up to three days per week."}]

    result = build_visual_diff(chunks_a, chunks_b)
    assert result["total_items"] == 1
    item = result["items"][0]
    assert item["type"] == "modified"
    assert "two days" in item["old_text"]
    assert "three days" in item["new_text"]
    assert item["similarity"] >= 0.60


def test_user_expected_policy_comparison():
    chunks_a = [{
        "page": 1,
        "chunk": 0,
        "text": (
            "Remote work: two days per week. "
            "Annual leave requires manager approval. "
            "Employees must follow company security policies."
        )
    }]
    chunks_b = [{
        "page": 1,
        "chunk": 0,
        "text": (
            "Remote work: three days per week. "
            "Annual leave requires manager approval. "
            "Employees must follow company security policies. "
            "Employees must complete annual security training."
        )
    }]

    result = build_visual_diff(chunks_a, chunks_b)
    types = [item["type"] for item in result["items"]]

    assert types.count("modified") == 1
    assert types.count("unchanged") == 2
    assert types.count("added") == 1
    assert types.count("removed") == 0

    modified = next(item for item in result["items"] if item["type"] == "modified")
    assert "two days" in modified["old_text"]
    assert "three days" in modified["new_text"]


