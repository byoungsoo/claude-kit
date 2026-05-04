"""CLI entry point: typer + rich."""
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(name="ppt-generator", help="AI-powered PPT generator using multi-agent pipeline.")
console = Console()

THEMES = ["corporate_navy", "startup_bold", "dark_tech", "academic_clean"]


@app.command()
def generate(
    topic: str = typer.Argument(..., help="Presentation topic"),
    slides: int = typer.Option(12, "--slides", "-s", help="Number of slides"),
    theme: str = typer.Option("corporate_navy", "--theme", "-t",
                               help=f"Theme: {', '.join(THEMES)}"),
    output: str = typer.Option("output.pptx", "--output", "-o", help="Output file path"),
    audience: str = typer.Option("general professionals", "--audience", "-a",
                                  help="Target audience"),
    tone: str = typer.Option("professional", "--tone",
                              help="Tone: professional, casual, academic, inspiring"),
    urls: Optional[list[str]] = typer.Option(None, "--url", "-u",
                                              help="Source URLs for research (repeatable)"),
    duration: int = typer.Option(20, "--duration", "-d",
                                  help="Presentation duration in minutes"),
):
    """Generate a sophisticated PPT presentation using multi-agent AI pipeline."""
    if theme not in THEMES:
        console.print(f"[red]Unknown theme '{theme}'. Available: {', '.join(THEMES)}[/]")
        raise typer.Exit(1)

    console.print(Panel.fit(
        f"[bold]PPT Generator[/]\n\n"
        f"Topic: [cyan]{topic}[/]\n"
        f"Slides: {slides} | Theme: {theme} | Duration: {duration}min\n"
        f"Audience: {audience}",
        title="Starting Pipeline",
        border_style="blue",
    ))

    start = time.time()

    from ..graph.graph import run_pipeline
    try:
        final_state = run_pipeline(
            topic=topic,
            slide_count=slides,
            theme=theme,
            output_path=output,
            audience=audience,
            tone=tone,
            urls=list(urls) if urls else [],
            duration_minutes=duration,
        )
    except Exception as e:
        console.print(f"\n[red]Pipeline failed: {e}[/]")
        raise typer.Exit(1)

    elapsed = time.time() - start

    # Summary report
    qa_report = final_state.get("qa_report")
    deck_score = qa_report.overall_deck_score if qa_report else "N/A"
    revisions = final_state.get("revision_count", 0)

    tbl = Table(title="Pipeline Summary", border_style="green")
    tbl.add_column("Stage", style="cyan")
    tbl.add_column("Result")
    tbl.add_row("Research", f"{len(final_state['research'].key_claims)} claims gathered")
    tbl.add_row("Outline", f"{final_state['outline'].total_slides} slides planned")
    tbl.add_row("Content", f"{len(final_state['slides'])} slides written")
    tbl.add_row("Design", f"Theme: {final_state['design_spec'].tokens.name}")
    tbl.add_row("QA Score", f"{deck_score}/10")
    tbl.add_row("Revisions", str(revisions))
    tbl.add_row("Output", output)
    tbl.add_row("Time", f"{elapsed:.1f}s")

    console.print(tbl)
    console.print(f"\n[bold green]✓ Done![/] Saved to [cyan]{output}[/]")


@app.command()
def themes():
    """List available themes."""
    tbl = Table(title="Available Themes")
    tbl.add_column("Name", style="cyan")
    tbl.add_column("Style")
    tbl.add_row("corporate_navy", "Navy/orange, professional corporate")
    tbl.add_row("startup_bold", "Purple/pink, bold startup vibes")
    tbl.add_row("dark_tech", "Dark mode, blue/green tech")
    tbl.add_row("academic_clean", "White/navy, minimal academic")
    console.print(tbl)


def main():
    app()


if __name__ == "__main__":
    main()
