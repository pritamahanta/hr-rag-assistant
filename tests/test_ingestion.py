from pathlib import Path

from app.services.ingestion import ingest_document


def test_ingest_document():
    file_path = Path("test_documents/leave_policy.md")

    chunks_indexed = ingest_document(file_path)

    assert chunks_indexed == 2