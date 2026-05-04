"""LangGraph node functions."""
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..agents.research_agent import ResearchAgent
from ..agents.outline_agent import OutlineAgent
from ..agents.content_agent import ContentAgent, ContentCriticAgent
from ..agents.design_agent import DesignAgent
from ..agents.qa_agent import QAAgent
from ..rendering.renderer import SlideRenderer
from .state import PipelineState

console = Console()


def research_node(state: PipelineState) -> PipelineState:
    console.print("[bold cyan]→ ResearchAgent[/] gathering facts and context...")
    agent = ResearchAgent()
    research = agent.research(
        topic=state["topic"],
        audience=state.get("audience", "general professionals"),
        urls=state.get("urls"),
    )
    console.print(f"  [green]✓[/] {len(research.key_claims)} claims, "
                  f"{len(research.suggested_visualizations)} visualizations found")
    return {"research": research, "status": "researched"}


def outline_node(state: PipelineState) -> PipelineState:
    console.print("[bold cyan]→ OutlineAgent[/] designing narrative structure (extended thinking)...")
    agent = OutlineAgent()
    outline = agent.create_outline(
        topic=state["topic"],
        research=state["research"],
        slide_count=state.get("slide_count", 12),
        audience=state.get("audience", "general professionals"),
        tone=state.get("tone", "professional"),
        duration_minutes=state.get("duration_minutes", 20),
    )
    console.print(f"  [green]✓[/] {outline.total_slides} slides outlined: '{outline.title}'")
    return {"outline": outline, "status": "outlined"}


def content_node(state: PipelineState) -> PipelineState:
    outline = state["outline"]
    research = state["research"]
    console.print(f"[bold cyan]→ ContentAgent[/] writing {len(outline.slides)} slides...")

    agent = ContentAgent()
    slides = []
    for stub in outline.slides:
        # Pass adjacent slides for context
        adj = []
        if stub.index > 0:
            adj.append(outline.slides[stub.index - 1])
        if stub.index < len(outline.slides) - 1:
            adj.append(outline.slides[stub.index + 1])

        content = agent.write_slide(
            stub=stub,
            research=research,
            outline=outline,
            adjacent_slides=adj,
        )
        slides.append(content)
        console.print(f"  [dim]  Slide {stub.index + 1}/{len(outline.slides)}: {content.heading[:50]}[/]")

    console.print(f"  [green]✓[/] {len(slides)} slides written")
    return {"slides": slides, "status": "content_written"}


def content_critique_node(state: PipelineState) -> PipelineState:
    console.print("[bold cyan]→ ContentCriticAgent[/] reviewing cross-slide coherence...")
    agent = ContentCriticAgent()
    issues = agent.critique(state["slides"], state["outline"])
    high_severity = [i for i in issues if i.get("severity") == "high"]
    console.print(f"  [green]✓[/] {len(issues)} issues found ({len(high_severity)} high severity)")
    return {"critic_issues": issues, "status": "critique_done"}


def design_node(state: PipelineState) -> PipelineState:
    console.print("[bold cyan]→ DesignAgent[/] assigning layouts and design tokens...")
    agent = DesignAgent()
    design_spec = agent.design(
        slides=state["slides"],
        outline=state["outline"],
        theme_name=state.get("theme", "corporate_navy"),
    )
    console.print(f"  [green]✓[/] {len(design_spec.layout_assignments)} layouts assigned, "
                  f"theme: {design_spec.tokens.name}")
    return {"design_spec": design_spec, "status": "designed"}


def render_node(state: PipelineState) -> PipelineState:
    console.print("[bold cyan]→ Renderer[/] assembling PPTX...")
    renderer = SlideRenderer(state["design_spec"])
    prs = renderer.render_deck(state["slides"])
    output_path = state.get("output_path", "output.pptx")
    renderer.save(output_path)
    console.print(f"  [green]✓[/] Saved: {output_path}")
    return {"status": "rendered"}


def qa_node(state: PipelineState) -> PipelineState:
    console.print("[bold cyan]→ QAAgent[/] scoring slides...")
    agent = QAAgent()
    report = agent.review(state["slides"], state["design_spec"])
    low_count = sum(1 for s in report.scores if s.needs_revision)
    console.print(f"  [green]✓[/] Deck score: {report.overall_deck_score:.1f}/10, "
                  f"{low_count} slides need revision")
    return {"qa_report": report, "revision_count": state.get("revision_count", 0), "status": "qa_done"}


def revision_node(state: PipelineState) -> PipelineState:
    """Re-generate only slides flagged for revision."""
    report = state["qa_report"]
    outline = state["outline"]
    research = state["research"]
    slides = list(state["slides"])

    revision_indices = {r.slide_index for r in report.revision_requests}
    console.print(f"[bold yellow]→ Revision[/] re-generating {len(revision_indices)} slides: "
                  f"{sorted(revision_indices)}")

    agent = ContentAgent()
    for stub in outline.slides:
        if stub.index not in revision_indices:
            continue
        req = next((r for r in report.revision_requests if r.slide_index == stub.index), None)
        revision_context = ""
        if req:
            revision_context = (
                f"\n\nREVISION REQUIRED. Issues:\n"
                + "\n".join(f"- {i}" for i in req.issues)
                + "\n\nSuggestions:\n"
                + "\n".join(f"- {s}" for s in req.suggestions)
            )
        content = agent.write_slide(
            stub=stub,
            research=research,
            outline=outline,
        )
        slides[stub.index] = content
        console.print(f"  [dim]  Revised slide {stub.index + 1}[/]")

    return {
        "slides": slides,
        "revision_count": state.get("revision_count", 0) + 1,
        "status": "revised",
    }
