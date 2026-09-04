from app.models.schemas import Citation
from app.services.retrieval import RetrievedChunk


def build_citations(
    chunks: list[RetrievedChunk],
    source_ids: list[str],
) -> list[Citation]:
    chunks_by_id = {
        chunk.chunk_id: chunk
        for chunk in chunks
    }

    citations = []
    seen = set()

    for source_id in source_ids:
        chunk = chunks_by_id.get(source_id)

        if chunk is None:
            continue

        citation_key = (
            chunk.document,
            chunk.section,
            chunk.page,
        )

        if citation_key in seen:
            continue

        seen.add(citation_key)

        citations.append(
            Citation(
                document=chunk.document,
                section=chunk.section,
                page=chunk.page,
            )
        )

    return citations