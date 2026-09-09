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

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    chunks = []
    current_lines = []
    current_size = 0

    def add_chunk():
        nonlocal current_lines, current_size

        if not current_lines:
            return

        chunks.append("\n".join(current_lines))

        overlap_lines = []
        overlap_size = 0

        for previous_line in reversed(current_lines):
            previous_size = len(previous_line) + 1

            if overlap_size + previous_size > CHUNK_OVERLAP:
                break

            overlap_lines.insert(0, previous_line)
            overlap_size += previous_size

        current_lines = overlap_lines
        current_size = overlap_size

    for line in lines:
        if len(line) > MAX_CHUNK_SIZE:
            if current_lines:
                add_chunk()

            start = 0

            while start < len(line):
                end = start + MAX_CHUNK_SIZE
                chunks.append(line[start:end])
                start = end

            current_lines = []
            current_size = 0
            continue

        line_size = len(line) + 1

        if current_lines and current_size + line_size > MAX_CHUNK_SIZE:
            add_chunk()

        current_lines.append(line)
        current_size += line_size

    if current_lines:
        add_chunk()

    return chunks


def create_chunks(sections: list[dict]) -> list[DocumentChunk]:
    chunks = []

    for section in sections:
        text_chunks = split_text(section["text"])

        for text in text_chunks:
            chunk_id = (
                f"{section['document']}-"
                f"chunk-{len(chunks)}"
            )

            chunks.append(
                DocumentChunk(
                    text=text,
                    document=section["document"],
                    section=section["section"],
                    page=section["page"],
                    chunk_id=chunk_id,
                )
            )

    return chunks