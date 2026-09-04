from pydantic import BaseModel, Field


class Citation(BaseModel):
    document: str
    section: str
    page: str | int = ""


class LLMResponse(BaseModel):
    answer: str
    source_ids: list[str] = Field(default_factory=list)


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)