import chromadb

from app.services.embedding import generate_embedding
from app.services.retrieval import RetrievedChunk, is_retrieval_strong
from app.services.vector_store import add_chunks


def test_retrieved_chunk_structure():
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_retrieval_service"
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
    )

    assert chunk.text
    assert chunk.document == "leave_policy.md"
    assert chunk.section == "Casual Leave"


def test_strong_retrieval():
    chunk = RetrievedChunk(
        text="Employees can carry forward up to 12 casual leave days.",
        document="leave_policy.md",
        section="Casual Leave",
        page="",
        distance=0.295,
    )

    assert is_retrieval_strong([chunk])


def test_weak_retrieval():
    chunk = RetrievedChunk(
        text="Employees receive 10 sick leave days per year.",
        document="leave_policy.md",
        section="Sick Leave",
        page="",
        distance=0.775,
    )

    assert not is_retrieval_strong([chunk])


def test_empty_retrieval_is_weak():
    assert not is_retrieval_strong([])