from groq import Groq

from app.core.config import GROQ_API_KEY
from app.models.schemas import LLMResponse


MODEL_NAME = "openai/gpt-oss-20b"

_client = None


def _get_client() -> Groq:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to .env before asking questions."
        )
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


LLM_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": [
                "answer",
                "clarify",
                "refuse",
            ],
        },
        "answer": {
            "type": "string",
        },
        "source_ids": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "decision",
        "answer",
        "source_ids",
    ],
    "additionalProperties": False,
}


def generate_answer(
    question: str,
    context: str,
) -> LLMResponse:
    client = _get_client()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                        "You are an internal HR policy assistant. "
                        "Answer the user's question using only the provided policy context. "
                        "Do not use outside knowledge. "

                        "Choose exactly one decision: "
                        "'answer', 'clarify', or 'refuse'. "

                        "Use 'answer' when the policy context contains enough information "
                        "to answer the user's question specifically and accurately. "

                        "Use 'clarify' when the policy context is relevant to the user's "
                        "question, but the user's question is ambiguous or missing information "
                        "needed to determine exactly what they are asking. "
                        "For example, if the user asks 'How many leave days do I have?' "
                        "and the context contains multiple types of leave, ask which type "
                        "of leave they mean. "
                        "The clarification must be based only on concepts present in the "
                        "provided policy context. "

                        "Use 'refuse' when the provided policy context does not contain "
                        "enough relevant information to answer the question. "
                        "Do not guess. "

                        "For 'answer', return the source_ids of the provided context entries "
                        "that directly support the answer. "

                        "For 'clarify' and 'refuse', return an empty source_ids array. "

                        "Never invent or modify a source_id."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Policy context:\n\n{context}\n\n"
                    f"Question:\n{question}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "llm_response",
                "strict": True,
                "schema": LLM_RESPONSE_SCHEMA,
            },
        },
    )

    return LLMResponse.model_validate_json(
        response.choices[0].message.content
    )