from pydantic import BaseModel, Field
from typing import Literal


SlideType = Literal[
    "title",
    "section",
    "content_text",
    "content_chart",
    "content_diagram",
    "two_column",
    "three_column",
    "full_width_chart",
    "data_story",
    "comparison_table",
    "quote",
    "closing",
]


class NarrativeTransition(BaseModel):
    from_slide: int
    to_slide: int
    transition_logic: str  # 왜 이 슬라이드가 다음 슬라이드로 이어지는가


class SlideStub(BaseModel):
    index: int
    slide_type: SlideType
    purpose: str  # 이 슬라이드의 존재 이유
    key_message: str  # 청중이 이 슬라이드에서 가져가야 할 핵심 메시지
    content_hints: list[str]  # ContentAgent에 넘길 내용 힌트
    estimated_complexity: Literal["low", "medium", "high"]
    has_chart: bool = False
    has_diagram: bool = False
    has_table: bool = False


class NarrativeArc(BaseModel):
    opening_hook: str
    problem_statement: str
    resolution_journey: str
    closing_impact: str


class DeckOutline(BaseModel):
    title: str
    subtitle: str | None = None
    total_slides: int
    narrative_arc: NarrativeArc
    slides: list[SlideStub]
    transitions: list[NarrativeTransition] = Field(default_factory=list)
    estimated_duration_minutes: int
