import chromadb

from app.services.embedding import generate_embedding
from app.services.vector_store import (
    add_chunks,
    delete_document,
    replace_document,
    search_chunks,
)


def test_vector_store_search():
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_hr_policies"
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
        ids=["test-casual-leave-1"],
        target_collection=test_collection,
    )

    query_embedding = generate_embedding(
        "How many casual leave days can I carry forward?"
    )

    results = search_chunks(
        query_embedding,
        top_k=1,
        target_collection=test_collection,
    )

    assert results["documents"]
    assert "12 casual leave days" in results["documents"][0][0]


def test_delete_document():
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_delete_document"
    )

    text = "Employees receive 12 casual leave days."

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
        ids=["delete-test-1"],
        target_collection=test_collection,
    )

    deleted = delete_document(
        "leave_policy.md",
        target_collection=test_collection,
    )

    assert deleted == 1

    results = test_collection.get()

    assert results["ids"] == []


def test_replace_document():
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_replace_document"
    )

    old_text = "Employees receive 12 casual leave days."
    old_embedding = generate_embedding(old_text)

    add_chunks(
        texts=[old_text],
        embeddings=[old_embedding],
        metadatas=[
            {
                "document": "leave_policy.md",
                "section": "Casual Leave",
                "page": "",
            }
        ],
        ids=["replace-test-old"],
        target_collection=test_collection,
    )

    new_text = "Employees receive 15 casual leave days."
    new_embedding = generate_embedding(new_text)

    replace_document(
        document="leave_policy.md",
        texts=[new_text],
        embeddings=[new_embedding],
        metadatas=[
            {
                "document": "leave_policy.md",
                "section": "Casual Leave",
                "page": "",
            }
        ],
        ids=["replace-test-new"],
        target_collection=test_collection,
    )

    results = test_collection.get()

    assert results["ids"] == ["replace-test-new"]
    assert results["documents"] == [new_text]