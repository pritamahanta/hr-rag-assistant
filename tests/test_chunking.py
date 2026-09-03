from app.services.chunking import create_chunks


def test_create_chunks():
    sections = [
        {
            "text": "Employees can carry forward up to 12 casual leave days.",
            "document": "leave_policy.md",
            "section": "Casual Leave",
            "page": None,
        }
    ]

    chunks = create_chunks(sections)

    assert len(chunks) == 1
    assert chunks[0].text == (
        "Employees can carry forward up to 12 casual leave days."
    )
    assert chunks[0].document == "leave_policy.md"
    assert chunks[0].section == "Casual Leave"


def test_large_text_is_split():
    sections = [
        {
            "text": "A" * 2500,
            "document": "large_policy.md",
            "section": "Example",
            "page": None,
        }
    ]

    chunks = create_chunks(sections)

    assert len(chunks) > 1
    assert all(chunk.document == "large_policy.md" for chunk in chunks)
    assert all(chunk.section == "Example" for chunk in chunks)