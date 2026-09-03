from pathlib import Path

from app.services.chunking import create_chunks
from app.services.document_parser import parse_document
from app.services.embedding import generate_embeddings
from app.services.vector_store import add_chunks


def ingest_document(file_path: Path) -> int:
    sections = parse_document(file_path)

    chunks = create_chunks(sections)

    if not chunks:
        return 0

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

    add_chunks(
        texts=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    return len(chunks)