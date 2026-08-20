"""render.py — JSON 데이터를 받아 PPTX를 조립하는 순수 렌더러 CLI.

사용법:
  python3 -m src.ppt_generator.cli.render \
    --slides slides.json \
    --design design.json \
    --theme corporate_navy \
    --output output.pptx
"""
import json
import sys
from pathlib import Path

import typer
from rich.console import Console

from ..schema.content import SlideContent
from ..schema.design import DesignSpec, DesignTokens
from ..rendering.renderer import SlideRenderer

app = typer.Typer(name="render", help="Render PPTX from JSON data produced by Claude agents.")
console = Console()

def _find_package_root() -> Path:
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Cannot find package root (pyproject.toml not found)")

THEMES_DIR = _find_package_root() / "themes"
VALID_THEMES = ["corporate_navy", "startup_bold", "dark_tech", "academic_clean"]


def load_theme(theme_name: str) -> DesignTokens:
    theme_file = THEMES_DIR / f"{theme_name}.json"
    if not theme_file.exists():
        console.print(f"[red]Theme file not found: {theme_file}[/]")
        raise typer.Exit(1)
    return DesignTokens(**json.loads(theme_file.read_text()))


@app.command()
def render(
    slides_file: str = typer.Option(..., "--slides", "-s", help="Path to slides JSON file"),
    design_file: str = typer.Option(..., "--design", "-d", help="Path to design spec JSON file"),
    theme: str = typer.Option("corporate_navy", "--theme", "-t", help=f"Theme: {', '.join(VALID_THEMES)}"),
    output: str = typer.Option("output.pptx", "--output", "-o", help="Output PPTX path"),
):
    """Assemble PPTX from Claude-generated JSON data."""

    # Load slides
    slides_path = Path(slides_file)
    if not slides_path.exists():
        console.print(f"[red]Slides file not found: {slides_file}[/]")
        raise typer.Exit(1)
    slides_data = json.loads(slides_path.read_text())
    slides = [SlideContent(**s) for s in slides_data]

    # Load design spec
    design_path = Path(design_file)
    if not design_path.exists():
        console.print(f"[red]Design file not found: {design_file}[/]")
        raise typer.Exit(1)
    design_data = json.loads(design_path.read_text())
    design_spec = DesignSpec(**design_data)

    # Inject theme tokens
    design_spec.tokens = load_theme(theme)

    # Render
    console.print(f"Rendering {len(slides)} slides with theme [cyan]{theme}[/]...")
    renderer = SlideRenderer(design_spec)
    renderer.render_deck(slides)
    renderer.save(output)

    console.print(f"[bold green]✓ Done![/] Saved to [cyan]{output}[/]")


def main():
    app()


if __name__ == "__main__":
    main()
