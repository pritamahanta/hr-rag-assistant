import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.llm import QUERY_RESOLUTION_SCHEMA, resolve_query


@pytest.mark.parametrize(
    ("decision", "clarification"),
    [
        ("answer", ""),
        ("refuse", ""),
        (
            "clarify",
            "Which type of leave are you asking about: casual, sick, or privilege?",
        ),
    ],
)
def test_resolver_returns_all_structured_decision_cases(
    decision,
    clarification,
):
    payload = {
        "decision": decision,
        "clarification": clarification,
    }
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(payload)),
            )
        ]
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_: response),
        )
    )

    with patch("app.services.llm._get_client", return_value=client):
        result = resolve_query(
            question="How many leave days can I carry forward?",
            context=(
                "Casual leave: up to 8 days can be carried forward.\n"
                "Privilege leave: up to 15 days can be carried forward.\n"
                "Sick leave: does not carry forward."
            ),
        )

    assert result.decision == decision
    assert result.clarification == clarification


def test_resolver_schema_requires_clarification():
    assert QUERY_RESOLUTION_SCHEMA["required"] == [
        "decision",
        "clarification",
    ]
    assert QUERY_RESOLUTION_SCHEMA["properties"]["clarification"] == {
        "type": "string",
    }
