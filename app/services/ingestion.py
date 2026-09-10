from pathlib import Path

from app.services.chunking import create_chunks
from app.services.document_parser import parse_document
from app.services.embedding import generate_embeddings
from app.services.keyword_search import rebuild_keyword_index
from app.services.vector_store import get_all_chunks, replace_document


class IngestionError(Exception):
    """Raised when a document cannot be indexed."""


def build_index_text(
    document: str,
    section: str | None,
    text: str,
) -> str:
    return (
        f"Document: {document}\n"
        f"Section: {section or 'N/A'}\n"
        f"Content: {text}"
    )


def ingest_document(
    file_path: Path,
    target_collection=None,
) -> int:
    sections = parse_document(file_path)
    chunks = create_chunks(sections)

    if not chunks:
        raise IngestionError(
            f"No extractable text found in document: {file_path.name}"
        )

    texts = [chunk.text for chunk in chunks]

    indexed_texts = [
        build_index_text(
            document=chunk.document,
            section=chunk.section,
            text=chunk.text,
        )
        for chunk in chunks
    ]

    embeddings = generate_embeddings(indexed_texts)

    metadatas = [
        {
            "document": chunk.document,
            "section": chunk.section or "",
            "page": chunk.page,
            "search_text": indexed_text,
        }
        for chunk, indexed_text in zip(chunks, indexed_texts)
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
        texts=[
            metadata.get("search_text", document)
            for metadata, document in zip(
                results.get("metadatas", []),
                results.get("documents", []),
            )
        ],
        ids=results.get("ids", []),
    )

    return len(chunks)