"""Mermaid diagram → PNG BytesIO.

Render chain:
  1. mmdc CLI (best quality) — used if @mermaid-js/mermaid-cli is installed
  2. matplotlib flowchart renderer (parses basic Mermaid syntax) — always available
  3. minimal text placeholder — absolute fallback
"""
import asyncio
import io
import os
import re
import tempfile


async def _render_mermaid_cli(mermaid_str: str) -> io.BytesIO | None:
    """Render via mmdc if available on PATH."""
    input_path = ""
    output_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as f:
            f.write(mermaid_str)
            input_path = f.name
        output_path = input_path.replace(".mmd", ".png")

        proc = await asyncio.create_subprocess_exec(
            "mmdc", "-i", input_path, "-o", output_path,
            "-w", "1200", "-H", "800", "--backgroundColor", "white",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode == 0 and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                buf = io.BytesIO(f.read())
            return buf
    except (FileNotFoundError, asyncio.TimeoutError):
        pass
    finally:
        for p in (input_path, output_path):
            if p and os.path.exists(p):
                os.unlink(p)
    return None


# ──────────────────────────────────────────────────────────────────────────
# Matplotlib-based Mermaid renderer
# Handles: flowchart LR/TD, graph LR/TD
# ──────────────────────────────────────────────────────────────────────────

def _parse_mermaid(mermaid_str: str) -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    """Parse simple Mermaid flowchart. Returns (nodes, edges).

    nodes: {id: label}
    edges: [(from_id, to_id, label)]
    """
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str, str]] = []

    node_pat = re.compile(r'(\w[\w\s]*?)\[([^\]]+)\]')
    edge_pat = re.compile(
        r'(\w[\w\s]*?)(?:\[([^\]]*)\])?\s*'
        r'(?:-->|->|--\|?>?|===>?|-.->)'
        r'(?:\|([^|]+)\|)?\s*'
        r'(\w[\w\s]*?)(?:\[([^\]]*)\])?'
    )

    for line in mermaid_str.splitlines():
        line = line.strip()
        if not line or line.startswith('%%') or line.lower().startswith(('flowchart', 'graph', 'subgraph', 'end')):
            # Extract direction but skip
            continue

        # Find standalone node definitions: A[Label]
        for m in node_pat.finditer(line):
            nid = m.group(1).strip()
            nodes[nid] = m.group(2).strip()

        # Find edges: A[Label] --> B[Label] or A --> B
        em = edge_pat.search(line)
        if em:
            src_id = em.group(1).strip()
            src_lbl = em.group(2)
            edge_lbl = em.group(3) or ""
            dst_id = em.group(4).strip()
            dst_lbl = em.group(5)
            if src_lbl and src_id not in nodes:
                nodes[src_id] = src_lbl.strip()
            elif src_id not in nodes:
                nodes[src_id] = src_id
            if dst_lbl and dst_id not in nodes:
                nodes[dst_id] = dst_lbl.strip()
            elif dst_id not in nodes:
                nodes[dst_id] = dst_id
            edges.append((src_id, dst_id, edge_lbl.strip()))

    return nodes, edges


def _layout_nodes(
    nodes: dict[str, str],
    edges: list[tuple[str, str, str]],
    direction: str = "LR",
) -> dict[str, tuple[float, float]]:
    """Assign (x, y) positions using a simple level-based layout."""
    # Build adjacency for topological layering
    from collections import defaultdict, deque

    out_edges: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = {n: 0 for n in nodes}
    for src, dst, _ in edges:
        out_edges[src].append(dst)
        if dst in in_degree:
            in_degree[dst] = in_degree.get(dst, 0) + 1

    # Kahn's algorithm for layers
    queue = deque(n for n in nodes if in_degree.get(n, 0) == 0)
    layer: dict[str, int] = {}
    while queue:
        n = queue.popleft()
        for nb in out_edges[n]:
            in_degree[nb] = in_degree.get(nb, 1) - 1
            layer[nb] = max(layer.get(nb, 0), layer.get(n, 0) + 1)
            if in_degree[nb] == 0:
                queue.append(nb)

    # Group by layer
    layer_groups: dict[int, list[str]] = defaultdict(list)
    for n in nodes:
        layer_groups[layer.get(n, 0)].append(n)

    positions: dict[str, tuple[float, float]] = {}
    max_layer = max(layer_groups.keys()) if layer_groups else 0
    for lv, members in layer_groups.items():
        for i, n in enumerate(members):
            col = lv / max(max_layer, 1)
            row = (i + 0.5) / len(members)
            if direction == "TD":
                positions[n] = (row, 1.0 - col)
            else:  # LR
                positions[n] = (col, 1.0 - row)

    return positions


def _render_matplotlib(mermaid_str: str, title: str = "") -> io.BytesIO:
    """Render Mermaid flowchart as a matplotlib figure."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyArrowPatch

    # Detect direction
    direction = "LR"
    for line in mermaid_str.splitlines():
        stripped = line.strip().lower()
        if "flowchart td" in stripped or "graph td" in stripped:
            direction = "TD"
            break

    nodes, edges = _parse_mermaid(mermaid_str)

    if not nodes:
        return _render_text_placeholder(mermaid_str, title)

    positions = _layout_nodes(nodes, edges, direction)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.axis("off")

    BOX_W, BOX_H = 0.14, 0.09
    NODE_COLOR = "#E8EDF5"
    NODE_EDGE = "#3B5998"
    TEXT_COLOR = "#1A1A2E"
    ARROW_COLOR = "#555555"

    # Draw edges
    for src, dst, lbl in edges:
        if src not in positions or dst not in positions:
            continue
        x1, y1 = positions[src]
        x2, y2 = positions[dst]
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="->", color=ARROW_COLOR,
                lw=1.2, connectionstyle="arc3,rad=0.05"
            ),
        )
        if lbl:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my, lbl, ha="center", va="center",
                    fontsize=6, color=ARROW_COLOR,
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                              edgecolor="none", alpha=0.8))

    # Draw nodes
    for nid, (x, y) in positions.items():
        label = nodes.get(nid, nid)
        box = mpatches.FancyBboxPatch(
            (x - BOX_W / 2, y - BOX_H / 2), BOX_W, BOX_H,
            boxstyle="round,pad=0.01",
            facecolor=NODE_COLOR, edgecolor=NODE_EDGE, linewidth=1.2,
        )
        ax.add_patch(box)
        # Wrap long labels
        words = label.split()
        lines = []
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 > 14:
                if cur:
                    lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
        ax.text(x, y, "\n".join(lines[:3]),
                ha="center", va="center",
                fontsize=7, color=TEXT_COLOR, fontweight="bold",
                multialignment="center")

    if title:
        ax.set_title(title, fontsize=9, color="#333333", pad=4)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_text_placeholder(mermaid_str: str, label: str) -> io.BytesIO:
    """Last-resort: render mermaid source as styled text."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lines = [l for l in mermaid_str.splitlines() if l.strip()][:20]
    text = "\n".join(lines)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#F8F9FA")
    ax.set_facecolor("#F8F9FA")
    ax.text(0.5, 0.95, label, ha="center", va="top",
            fontsize=12, fontweight="bold", color="#1A1A2E",
            transform=ax.transAxes)
    ax.text(0.05, 0.80, text, ha="left", va="top",
            fontsize=8, color="#374151", fontfamily="monospace",
            transform=ax.transAxes, wrap=True)
    ax.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────

async def render_diagram_async(mermaid_str: str, page_name: str = "diagram") -> io.BytesIO:
    result = await _render_mermaid_cli(mermaid_str)
    if result:
        return result
    return _render_matplotlib(mermaid_str, page_name)


def render_diagram_sync(mermaid_str: str, page_name: str = "diagram") -> io.BytesIO:
    """Synchronous entry point used by SlideRenderer."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run,
                                     render_diagram_async(mermaid_str, page_name))
                return future.result(timeout=60)
        else:
            return loop.run_until_complete(render_diagram_async(mermaid_str, page_name))
    except Exception:
        pass
    return _render_matplotlib(mermaid_str, page_name)
