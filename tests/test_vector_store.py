from app.services.embedding import generate_embedding
from app.services.vector_store import add_chunks, search_chunks


def test_vector_store_search():
    text = "Employees can carry forward up to 12 casual leave days."

    embedding = generate_embedding(text)

    add_chunks(
        texts=[text],
        embeddings=[embedding],
        metadatas=[
            {
                "document": "leave_policy.md",
                "section": "Casual Leave",
                "page": "",
            }
        ],
        ids=["test-casual-leave-1"],
    )

    query_embedding = generate_embedding(
        "How many casual leave days can I carry forward?"
    )

    results = search_chunks(query_embedding, top_k=1)

    assert results["documents"]
    assert "12 casual leave days" in results["documents"][0][0]