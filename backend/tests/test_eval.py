from unittest.mock import patch

from app.models.schemas import LLMResponse, QueryResolution
from app.services.query import answer_query
from app.services.retrieval import RetrievedChunk


def _chunk():
    return RetrievedChunk(
        text="Employees can carry forward up to 12 casual leave days.",
        document="leave_policy.md",
        section="Casual Leave",
        page="",
        distance=0.2,
        chunk_id="leave-policy-chunk-0",
    )


EVAL_CASES = [
    {
        "question": "How many casual leave days can employees carry forward?",
        "resolution": "answer",
        "answer": "Employees can carry forward up to 12 casual leave days.",
        "source_ids": ["leave-policy-chunk-0"],
    },
    {
        "question": "how many casual leaves we have",
        "resolution": "answer",
        "answer": "Employees can carry forward up to 12 casual leave days.",
        "source_ids": ["leave-policy-chunk-0"],
    },
    {
        "question": "How many leave days do I get?",
        "resolution": "clarify",
        "answer": None,
        "source_ids": [],
    },
    {
        "question": "Does the company provide dental insurance?",
        "resolution": "refuse",
        "answer": None,
        "source_ids": [],
    },
]


def test_eval_cases():
    for case in EVAL_CASES:
        with patch(
            "app.services.query.retrieve_chunks",
            return_value=[_chunk()],
        ), patch(
            "app.services.query.resolve_query",
            return_value=QueryResolution(decision=case["resolution"]),
        ), patch(
            "app.services.query.generate_answer",
            return_value=LLMResponse(
                answer=case["answer"] or "",
                source_ids=case["source_ids"],
            ),
        ):
            response = answer_query(case["question"])

        if case["resolution"] == "answer":
            assert response.answer == case["answer"]
            assert len(response.citations) == 1

        elif case["resolution"] == "clarify":
            assert response.answer != case["answer"]
            assert response.citations == []

        else:
            assert response.citations == []