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
        "clarification": {
            "type": "string",
        },
    },
    "required": [
        "decision",
        "clarification",
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
                    "You are an internal policy assistant. "
                    "Answer the user's question using ONLY the provided policy context. "
                    "Do not use general knowledge, assumptions, outside information, or rules "
                    "that are not supported by the provided context. "

                    "Answer only when the retrieved context contains sufficient evidence for "
                    "the user's specific question. Preserve the meaning, scope, and conditions "
                    "of the policy. Do not strengthen, weaken, extend, or reinterpret a rule. "

                    "Do not create a new permission, entitlement, eligibility condition, "
                    "restriction, limit, exception, or guarantee by combining separate policy "
                    "statements unless the resulting conclusion is directly supported by the "
                    "policy context. Simple arithmetic or direct aggregation of explicitly "
                    "stated values is allowed when it directly answers the question. "

                    "Do not treat the absence of a prohibition as permission, and do not treat "
                    "the presence of related restrictions as evidence that an action is "
                    "generally prohibited. Answer only what the policy explicitly establishes. "

                    "When the user asks whether a specific action, behavior, or scenario is "
                    "permitted, require explicit policy support for that permission. Do not infer "
                    "permission or prohibition from related rules, procedures, limits, "
                    "entitlements, or conditions. "

                    "Do not convert separate policy facts into a new permission, prohibition, "
                    "eligibility condition, entitlement, duration, or allowance unless the policy "
                    "explicitly states that conclusion. "

                    "If the context does not sufficiently support the requested conclusion, "
                    "return an empty answer and an empty source_ids array. "
                    "Do not fill gaps with plausible assumptions. "

                    "Return source_ids only for context entries that directly support claims "
                    "made in the answer. Do not cite a source merely because it is related "
                    "to the topic. "

                    "For list, comparison, count, or multi-item answers, make sure every "
                    "important item or claim is directly supported by the cited source or "
                    "sources. When multiple context entries are required, include the source "
                    "that directly establishes each distinct claim. Prefer the most specific "
                    "source available when several sources mention the same topic. "

                    "Do not include unnecessary or merely related source_ids. "
                    "Never invent, modify, or guess a source_id. "

                    "Keep the answer focused on what the user asked. "
                    "Do not add unrelated policy details. "
                    "Use clear, natural, complete sentences. "

                    "Return only the structured response defined by the schema."
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
                    "You are a strict evidence resolver for an internal policy assistant. "
                    "Your ONLY task is to decide whether the user's question can be answered "
                    "using ONLY the provided policy context. "

                    "Choose exactly one decision: 'answer', 'clarify', or 'refuse'. "

                    "'answer' means the user's intended question is sufficiently clear and "
                    "the provided policy context contains sufficient evidence to answer it "
                    "accurately without introducing an unsupported policy rule or conclusion. "

                    "'clarify' means the user's question is genuinely ambiguous or "
                    "underspecified because more than one materially different interpretation "
                    "or answer is possible, and a missing distinction is required to determine "
                    "what the user intends. "

                    "Do NOT choose 'clarify' merely because the policy cannot answer the "
                    "question. If there is one clear interpretation of what the user is "
                    "asking, the question is not ambiguous. "

                    "When a question is materially ambiguous because the policy contains "
                    "multiple distinct values, categories, rules, entities, or possible "
                    "answers that could reasonably apply, choose 'clarify' unless the user "
                    "clearly identifies which one they mean. Do not choose 'answer' merely "
                    "because the context contains information for all possible interpretations. "

                    "'refuse' means the user's intent is clear, but the provided policy "
                    "context does not contain enough evidence to answer the question safely "
                    "and accurately. "

                    "Use 'refuse' when the policy is silent or does not explicitly establish "
                    "the requested fact, permission, prohibition, eligibility, condition, "
                    "exception, or other conclusion. "

                    "If the user asks whether a specific action, behavior, or scenario is "
                    "permitted or prohibited, require explicit support for that conclusion "
                    "in the provided policy context. Do not infer permission or prohibition "
                    "from related rules, restrictions, procedures, limits, entitlements, or "
                    "from the absence of a prohibition. If the policy does not explicitly "
                    "establish the requested conclusion, choose 'refuse'. "

                    "Treat informal wording, abbreviations, missing punctuation, and minor "
                    "grammatical errors as equivalent to a clear question when the intended "
                    "meaning is still unambiguous. "

                    "Every material part of the requested answer must be supported by the "
                    "provided context. If any material part is unsupported, do not choose "
                    "'answer'. Do not partially answer a request while ignoring unsupported "
                    "parts. "

                    "Do not infer a new permission, entitlement, eligibility condition, "
                    "restriction, limit, exception, or guarantee merely by combining separate "
                    "policy statements. Distinguish between information explicitly stated in "
                    "the policy, straightforward arithmetic over explicit values, and "
                    "conclusions that require an unstated policy assumption. "

                    "If answering the question requires introducing an unstated policy rule "
                    "or assumption, choose 'refuse'. "

                    "When choosing 'clarify', also provide a short clarification question. "
                    "Construct it strictly from the provided policy context and the user's "
                    "question. Ask only for the missing distinction or information needed to "
                    "choose among materially different context-supported interpretations. "
                    "Use only categories, values, entities, and terminology explicitly present "
                    "in the context; never introduce a fact, policy option, leave type, benefit, "
                    "or term that the context does not support. Keep it concise and natural. "
                    "For 'answer' and 'refuse', set clarification to an empty string. "

                    "Use only the provided policy context. "
                    "Do not use general knowledge or outside information. "

                    "Do not answer the user's question directly. "
                    "Return both the decision and clarification fields."
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