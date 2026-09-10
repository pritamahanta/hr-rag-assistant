import logging

from app.models.schemas import AnswerResponse
from app.services.citations import build_citations
from app.services.llm import generate_answer, resolve_query
from app.services.retrieval import retrieve_chunks


logger = logging.getLogger(__name__)


class QueryServiceError(Exception):
    """Raised when the query pipeline fails unexpectedly."""


REFUSAL_MESSAGE = (
    "I couldn't find enough information in the available HR policies to answer that. "
    "Please contact HR."
)

CLARIFICATION_MESSAGE = (
    "Could you please provide a little more detail about what you're asking about?"
)


def build_context(chunks) -> str:
    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"[Source ID: {chunk.chunk_id}]\n"
            f"Document: {chunk.document}\n"
            f"Section: {chunk.section}\n"
            f"Page: {chunk.page}\n"
            f"Content: {chunk.text}"
        )

    return "\n\n---\n\n".join(context_parts)


def is_enumeration_query(question: str) -> bool:
    question = question.lower()

    patterns = (
        "what types",
        "which types",
        "how many types",
        "what are the types",
        "list the types",
    )

    return any(pattern in question for pattern in patterns)


def answer_query(
    question: str,
    top_k: int = 5,
) -> AnswerResponse:

    try:
        retrieval_k = 8 if is_enumeration_query(question) else top_k

        chunks = retrieve_chunks(
            query=question,
            top_k=retrieval_k,
        )
    except Exception as exc:
        logger.exception(
            "Retrieval failed for query: %r",
            question,
        )
        raise QueryServiceError("Retrieval failed.") from exc

    if not chunks:
        return AnswerResponse(
            answer=REFUSAL_MESSAGE,
            citations=[],
        )

    context = build_context(chunks)

    try:
        resolution = resolve_query(
            question=question,
            context=context,
        )
    except Exception as exc:
        logger.exception(
            "Query resolution failed for query: %r",
            question,
        )
        raise QueryServiceError("Query resolution failed.") from exc

    if resolution.decision == "refuse":
        return AnswerResponse(
            answer=REFUSAL_MESSAGE,
            citations=[],
        )

    if resolution.decision == "clarify":
        return AnswerResponse(
            answer=CLARIFICATION_MESSAGE,
            citations=[],
        )

    try:
        llm_response = generate_answer(
            question=question,
            context=context,
        )
    except Exception as exc:
        logger.exception(
            "LLM call failed while answering query: %r",
            question,
        )
        raise QueryServiceError("Answer generation failed.") from exc

    if not llm_response.source_ids:
        return AnswerResponse(
            answer=REFUSAL_MESSAGE,
            citations=[],
        )

    citations = build_citations(
        chunks,
        llm_response.source_ids,
    )

    if not citations:
        return AnswerResponse(
            answer=REFUSAL_MESSAGE,
            citations=[],
        )

    return AnswerResponse(
        answer=llm_response.answer,
        citations=citations,
    )

