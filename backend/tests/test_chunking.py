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


def test_long_table_rows_are_not_split():
    header = "| Plan | Benefit | Limit |\n"
    rows = [
        f"| Plan {i} | Benefit description for plan {i} | Limit {i} |\n"
        for i in range(100)
    ]

    table = header + "".join(rows)

    assert len(table) > 1000

    chunks = create_chunks(
        [
            {
                "text": table,
                "document": "benefits.md",
                "section": "Benefits",
                "page": None,
            }
        ]
    )

    assert len(chunks) > 1

    original_rows = {
        row.strip()
        for row in table.splitlines()
        if row.strip()
    }

    for chunk in chunks:
        for line in chunk.text.splitlines():
            if line.strip().startswith("|"):
                assert line.strip() in original_rows


def test_long_table_header_is_preserved_in_each_chunk():
    header = "| Plan | Benefit | Limit |"
    separator = "|------|---------|-------|"

    rows = [
        f"| Plan {i} | Benefit description for plan {i} | Limit {i} |"
        for i in range(100)
    ]

    table = "\n".join([header, separator, *rows])

    assert len(table) > 1000

    chunks = create_chunks(
        [
            {
                "text": table,
                "document": "benefits.md",
                "section": "Benefits",
                "page": None,
            }
        ]
    )

    assert len(chunks) > 1

    for chunk in chunks:
        assert header in chunk.text
        assert separator in chunk.text