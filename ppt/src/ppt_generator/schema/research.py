from pydantic import BaseModel, Field
from typing import Literal


class SourceCitation(BaseModel):
    title: str
    source: str
    year: int | None = None
    url: str | None = None


class KeyClaim(BaseModel):
    claim: str
    confidence: float = Field(ge=0.0, le=1.0)
    citation: SourceCitation | None = None


class SuggestedVisualization(BaseModel):
    type: Literal["bar_chart", "line_chart", "pie_chart", "radar_chart", "scatter_chart", "diagram", "table"]
    title: str
    description: str
    mermaid: str | None = None  # diagram 타입일 때만 사용
    data_hint: str | None = None  # chart 타입일 때 데이터 구조 힌트


class ResearchBundle(BaseModel):
    topic_summary: str
    key_claims: list[KeyClaim]
    suggested_visualizations: list[SuggestedVisualization]
    narrative_hook: str  # 발표 오프닝에 쓸 임팩트 있는 문장
    audience_assumptions: str  # 대상 청중에 대한 가정
    key_themes: list[str]  # 3~5개 핵심 테마
