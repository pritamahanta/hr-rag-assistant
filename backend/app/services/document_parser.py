from pathlib import Path
from pypdf import PdfReader


def parse_text_file(file_path: Path) -> list[dict]:
    text = file_path.read_text(encoding="utf-8")

    return [
        {
            "text": text,
            "document": file_path.name,
            "section": None,
            "page": "",
        }
    ]


def parse_markdown_file(file_path: Path) -> list[dict]:
    text = file_path.read_text(encoding="utf-8")

    sections = []
    heading_stack: list[tuple[int, str]] = []
    current_lines = []

    def current_section_path() -> str | None:
        if not heading_stack:
            return None

        return " > ".join(
            heading
            for _, heading in heading_stack
        )

    def add_section():
        if not current_lines:
            return

        sections.append(
            {
                "text": "\n".join(current_lines).strip(),
                "document": file_path.name,
                "section": current_section_path(),
                "page": "",
            }
        )

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("#"):
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            heading_text = stripped.lstrip("#").strip()

            add_section()

            while (
                heading_stack
                and heading_stack[-1][0] >= heading_level
            ):
                heading_stack.pop()

            heading_stack.append(
                (heading_level, heading_text)
            )

            current_lines = []
        else:
            current_lines.append(line)

    add_section()

    return [
        section
        for section in sections
        if section["text"]
    ]

def parse_pdf_file(file_path: Path) -> list[dict]:
    reader = PdfReader(file_path)

    sections = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if not text:
            continue

        sections.append(
            {
                "text": text.strip(),
                "document": file_path.name,
                "section": None,
                "page": page_number,
            }
        )

    return sections


def parse_document(file_path: Path) -> list[dict]:
    extension = file_path.suffix.lower()

    if extension == ".md":
        return parse_markdown_file(file_path)

    if extension == ".txt":
        return parse_text_file(file_path)

    if extension == ".pdf":
        return parse_pdf_file(file_path)

    raise ValueError(f"Unsupported file type: {extension}")