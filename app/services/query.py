from app.models.schemas import AnswerResponse
from app.services.citations import build_citations
from app.services.llm import generate_answer
from app.services.retrieval import is_retrieval_strong, retrieve_chunks


REFUSAL_MESSAGE = (
    "I don't have enough information in the uploaded policies. "
    "Please contact HR."
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


def answer_query(
    question: str,
    top_k: int = 5,
) -> AnswerResponse:
    chunks = retrieve_chunks(
        query = question,
        top_k = top_k,
    )

    if not is_retrieval_strong(chunks):
        return AnswerResponse(
            answer = REFUSAL_MESSAGE,
            citations = [],
        )

    context = build_context(chunks)

    try:
        llm_response = generate_answer(
            question = question,
            context = context,
        )
    except Exception:
        return AnswerResponse(
            answer = REFUSAL_MESSAGE,
            citations = [],
        )

    citations = build_citations(
        chunks,
        llm_response.source_ids,
    )

    return AnswerResponse (
        answer = llm_response.answer,
        citations = citations,
    )