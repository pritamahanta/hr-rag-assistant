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
    current_section = None
    current_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("#"):
            if current_lines:
                sections.append(
                    {
                        "text": "\n".join(current_lines).strip(),
                        "document": file_path.name,
                        "section": current_section,
                        "page": "",
                    }
                )

            current_section = stripped.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(
            {
                "text": "\n".join(current_lines).strip(),
                "document": file_path.name,
                "section": current_section,
                "page": None,
            }
        )

    return [section for section in sections if section["text"]]


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