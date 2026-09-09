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