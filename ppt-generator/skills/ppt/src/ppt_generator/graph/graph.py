"""LangGraph StateGraph definition."""
from langgraph.graph import StateGraph, END

from .state import PipelineState
from .nodes import (
    research_node,
    outline_node,
    content_node,
    content_critique_node,
    design_node,
    render_node,
    qa_node,
    revision_node,
)
from .conditions import critique_ok, qa_routing


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Nodes
    graph.add_node("research", research_node)
    graph.add_node("outline", outline_node)
    graph.add_node("content", content_node)
    graph.add_node("critique", content_critique_node)
    graph.add_node("design", design_node)
    graph.add_node("render", render_node)
    graph.add_node("qa", qa_node)
    graph.add_node("revision", revision_node)

    # Edges
    graph.set_entry_point("research")
    graph.add_edge("research", "outline")
    graph.add_edge("outline", "content")
    graph.add_edge("content", "critique")

    # Critique always proceeds to design (issues inform design, don't block)
    graph.add_conditional_edges("critique", critique_ok, {"design": "design"})

    graph.add_edge("design", "render")
    graph.add_edge("render", "qa")

    # QA conditionally triggers revision
    graph.add_conditional_edges(
        "qa",
        qa_routing,
        {"revise": "revision", "end": END},
    )

    # After revision: re-render and re-QA
    graph.add_edge("revision", "render")

    return graph.compile()


def run_pipeline(
    topic: str,
    slide_count: int = 12,
    theme: str = "corporate_navy",
    output_path: str = "output.pptx",
    audience: str = "general professionals",
    tone: str = "professional",
    urls: list[str] | None = None,
    duration_minutes: int = 20,
) -> PipelineState:
    app = build_graph()

    initial_state: PipelineState = {
        "topic": topic,
        "slide_count": slide_count,
        "theme": theme,
        "output_path": output_path,
        "audience": audience,
        "tone": tone,
        "urls": urls or [],
        "duration_minutes": duration_minutes,
        "revision_count": 0,
        "errors": [],
    }

    final_state = app.invoke(initial_state)
    return final_state
