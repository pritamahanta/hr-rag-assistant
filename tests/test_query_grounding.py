from unittest.mock import patch

from app.models.schemas import LLMResponse
from app.services.query import REFUSAL_MESSAGE, answer_query
from app.services.retrieval import RetrievedChunk


def _strong_chunk():
    return RetrievedChunk(
        text="Employees can carry forward up to 12 casual leave days.",
        document="leave_policy.md",
        section="Casual Leave",
        page="",
        distance=0.1,  # well under threshold -> retrieval gate passes
        chunk_id="casual-leave-1",
    )


def _run_with_mocked_llm(fake_llm_response, question="Any question"):
    with patch(
        "app.services.query.retrieve_chunks", return_value=[_strong_chunk()]
    ), patch(
        "app.services.query.generate_answer", return_value=fake_llm_response
    ):
        return answer_query(question)


def test_refuse_decision_returns_canonical_message():
    fake = LLMResponse(decision="refuse", answer="No idea.", source_ids=[])
    result = _run_with_mocked_llm(fake)
    assert result.answer == REFUSAL_MESSAGE
    assert result.citations == []


def test_clarify_decision_passes_through_the_question_with_no_citations():
    """
    This is the case the naive 'empty source_ids => refuse' gate breaks:
    a legitimate clarifying question also has empty source_ids, and must
    NOT be swallowed into the generic refusal message.
    """
    fake = LLMResponse(
        decision="clarify",
        answer="Do you mean casual leave or sick leave?",
        source_ids=[],
    )
    result = _run_with_mocked_llm(fake)
    assert result.answer == "Do you mean casual leave or sick leave?"
    assert result.citations == []


def test_answer_decision_with_empty_source_ids_is_treated_as_untrustworthy():
    """
    decision='answer' but no source_ids is a contradiction -- the model
    claims a grounded answer but cited nothing. Don't trust the free text.
    """
    fake = LLMResponse(
        decision="answer",
        answer="Yes, this is definitely covered under company policy.",
        source_ids=[],
    )
    result = _run_with_mocked_llm(fake)
    assert result.answer == REFUSAL_MESSAGE
    assert result.citations == []


def test_answer_decision_with_valid_source_ids_passes_through_normally():
    fake = LLMResponse(
        decision="answer",
        answer="You can carry forward up to 12 casual leave days.",
        source_ids=["casual-leave-1"],
    )
    result = _run_with_mocked_llm(fake)
    assert result.answer == fake.answer
    assert len(result.citations) == 1
    assert result.citations[0].document == "leave_policy.md"


def test_llm_exception_returns_refusal_and_does_not_crash():
    with patch(
        "app.services.query.retrieve_chunks", return_value=[_strong_chunk()]
    ), patch(
        "app.services.query.generate_answer", side_effect=RuntimeError("boom")
    ):
        result = answer_query("Anything?")
    assert result.answer == REFUSAL_MESSAGE
    assert result.citations == []