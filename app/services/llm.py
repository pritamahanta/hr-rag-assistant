from groq import Groq

from app.core.config import GROQ_API_KEY
from app.models.schemas import LLMResponse


MODEL_NAME = "openai/gpt-oss-20b"

client = Groq(api_key=GROQ_API_KEY)


LLM_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
        },
    },
    "required": [
        "answer",
    ],
    "additionalProperties": False,
}


def generate_answer(
    question: str,
    context: str,
) -> LLMResponse:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an internal HR policy assistant. "
                    "Answer the user's question using only the provided policy context. "
                    "Do not use outside knowledge. "
                    "If the context does not contain enough information to answer "
                    "the question, clearly say that the information is not available "
                    "in the provided policies."
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