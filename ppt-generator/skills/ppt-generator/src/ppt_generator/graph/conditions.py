"""Conditional edge predicate functions for LangGraph."""
from .state import PipelineState

MAX_REVISIONS = 2


def critique_ok(state: PipelineState) -> str:
    """Route after content critique: proceed or flag (we always proceed, critique informs design)."""
    return "design"


def qa_routing(state: PipelineState) -> str:
    """Route after QA: end or trigger revision."""
    report = state.get("qa_report")
    revision_count = state.get("revision_count", 0)

    if report is None:
        return "end"

    if report.has_revisions and revision_count < MAX_REVISIONS:
        return "revise"

    return "end"
