from app.models.schemas import Citation
from app.services.retrieval import RetrievedChunk


def build_citations(
    chunks: list[RetrievedChunk],
) -> list[Citation]:
    citations = []

    seen = set()

    for chunk in chunks:
        key = (
            chunk.document,
            chunk.section,
            chunk.page,
        )

        if key in seen:
            continue

        seen.add(key)

        citations.append(
            Citation(
                document=chunk.document,
                section=chunk.section,
                page=chunk.page,
            )
        )

    return citations