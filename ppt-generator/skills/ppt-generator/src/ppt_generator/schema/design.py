from pydantic import BaseModel, Field
from typing import Literal, Optional


class ColorPalette(BaseModel):
    primary: str      # hex
    secondary: str    # hex
    accent: str       # hex
    background: str   # hex
    surface: str      # hex
    text_primary: str # hex
    text_secondary: str # hex
    success: str = "#22C55E"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    border: str = "#E2E8F0"
    text_muted: str = "#94A3B8"
    surface2: str = "#F1F5F9"
    accent2: str = "#10B981"


class Typography(BaseModel):
    heading_font: str = "Calibri"
    body_font: str = "Calibri"
    heading_size_h1: int = 40
    heading_size_h2: int = 28
    heading_size_h3: int = 20
    body_size: int = 14
    caption_size: int = 11
    line_spacing_pct: int = 140


class SpacingTokens(BaseModel):
    margin_top_pct: float = 0.08
    margin_bottom_pct: float = 0.06
    margin_left_pct: float = 0.06
    margin_right_pct: float = 0.06
    gutter_pct: float = 0.03


class ShadowToken(BaseModel):
    blur_pt: int = 8
    dist_pt: int = 4
    angle_deg: int = 45
    color_hex: str = "#00000033"


class DesignTokens(BaseModel):
    name: str
    colors: ColorPalette
    typography: Typography
    spacing: SpacingTokens
    shadow: ShadowToken
    border_radius_pt: int = 6
    use_gradient_background: bool = False
    gradient_angle_deg: int = 135


class ElementEmphasis(BaseModel):
    element_id: str
    emphasis_type: Literal["highlight", "shadow", "border", "bold", "large"]
    color_override: str | None = None


class LayoutAssignment(BaseModel):
    slide_index: int
    layout_type: str
    split_ratio: float = 0.5  # two_column 레이아웃일 때
    primary_zone: str = "left"  # 주요 컨텐츠 위치
    emphasis_elements: list[ElementEmphasis] = Field(default_factory=list)
    accent_color: str | None = None  # 슬라이드별 강조색


class DesignSpec(BaseModel):
    tokens: Optional[DesignTokens] = None  # DesignAgent 호출 후 load_theme()으로 덮어씀
    layout_assignments: list[LayoutAssignment]
    global_accent_color: str  # 전체 덱의 주요 강조색
    use_section_dividers: bool = True
    footer_text: str | None = None
    logo_position: Literal["bottom_left", "bottom_right", "top_right", "none"] = "bottom_right"
