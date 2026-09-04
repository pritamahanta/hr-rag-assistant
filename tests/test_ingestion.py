import chromadb
from pathlib import Path
from app.services.ingestion import ingest_document


def test_ingest_document():
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_ingestion"
    )

    file_path = Path("test_documents/leave_policy.md")

    chunks_indexed = ingest_document(
        file_path,
        target_collection=test_collection,
    )

    assert chunks_indexed == 2

    results = test_collection.get()

    assert len(results["ids"]) == 2