from unittest.mock import patch

from app.models.schemas import LLMResponse, QueryResolution

from app.services.query import REFUSAL_MESSAGE, answer_query

from app.services.retrieval import RetrievedChunk


def _strong_chunk():
    return RetrievedChunk(
        text="Employees can carry forward up to 12 casual leave days.",
        document="leave_policy.md",
        section="Casual Leave",
        page="",
        distance=0.1,
        chunk_id="casual-leave-1",
    )


def _run_with_mocked_llm(
    resolution,
    llm_response=None,
    question="Any question",
):
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        return_value=resolution,
    ), patch(
        "app.services.query.generate_answer",
        return_value=llm_response,
    ):
        return answer_query(question)


def test_refuse_decision_returns_canonical_message():
    resolution = QueryResolution(
        decision="refuse",
        clarification="",
    )

    result = _run_with_mocked_llm(resolution)

    assert result.answer == REFUSAL_MESSAGE
    assert result.citations == []


def test_clarify_decision_passes_through_clarification():
    resolution = QueryResolution(
        decision="clarify",
        clarification="Which type of leave are you asking about?",
    )

    result = _run_with_mocked_llm(resolution)

    assert result.answer == "Could you please provide a little more detail about what you're asking about?"
    assert result.citations == []


def test_answer_decision_with_empty_source_ids_is_untrustworthy():
    resolution = QueryResolution(
        decision="answer",
        clarification="",
    )

    llm_response = LLMResponse(
        answer="Yes, this is definitely covered under company policy.",
        source_ids=[],
    )

    result = _run_with_mocked_llm(
        resolution,
        llm_response,
    )

    assert result.answer == REFUSAL_MESSAGE
    assert result.citations == []


def test_answer_decision_with_valid_source_ids_passes_through_normally():
    resolution = QueryResolution(
        decision="answer",
        clarification="",
    )

    llm_response = LLMResponse(
        answer="You can carry forward up to 12 casual leave days.",
        source_ids=["casual-leave-1"],
    )

    result = _run_with_mocked_llm(
        resolution,
        llm_response,
    )

    assert result.answer == llm_response.answer
    assert len(result.citations) == 1
    assert result.citations[0].document == "leave_policy.md"


def test_llm_exception_returns_refusal_and_does_not_crash():
    resolution = QueryResolution(
        decision="answer",
        clarification="",
    )

    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        return_value=resolution,
    ), patch(
        "app.services.query.generate_answer",
        side_effect=RuntimeError("boom"),
    ):
        result = answer_query("Anything?")

    assert result.answer == REFUSAL_MESSAGE
    assert result.citations == []


def test_clarify_does_not_call_answer_generation():
    resolution = QueryResolution(
        decision="clarify",
    )

    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        return_value=resolution,
    ), patch(
        "app.services.query.generate_answer",
    ) as mock_generate:

        result = answer_query("How many leave days do I get?")

    mock_generate.assert_not_called()

    assert result.answer == "Could you please provide a little more detail about what you're asking about?"
    assert result.citations == []