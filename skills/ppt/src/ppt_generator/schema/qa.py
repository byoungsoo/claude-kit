from pydantic import BaseModel, Field
from typing import Literal


class SlideScore(BaseModel):
    slide_index: int
    visual_balance: int = Field(ge=1, le=10)
    content_clarity: int = Field(ge=1, le=10)
    consistency: int = Field(ge=1, le=10)
    overall: float

    @property
    def needs_revision(self) -> bool:
        return self.overall < 7.0


class RevisionRequest(BaseModel):
    slide_index: int
    target: Literal["content", "design", "both"]
    issues: list[str]
    suggestions: list[str]


class QAReport(BaseModel):
    scores: list[SlideScore]
    revision_requests: list[RevisionRequest] = Field(default_factory=list)
    overall_deck_score: float
    summary: str

    @property
    def has_revisions(self) -> bool:
        return len(self.revision_requests) > 0
