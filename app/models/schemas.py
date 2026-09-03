from pydantic import BaseModel, Field


class Citation(BaseModel):
    document: str
    section: str
    page: str | int = ""


class LLMResponse(BaseModel):
    answer: str


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)