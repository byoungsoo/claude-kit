"""Diagram → PNG BytesIO.

Render chain:
  svg  field → cairosvg → PNG  (primary, AI-authored SVG XML)
  aws_diagram  field → base64 decode → PNG  (draw.io export)
"""
import base64
import io


_KOREAN_FONT_STACK = "Apple SD Gothic Neo, Malgun Gothic, NanumGothic, sans-serif"


def _inject_font(svg_str: str) -> str:
    """Ensure the SVG root element has a Korean-capable font-family."""
    import re
    # 이미 font-family가 있으면 한글 폰트 스택으로 교체
    if 'font-family=' in svg_str:
        svg_str = re.sub(
            r'font-family=["\'][^"\']*["\']',
            f'font-family="{_KOREAN_FONT_STACK}"',
            svg_str,
        )
    else:
        # <svg ...> 루트 태그에 삽입
        svg_str = re.sub(
            r'(<svg\b[^>]*?)(>)',
            rf'\1 font-family="{_KOREAN_FONT_STACK}"\2',
            svg_str,
            count=1,
        )
    return svg_str


def render_svg(svg_str: str) -> io.BytesIO:
    """Convert SVG XML string to PNG BytesIO via cairosvg."""
    import cairosvg
    svg_str = _inject_font(svg_str)
    png_bytes = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), scale=2.0)
    buf = io.BytesIO(png_bytes)
    buf.seek(0)
    return buf


def render_aws_diagram(png_base64: str) -> io.BytesIO:
    """Decode draw.io-exported PNG base64 to BytesIO."""
    data = base64.b64decode(png_base64)
    buf = io.BytesIO(data)
    buf.seek(0)
    return buf
