from pathlib import Path

from pypdf import PdfWriter

from app.services.document_parser import (
    parse_document,
    parse_markdown_file,
    parse_pdf_file,
    parse_text_file,
)


def test_parse_text_file(tmp_path):
    file_path = tmp_path / "leave_policy.txt"
    file_path.write_text(
        "Employees can carry forward up to 12 casual leave days.",
        encoding="utf-8",
    )

    sections = parse_text_file(file_path)

    assert sections == [
        {
            "text": "Employees can carry forward up to 12 casual leave days.",
            "document": "leave_policy.txt",
            "section": None,
            "page": "",
        }
    ]


def test_parse_markdown_file_extracts_sections(tmp_path):
    file_path = tmp_path / "leave_policy.md"
    file_path.write_text(
        """# Casual Leave

Employees receive 12 casual leave days.

# Sick Leave

Employees receive 10 sick leave days.
""",
        encoding="utf-8",
    )

    sections = parse_markdown_file(file_path)

    assert len(sections) == 2

    assert sections[0]["section"] == "Casual Leave"
    assert sections[0]["text"] == "Employees receive 12 casual leave days."
    assert sections[0]["document"] == "leave_policy.md"

    assert sections[1]["section"] == "Sick Leave"
    assert sections[1]["text"] == "Employees receive 10 sick leave days."


def test_parse_pdf_file_extracts_page_text(tmp_path, monkeypatch):
    file_path = tmp_path / "policy.pdf"
    file_path.write_bytes(b"fake pdf")

    class FakePage:
        def extract_text(self):
            return "Employees receive 12 casual leave days."

    class FakeReader:
        def __init__(self, path):
            self.pages = [FakePage()]

    monkeypatch.setattr(
        "app.services.document_parser.PdfReader",
        FakeReader,
    )

    sections = parse_pdf_file(file_path)

    assert sections == [
        {
            "text": "Employees receive 12 casual leave days.",
            "document": "policy.pdf",
            "section": None,
            "page": 1,
        }
    ]


def test_parse_document_dispatches_by_extension(tmp_path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text(
        "Policy content.",
        encoding="utf-8",
    )

    sections = parse_document(file_path)

    assert len(sections) == 1
    assert sections[0]["text"] == "Policy content."


def test_parse_document_rejects_unsupported_extension(tmp_path):
    file_path = tmp_path / "policy.docx"
    file_path.write_text(
        "Unsupported document.",
        encoding="utf-8",
    )

    try:
        parse_document(file_path)
    except ValueError as exc:
        assert str(exc) == "Unsupported file type: .docx"
    else:
        assert False, "Expected ValueError"


def test_parse_markdown_file_preserves_heading_hierarchy(tmp_path):
    file_path = tmp_path / "benefits.md"

    file_path.write_text(
        """# Health Insurance

General health insurance information.

## Dental Implant Coverage

Premium covers dental implants.

### Premium Plus

Premium Plus has a higher annual limit.

## Claims

Claims are submitted through HR.

# Leave Policy

Leave information.
""",
        encoding="utf-8",
    )

    sections = parse_markdown_file(file_path)

    section_names = [
        section["section"]
        for section in sections
    ]

    assert section_names == [
        "Health Insurance",
        "Health Insurance > Dental Implant Coverage",
        "Health Insurance > Dental Implant Coverage > Premium Plus",
        "Health Insurance > Claims",
        "Leave Policy",
    ]


def test_parse_markdown_file_keeps_sibling_sections_separate(tmp_path):
    file_path = tmp_path / "policy.md"

    file_path.write_text(
        """# Health Insurance

## Overview

Health overview.

# Leave Policy

## Overview

Leave overview.
""",
        encoding="utf-8",
    )

    sections = parse_markdown_file(file_path)

    assert sections[0]["section"] == "Health Insurance > Overview"
    assert sections[1]["section"] == "Leave Policy > Overview"