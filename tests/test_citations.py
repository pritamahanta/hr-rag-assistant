from app.models.schemas import Citation
from app.services.citations import build_citations
from app.services.retrieval import RetrievedChunk


def test_build_citations():
    chunks = [
        RetrievedChunk(
            text="Employees can carry forward up to 12 casual leave days.",
            document="leave_policy.md",
            section="Casual Leave",
            page="",
            distance=0.295,
        ),
        RetrievedChunk(
            text="Employees can carry forward up to 12 casual leave days.",
            document="leave_policy.md",
            section="Casual Leave",
            page="",
            distance=0.300,
        ),
    ]

    citations = build_citations(chunks)

    assert citations == [
        Citation(
            document="leave_policy.md",
            section="Casual Leave",
            page="",
        )
    ]


def test_build_citations_from_multiple_sections():
    chunks = [
        RetrievedChunk(
            text="Casual leave information.",
            document="leave_policy.md",
            section="Casual Leave",
            page="",
            distance=0.3,
        ),
        RetrievedChunk(
            text="Sick leave information.",
            document="leave_policy.md",
            section="Sick Leave",
            page="",
            distance=0.5,
        ),
    ]

    citations = build_citations(chunks)

    assert len(citations) == 2
    assert citations[0].section == "Casual Leave"
    assert citations[1].section == "Sick Leave"


def test_empty_chunks_produce_no_citations():
    assert build_citations([]) == []