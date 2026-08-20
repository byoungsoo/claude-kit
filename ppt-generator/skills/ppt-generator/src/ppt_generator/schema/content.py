from pydantic import BaseModel, Field
from typing import Literal


class TextRun(BaseModel):
    text: str
    bold: bool = False
    italic: bool = False
    size_pt: int | None = None
    color_hex: str | None = None  # None이면 테마 기본값 사용


class TextBlock(BaseModel):
    runs: list[TextRun]
    alignment: Literal["left", "center", "right"] = "left"
    line_spacing_pct: int = 140
    space_before_pt: int = 6


class ChartSeries(BaseModel):
    name: str
    values: list[float]


class ChartSpec(BaseModel):
    engine: Literal["plotly", "matplotlib"] = "plotly"
    chart_type: Literal["bar", "line", "pie", "radar", "scatter", "area", "heatmap"]
    title: str
    categories: list[str]
    series: list[ChartSeries]
    x_label: str | None = None
    y_label: str | None = None
    show_legend: bool = True


class DiagramSpec(BaseModel):
    svg: str | None = None           # SVG XML 문자열 (AI가 직접 작성)
    aws_diagram: str | None = None   # AWS 아키텍처 (draw.io PNG base64, aws-architect 에이전트가 채움)
    caption: str | None = None


class TableCell(BaseModel):
    text: str
    bold: bool = False
    is_header: bool = False


class TableSpec(BaseModel):
    headers: list[str]
    rows: list[list[str]]
    highlight_column: int | None = None  # 강조할 열 인덱스
    caption: str | None = None


class SlideContent(BaseModel):
    index: int
    slide_type: str
    heading: str
    subheading: str | None = None

    # 텍스트 컨텐츠
    body_blocks: list[TextBlock] = Field(default_factory=list)

    # 시각화 컨텐츠 (있는 경우)
    chart: ChartSpec | None = None
    diagram: DiagramSpec | None = None
    table: TableSpec | None = None

    # Layout template — ContentAgent가 직접 지정 (DesignAgent 불필요)
    # 선택지: text_only | viz_only | text_top_viz_bottom |
    #         text_left_viz_right | viz_left_text_right | two_column_text
    layout_template: str | None = None

    # (구) 레이아웃 힌트 — 하위 호환을 위해 유지, 신규 코드는 layout_template 사용
    layout_hint: str | None = None

    # 발표자 노트 (3~5문장, 상세하게)
    speaker_notes: str

    # 배경 색상 힌트
    background_variant: Literal["default", "dark", "accent", "minimal"] = "default"
