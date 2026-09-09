import pytest

from app.services.keyword_search import KeywordIndex, tokenize


def test_tokenize_is_case_insensitive():
    assert tokenize("Premium Dental Coverage") == [
        "premium",
        "dental",
        "coverage",
    ]


def test_keyword_search_ranks_matching_chunk_first():
    index = KeywordIndex()

    index.build(
        texts=[
            "Standard plan does not cover dental implants.",
            "Premium plan covers dental implants up to 50,000.",
            "Employees receive 12 casual leave days.",
        ],
        ids=[
            "standard",
            "premium",
            "leave",
        ],
    )

    results = index.search(
        query="Premium dental implants",
        top_k=2,
    )

    assert results[0][0] == "premium"


def test_keyword_search_returns_empty_for_blank_query():
    index = KeywordIndex()

    index.build(
        texts=["Premium plan covers dental implants."],
        ids=["premium"],
    )

    assert index.search("   ") == []


def test_keyword_index_rejects_mismatched_lengths():
    index = KeywordIndex()

    with pytest.raises(
        ValueError,
        match="texts and ids must have the same length.",
    ):
        index.build(
            texts=["one"],
            ids=["one", "two"],
        )

def test_rebuild_keyword_index_removes_deleted_chunks():
    from app.services.keyword_search import (
        keyword_index,
        rebuild_keyword_index,
    )

    rebuild_keyword_index(
        texts=[
            "Standard plan does not cover dental implants.",
            "Premium plan covers dental implants.",
        ],
        ids=[
            "standard",
            "premium",
        ],
    )

    assert keyword_index.search(
        "standard dental implants",
        top_k=1,
    )[0][0] == "standard"

    rebuild_keyword_index(
        texts=[
            "Premium plan covers dental implants.",
        ],
        ids=[
            "premium",
        ],
    )

    results = keyword_index.search(
        "standard dental implants",
        top_k=5,
    )

    assert all(
        chunk_id != "standard"
        for chunk_id, _ in results
    )