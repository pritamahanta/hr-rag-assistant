from pydantic import BaseModel, Field
from typing import Literal


class Citation(BaseModel):
    document: str
    section: str
    page: str | int = ""


class LLMResponse(BaseModel):
    decision: Literal["answer", "clarify", "refuse"]
    answer: str
    source_ids: list[str] = Field(default_factory=list)


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)

class QueryRequest(BaseModel):
    question: str = Field(min_length=1)