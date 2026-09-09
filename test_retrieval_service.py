from app.services.retrieval import (
    RetrievedChunk,
    reciprocal_rank_fusion,
)


def test_reciprocal_rank_fusion_rewards_multiple_rankings():
    result = reciprocal_rank_fusion(
        rankings=[
            ["a", "b", "c"],
            ["c", "a", "d"],
        ],
        top_k=4,
    )

    assert result[0] == "a"
    assert result[1] == "c"
    assert set(result) == {"a", "b", "c", "d"}
