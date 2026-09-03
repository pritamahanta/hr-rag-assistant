from dataclasses import dataclass


@dataclass
class DocumentChunk:
    text: str
    document: str
    section: str | None
    page: int | str
    chunk_id: str


MAX_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def split_text(text: str) -> list[str]:
    text = text.strip()

    if len(text) <= MAX_CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + MAX_CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        next_start = end - CHUNK_OVERLAP

        if next_start <= start:
            break

        start = next_start

    return chunks


def create_chunks(sections: list[dict]) -> list[DocumentChunk]:
    chunks = []

    for section in sections:
        text_chunks = split_text(section["text"])

        for index, text in enumerate(text_chunks):
            chunk_id = (
                f"{section['document']}-"
                f"{section['section'] or 'unknown'}-"
                f"{index}"
            )

            chunks.append(
                DocumentChunk(
                    text = text,
                    document=section["document"],
                    section=section["section"],
                    page=section["page"],
                    chunk_id=chunk_id,
                )
            )

    return chunks