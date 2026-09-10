from pathlib import Path

import chromadb
import pytest

from app.services.ingestion import IngestionError, ingest_document


def test_ingest_document(tmp_path):
    file_path = tmp_path / "leave_policy.md"

    file_path.write_text(
        """# Casual Leave

Employees can carry forward up to 12 casual leave days.

# Sick Leave

Employees can carry forward up to 5 sick leave days.
""",
        encoding="utf-8",
    )

    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_ingestion",
    )

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

def test_ingestion_rebuilds_keyword_index(tmp_path):
    file_path = tmp_path / "leave_policy.md"

    file_path.write_text(
        """# Casual Leave

Employees receive 12 casual leave days.
""",
        encoding="utf-8",
    )

    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_keyword_sync",
    )

    ingest_document(
        file_path,
        target_collection=test_collection,
    )

    from app.services.keyword_search import keyword_index

    results = keyword_index.search(
        query="12 casual leave days",
        top_k=1,
    )

    assert results
    assert results[0][0] == "leave_policy.md-chunk-0"


def test_ingestion_indexes_document_and_section_context(tmp_path):
    file_path = tmp_path / "health_policy.md"

    file_path.write_text(
        """# Health Insurance

## Dental Implant Coverage

Covered up to 50,000 under Premium.
""",
        encoding="utf-8",
    )

    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_indexed_context",
    )

    ingest_document(
        file_path,
        target_collection=test_collection,
    )

    results = test_collection.get(
        include=["documents", "metadatas"],
    )

    assert results["documents"]

    indexed_document = results["documents"][0]
    metadata = results["metadatas"][0]

    assert indexed_document == (
        "Covered up to 50,000 under Premium."
    )

    assert metadata["search_text"] == (
        "Document: health_policy.md\n"
        "Section: Health Insurance > Dental Implant Coverage\n"
        "Content: Covered up to 50,000 under Premium."
    )

def test_section_context_is_available_to_keyword_index(tmp_path):
    file_path = tmp_path / "health_policy.md"

    file_path.write_text(
        """# Health Insurance

## Dental Implant Coverage

Covered up to 50,000 under Premium.
""",
        encoding="utf-8",
    )

    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="test_keyword_section_context",
    )

    ingest_document(
        file_path,
        target_collection=test_collection,
    )

    from app.services.keyword_search import keyword_index

    results = keyword_index.search(
        query="health insurance",
        top_k=1,
    )

    assert results
    assert results[0][0] == "health_policy.md-chunk-0"
    
