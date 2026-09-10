from groq import Groq

from app.core.config import GROQ_API_KEY
from app.models.schemas import LLMResponse, QueryResolution


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
        "answer",
        "source_ids",
    ],
    "additionalProperties": False,
}


QUERY_RESOLUTION_SCHEMA = {
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
    },
    "required": [
        "decision",
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
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": (
                   "You are an internal HR policy assistant. "

                    "Answer the user's question using ONLY the provided policy context. "
            
                    "Do not use general knowledge, assumptions, or information "
                    "that is not supported by the provided policy context. "
            
                    "Only provide an answer when the policy context directly "
                    "supports the answer. Do not infer missing policy rules. "
            
                    "Return the source_ids of the provided context entries that "
                    "DIRECTLY support the factual claims in the answer. "
            
                    "A source is valid only if its content explicitly supports "
                    "the claim it is being cited for. Do not cite a source merely "
                    "because it is related to the topic. "
            
                    "For list, count, or enumeration questions, make sure every "
                    "listed item is directly supported by the cited source(s). "
                    "Include the relevant source for each distinct item when "
                    "multiple policy sections are required. "
            
                    "For example, if the answer lists casual leave, sick leave, "
                    "and privilege leave, the cited sources must contain the "
                    "policy sections defining those three leave types. A section "
                    "about combining leave types must NOT be cited merely because "
                    "it mentions leave types. "
            
                    "Only include source_ids that were actually used to support "
                    "the answer. Do not include extra, merely related sources. "
            
                    "Never invent, modify, or guess a source_id. "
            
                    "If the provided policy context does not support an answer, "
                    "return an empty answer and an empty source_ids array. "
            
                    "Return only the structured response defined by the schema. "
            
                    "Answer the user's question clearly and naturally in a complete sentence. "
            
                    "Do not return only a number, word, or fragment when a short complete "
                    "sentence can answer the question. "
            
                    "Preserve the meaning of the policy and do not add unsupported information."
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


def resolve_query(
    question: str,
    context: str,
) -> QueryResolution:
    client = _get_client()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": (
                   "You are a strict evidence resolver for an internal HR policy assistant. "

                    "Your ONLY task is to determine whether the user's question can be "
                    "answered using ONLY the provided policy context. "

                    "You MUST use only the provided policy context. "
                    "Do not use general knowledge, assumptions, or unsupported information. "

                    "Choose exactly one decision: 'answer', 'clarify', or 'refuse'. "

                    "Choose 'answer' only when the policy context contains sufficient "
                    "information to answer the user's specific question accurately. "

                    "Choose 'clarify' when the policy context is relevant to the user's "
                    "question, but the question is genuinely ambiguous or is missing "
                    "information needed to determine exactly what the user is asking. "

                    "Treat natural, informal, abbreviated, or grammatically incomplete "
                    "phrasing as equivalent to a clearly stated policy question when the "
                    "intended policy concept is unambiguous from the question and context. "

                    "Do not choose 'clarify' merely because of capitalization differences, "
                    "missing punctuation, informal grammar, or conversational wording. "

                    "For example, 'How many casual leaves we have' and "
                    "'How many casual leave days do employees receive?' should be treated "
                    "as the same question when the policy context clearly identifies "
                    "casual leave. "

                    "Choose 'clarify' only when there is genuine ambiguity about what "
                    "policy concept the user is asking about, or required information is "
                    "actually missing. "

                    "Choose 'refuse' when the policy context does not contain enough "
                    "relevant information to answer the question, or when the question "
                    "cannot be safely resolved from the context. "

                    "Do not answer the user's question. "
                    "Return only the decision. "

                    "Every material part of the user's question must be supported by the "
                    "provided policy context. If any material part of the requested answer "
                    "is not explicitly supported, do not choose 'answer'. "

                    "Do not partially answer a question when part of what the user is asking "
                    "is unsupported. Choose 'refuse' instead."
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
                "name": "query_resolution",
                "strict": True,
                "schema": QUERY_RESOLUTION_SCHEMA,
            },
        },
    )

    return QueryResolution.model_validate_json(
        response.choices[0].message.content
    )