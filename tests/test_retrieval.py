import chromadb

from app.services.embedding import generate_embedding
from app.services.vector_store import add_chunks, search_chunks


def test_retrieve_relevant_chunk():
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_retrieval"
    )

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
        ids=["retrieval-test-1"],
        target_collection=test_collection,
    )

    query = "How many casual leave days can employees carry forward?"

    query_embedding = generate_embedding(query)

    results = search_chunks(
        query_embedding=query_embedding,
        top_k=2,
        target_collection=test_collection,
    )

    assert results["documents"]

    retrieved_documents = results["documents"][0]

    assert any(
        "12 casual leave days" in document
        for document in retrieved_documents
    )