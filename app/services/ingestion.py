from pathlib import Path

from app.services.chunking import create_chunks
from app.services.document_parser import parse_document
from app.services.embedding import generate_embeddings
from app.services.vector_store import get_all_chunks, replace_document
from app.services.keyword_search import rebuild_keyword_index


class IngestionError(Exception):
    """Raised when a document cannot be indexed."""


def ingest_document(file_path: Path, target_collection=None) -> int:
    sections = parse_document(file_path)
    chunks = create_chunks(sections)

    if not chunks:
        raise IngestionError(
            f"No extractable text found in document: {file_path.name}"
        )

    texts = [chunk.text for chunk in chunks]

    embeddings = generate_embeddings(texts)

    metadatas = [
        {
            "document": chunk.document,
            "section": chunk.section or "",
            "page": chunk.page,
        }
        for chunk in chunks
    ]

    ids = [chunk.chunk_id for chunk in chunks]

    replace_document(
        document=file_path.name,
        texts=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
        target_collection=target_collection,
    )

    results = get_all_chunks(
        target_collection=target_collection,
    )

    rebuild_keyword_index(
        texts=results.get("documents", []),
        ids=results.get("ids", []),
    )

    return len(chunks)