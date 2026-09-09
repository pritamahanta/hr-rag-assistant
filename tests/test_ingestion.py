import chromadb
import pytest
from pathlib import Path
from app.services.ingestion import ingest_document, IngestionError


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

def test_ingestion_rejects_document_with_no_extractable_text(
    tmp_path,
    monkeypatch,
):
    file_path = tmp_path / "empty_policy.pdf"
    file_path.write_bytes(b"fake pdf")

    monkeypatch.setattr(
        "app.services.ingestion.parse_document",
        lambda _: [],
    )

    with pytest.raises(
        IngestionError,
        match="No extractable text found in document: empty_policy.pdf",
    ):
        ingest_document(file_path)