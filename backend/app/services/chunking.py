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


def _is_table_line(line: str) -> bool:
    return line.startswith("|") and "|" in line[1:]


def _is_table_separator(line: str) -> bool:
    stripped = line.replace("|", "").replace("-", "").replace(":", "").strip()
    return not stripped


def _split_oversized_line(line: str) -> list[str]:
    chunks = []

    start = 0

    while start < len(line):
        end = start + MAX_CHUNK_SIZE
        chunks.append(line[start:end])
        start = end

    return chunks


def _split_table(lines: list[str]) -> list[str]:
    if not lines:
        return []

    header_lines = [lines[0]]

    if len(lines) > 1 and _is_table_separator(lines[1]):
        header_lines.append(lines[1])

    header = "\n".join(header_lines)
    header_size = len(header) + len(header_lines) - 1

    if header_size >= MAX_CHUNK_SIZE:
        return _split_oversized_line(header)

    chunks = []
    current_rows = []
    current_size = header_size

    for row in lines[len(header_lines):]:
        row_size = len(row) + 1

        if current_rows and current_size + row_size > MAX_CHUNK_SIZE:
            chunks.append(
                header
                + "\n"
                + "\n".join(current_rows)
            )

            overlap_rows = []
            overlap_size = 0

            for previous_row in reversed(current_rows):
                previous_size = len(previous_row) + 1

                if overlap_size + previous_size > CHUNK_OVERLAP:
                    break

                overlap_rows.insert(0, previous_row)
                overlap_size += previous_size

            current_rows = overlap_rows
            current_size = header_size + overlap_size

        current_rows.append(row)
        current_size += row_size

    if current_rows:
        chunks.append(
            header
            + "\n"
            + "\n".join(current_rows)
        )

    return chunks


def split_text(text: str) -> list[str]:
    text = text.strip()

    if len(text) <= MAX_CHUNK_SIZE:
        return [text]

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    chunks = []
    current_lines = []
    current_size = 0
    index = 0

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

    while index < len(lines):
        line = lines[index]

        if (
            _is_table_line(line)
            and index + 1 < len(lines)
            and _is_table_separator(lines[index + 1])
        ):
            table_lines = []

            while index < len(lines) and _is_table_line(lines[index]):
                table_lines.append(lines[index])
                index += 1

            add_chunk()
            chunks.extend(_split_table(table_lines))
            continue

        if len(line) > MAX_CHUNK_SIZE:
            if current_lines:
                add_chunk()

            chunks.extend(_split_oversized_line(line))

            current_lines = []
            current_size = 0
            index += 1
            continue

        line_size = len(line) + 1

        if current_lines and current_size + line_size > MAX_CHUNK_SIZE:
            add_chunk()

        current_lines.append(line)
        current_size += line_size
        index += 1

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