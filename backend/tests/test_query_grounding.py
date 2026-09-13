from unittest.mock import patch

import pytest

from app.models.schemas import LLMResponse, QueryResolution
from app.services.query import (
    CLARIFICATION_MESSAGE,
    QueryServiceError,
    REFUSAL_MESSAGE,
    answer_query,
)
from app.services.retrieval import RetrievedChunk


def _strong_chunk():
    return RetrievedChunk(
        text="Employees can carry forward up to 12 casual leave days.",
        document="leave_policy.md",
        section="Casual Leave",
        page="",
        distance=0.2,
        chunk_id="leave-policy-chunk-0",
    )


def _run_with_mocked_llm(
    resolution="answer",
    answer="Employees can carry forward up to 12 casual leave days.",
    source_ids=None,
):
    if source_ids is None:
        source_ids = ["leave-policy-chunk-0"]

    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        return_value=QueryResolution(decision=resolution),
    ), patch(
        "app.services.query.generate_answer",
        return_value=LLMResponse(
            answer=answer,
            source_ids=source_ids,
        ),
    ):
        return answer_query("How many casual leave days?")


def test_refuse_decision_returns_canonical_message():
    response = _run_with_mocked_llm(
        resolution="refuse",
        answer="",
        source_ids=[],
    )

    assert response.answer == REFUSAL_MESSAGE
    assert response.citations == []


def test_clarify_decision_returns_generic_clarification():
    response = _run_with_mocked_llm(
        resolution="clarify",
        answer="",
        source_ids=[],
    )

    assert response.answer == CLARIFICATION_MESSAGE
    assert response.citations == []


def test_ambiguous_leave_question_returns_generated_clarification():
    chunks = [
        _strong_chunk(),
        RetrievedChunk(
            text="Privilege leave: up to 15 days can be carried forward.",
            document="leave_policy.md",
            section="Privilege Leave",
            page="",
            distance=0.2,
            chunk_id="privilege-leave-1",
        ),
        RetrievedChunk(
            text="Sick leave does not carry forward.",
            document="leave_policy.md",
            section="Sick Leave",
            page="",
            distance=0.2,
            chunk_id="sick-leave-1",
        ),
    ]
    clarification = (
        "Which type of leave are you asking about: casual, sick, or privilege leave?"
    )
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=chunks,
    ), patch(
        "app.services.query.resolve_query",
        return_value=QueryResolution(
            decision="clarify",
            clarification=clarification,
        ),
    ):
        response = answer_query("How many leave days can I carry forward?")

    assert response.answer == clarification
    assert response.citations == []


def test_answer_decision_with_empty_source_ids_is_untrustworthy():
    response = _run_with_mocked_llm(
        resolution="answer",
        source_ids=[],
    )

    assert response.answer == REFUSAL_MESSAGE
    assert response.citations == []


def test_answer_decision_with_valid_source_ids_passes_through_normally():
    response = _run_with_mocked_llm()

    assert response.answer == (
        "Employees can carry forward up to 12 casual leave days."
    )
    assert len(response.citations) == 1
    assert response.citations[0].document == "leave_policy.md"
    assert response.citations[0].section == "Casual Leave"


def test_llm_exception_raises_query_service_error():
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        return_value=QueryResolution(decision="answer"),
    ), patch(
        "app.services.query.generate_answer",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        with pytest.raises(
            QueryServiceError,
            match="Answer generation failed.",
        ):
            answer_query("How many casual leave days?")


def test_resolver_exception_raises_query_service_error():
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        side_effect=RuntimeError("Resolver unavailable"),
    ):
        with pytest.raises(
            QueryServiceError,
            match="Query resolution failed.",
        ):
            answer_query("How many casual leave days?")


def test_retrieval_exception_raises_query_service_error():
    with patch(
        "app.services.query.retrieve_chunks",
        side_effect=RuntimeError("Vector store unavailable"),
    ):
        with pytest.raises(
            QueryServiceError,
            match="Retrieval failed.",
        ):
            answer_query("How many casual leave days?")


def test_clarify_does_not_call_answer_generation():
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        return_value=QueryResolution(decision="clarify"),
    ), patch(
        "app.services.query.generate_answer",
    ) as mock_generate:

        response = answer_query("How many leave days do I get?")

    assert response.answer == CLARIFICATION_MESSAGE
    assert response.citations == []
    mock_generate.assert_not_called()


def test_empty_retrieval_returns_policy_refusal():
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[],
    ):
        response = answer_query("Does the company provide dental insurance?")

    assert response.answer == REFUSAL_MESSAGE
    assert response.citations == []


def test_unsupported_permission_returns_refusal_without_llm_calls():
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch("app.services.query.resolve_query") as mock_resolve, patch(
        "app.services.query.generate_answer"
    ) as mock_generate:
        response = answer_query("Can I take leave for a vacation abroad?")

    assert response.answer == REFUSAL_MESSAGE
    assert response.citations == []
    mock_resolve.assert_not_called()
    mock_generate.assert_not_called()


def test_explicit_permission_proceeds_to_llm():
    chunk = RetrievedChunk(
        text="Casual leave and privilege leave may be combined in a single request.",
        document="leave-policy.md",
        section="Combining leave types",
        page="",
        distance=0.2,
        chunk_id="combining-leave-types",
    )
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[chunk],
    ), patch(
        "app.services.query.resolve_query",
        return_value=QueryResolution(decision="answer"),
    ) as mock_resolve, patch(
        "app.services.query.generate_answer",
        return_value=LLMResponse(
            answer="They may be combined in a single request.",
            source_ids=["combining-leave-types"],
        ),
    ) as mock_generate:
        response = answer_query("Can I combine casual and privilege leave?")

    assert response.answer == "They may be combined in a single request."
    assert response.citations
    mock_resolve.assert_called_once()
    mock_generate.assert_called_once()


def test_ordinary_factual_question_is_unaffected():
    response = _run_with_mocked_llm()

    assert response.answer == (
        "Employees can carry forward up to 12 casual leave days."
    )


def test_combination_question_with_non_permission_wording_is_unaffected():
    with patch(
        "app.services.query.retrieve_chunks",
        return_value=[_strong_chunk()],
    ), patch(
        "app.services.query.resolve_query",
        return_value=QueryResolution(decision="answer"),
    ), patch(
        "app.services.query.generate_answer",
        return_value=LLMResponse(
            answer="Casual leave can be carried forward.",
            source_ids=["leave-policy-chunk-0"],
        ),
    ):
        response = answer_query("What happens when casual leave days are combined?")

    assert response.answer == "Casual leave can be carried forward."
    assert response.citations