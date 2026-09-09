from unittest.mock import patch

import chromadb

from app.services.embedding import generate_embedding
from app.services.retrieval import (
    RetrievedChunk,
    reciprocal_rank_fusion,
    retrieve_chunks,
)
from app.services.vector_store import add_chunks


def test_retrieved_chunk_structure():
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_retrieval_service",
    )

    text = "Employees can carry forward up to 12 casual leave days."

    add_chunks(
        texts=[text],
        embeddings=[generate_embedding(text)],
        metadatas=[
            {
                "document": "leave_policy.md",
                "section": "Casual Leave",
                "page": "",
            }
        ],
        ids=["retrieval-service-test-1"],
        target_collection=test_collection,
    )

    results = test_collection.query(
        query_embeddings=[
            generate_embedding(
                "How many casual leave days can employees carry forward?"
            )
        ],
        n_results=1,
    )

    chunk = RetrievedChunk(
        text=results["documents"][0][0],
        document=results["metadatas"][0][0]["document"],
        section=results["metadatas"][0][0]["section"],
        page=results["metadatas"][0][0]["page"],
        distance=results["distances"][0][0],
        chunk_id=results["ids"][0][0],
    )

    assert chunk.text
    assert chunk.document == "leave_policy.md"
    assert chunk.section == "Casual Leave"


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


def test_retrieval_can_return_bm25_only_candidate():
    vector_results = {
        "documents": [["semantic chunk"]],
        "metadatas": [[
            {
                "document": "policy.md",
                "section": "Section A",
                "page": "",
            }
        ]],
        "distances": [[0.2]],
        "ids": [["vector-chunk"]],
    }

    keyword_results = [
        ("keyword-chunk", 10.0),
    ]

    with patch(
        "app.services.retrieval.generate_embedding",
        return_value=[0.1],
    ), patch(
        "app.services.retrieval.search_chunks",
        return_value=vector_results,
    ), patch(
        "app.services.retrieval.keyword_index.search",
        return_value=keyword_results,
    ), patch(
        "app.services.retrieval.get_chunks_by_ids",
        return_value={
            "documents": [
                "semantic chunk",
                "keyword-only chunk",
            ],
            "metadatas": [
                {
                    "document": "policy.md",
                    "section": "Section A",
                    "page": "",
                },
                {
                    "document": "policy.md",
                    "section": "Section B",
                    "page": "",
                },
            ],
            "ids": [
                "vector-chunk",
                "keyword-chunk",
            ],
        },
    ):
        chunks = retrieve_chunks(
            query="exact policy term",
            top_k=2,
        )

    assert len(chunks) == 2
    assert "keyword-chunk" in {
        chunk.chunk_id
        for chunk in chunks
    }