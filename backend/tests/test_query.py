from app.services.query import build_context
from app.services.retrieval import RetrievedChunk


def test_build_context():
    chunks = [
        RetrievedChunk(
            text="Employees can carry forward up to 12 casual leave days.",
            document="leave_policy.md",
            section="Casual Leave",
            page="",
            distance=0.295,
            chunk_id="casual-leave-1",
        )
    ]

    context = build_context(chunks)

    assert "[Source ID: casual-leave-1]" in context
    assert "Document: leave_policy.md" in context
    assert "Section: Casual Leave" in context
    assert "Employees can carry forward up to 12 casual leave days." in context