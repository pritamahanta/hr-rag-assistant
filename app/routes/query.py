from fastapi import APIRouter, HTTPException

from app.models.schemas import AnswerResponse, QueryRequest
from app.services.query import QueryServiceError, answer_query


router = APIRouter(tags=["Query"])


@router.post("/query", response_model=AnswerResponse)
def query_policies(request: QueryRequest) -> AnswerResponse:
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question must not be empty.",
        )

    try:
        return answer_query(question=question)
    except QueryServiceError:
        raise HTTPException(
            status_code=500,
            detail="The query service is temporarily unavailable. Please try again.",
        )