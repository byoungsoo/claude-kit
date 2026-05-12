"""Pre-defined slide layout templates.

Claude selects a template by name; the renderer resolves zone coordinates.
Each zone is a tuple (x, y, w, h) in EMU.

Slide dimensions: 9144000 × 5143500 EMU (16:9 widescreen)
Heading occupies y=0.08–0.20, subheading y=0.20–0.27.
Content zone: y=0.27–0.88 (footer at y=0.93).
"""

SLIDE_W = 9144000
SLIDE_H = 5143500

_ML = 0.06  # margin left
_MR = 0.06  # margin right
_CT = 0.31  # content top (heading 0.08~0.20 + subheading ~0.29 + gap)
_CB = 0.88  # content bottom (footer starts at 0.93)
_CH = _CB - _CT  # content height = 0.61
_FW = 1.0 - _ML - _MR  # full content width = 0.88


def _z(x: float, y: float, w: float, h: float) -> tuple[int, int, int, int]:
    return (
        int(x * SLIDE_W),
        int(y * SLIDE_H),
        int(w * SLIDE_W),
        int(h * SLIDE_H),
    )


# Template registry: name → {zone_name: (x, y, w, h) EMU}
TEMPLATES: dict[str, dict[str, tuple[int, int, int, int]]] = {
    # Full-width text (no visualization)
    "text_only": {
        "text": _z(_ML, _CT, _FW, _CH),
    },
    # Full-width visualization (no body text, or text encoded inside SVG)
    "viz_only": {
        "viz": _z(_ML, _CT, _FW, _CH),
    },
    # Short text at top (~14% height), large viz below with gap
    "text_top_viz_bottom": {
        "text": _z(_ML, _CT, _FW, 0.14),
        "viz":  _z(_ML, _CT + 0.14 + 0.04, _FW, _CH - 0.14 - 0.04),
    },
    # Text on left (~32% width), viz on right (~53% width)
    "text_left_viz_right": {
        "text": _z(_ML, _CT, 0.32, _CH),
        "viz":  _z(_ML + 0.32 + 0.04, _CT, _FW - 0.32 - 0.04, _CH),
    },
    # Viz on left (~53% width), text on right (~32% width)
    "viz_left_text_right": {
        "viz":  _z(_ML, _CT, _FW - 0.32 - 0.04, _CH),
        "text": _z(_ML + _FW - 0.32, _CT, 0.32, _CH),
    },
    # Two equal text columns (body_blocks split evenly)
    "two_column_text": {
        "left":  _z(_ML, _CT, 0.41, _CH),
        "right": _z(_ML + 0.41 + 0.03, _CT, 0.44, _CH),
    },
}

# Recommended SVG canvas size (width × height in px) per template viz zone.
# _CT=0.31, _CB=0.88, _CH=0.57, SLIDE_H/SLIDE_W = 5143500/9144000 ≈ 0.5625
# viz_only:            AR = (_FW/_CH) * (SLIDE_W/SLIDE_H) = (0.88/0.57) * 1.778 ≈ 2.74
# text_left_viz_right: viz_w=0.51, AR = (0.51/0.57) * 1.778 ≈ 1.59
# text_top_viz_bottom: viz_h=0.39, AR = (0.88/0.39) * 1.778 ≈ 4.01
SVG_CANVAS: dict[str, tuple[int, int]] = {
    "viz_only":            (900, 328),
    "text_left_viz_right": (900, 566),
    "viz_left_text_right": (900, 566),
    "text_top_viz_bottom": (900, 224),
    "two_column_text":     None,
    "text_only":           None,
}


def get_template(name: str) -> dict[str, tuple[int, int, int, int]]:
    return TEMPLATES.get(name, TEMPLATES["text_only"])


def get_svq_canvas(name: str) -> tuple[int, int] | None:
    return SVG_CANVAS.get(name)
