"""PipelineState: shared state across all LangGraph nodes."""
from typing import TypedDict, Annotated
import operator

from ..schema.research import ResearchBundle
from ..schema.outline import DeckOutline
from ..schema.content import SlideContent
from ..schema.design import DesignSpec
from ..schema.qa import QAReport


class PipelineState(TypedDict, total=False):
    # Input
    topic: str
    audience: str
    tone: str
    slide_count: int
    theme: str
    output_path: str
    urls: list[str]
    duration_minutes: int

    # Pipeline outputs
    research: ResearchBundle
    outline: DeckOutline
    slides: list[SlideContent]
    critic_issues: list[dict]
    design_spec: DesignSpec
    qa_report: QAReport

    # Control
    revision_count: int
    errors: Annotated[list[str], operator.add]
    status: str
