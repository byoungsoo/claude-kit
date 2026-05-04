"""DesignAgent: layout + typography + emphasis map."""
import json
from pathlib import Path
from ..schema.content import SlideContent
from ..schema.outline import DeckOutline
from ..schema.design import DesignSpec, DesignTokens
from .base_agent import BaseAgent


_SYSTEM = """당신은 시각적으로 매력적이고 일관된 슬라이드 덱을 만드는 발표 디자인 전문가입니다.

따르는 디자인 원칙:
- CRAP: 대비(Contrast), 반복(Repetition), 정렬(Alignment), 근접성(Proximity)
- 시각적 위계: 크기, 굵기, 색상으로 시선 유도
- 여백도 디자인 — 모든 픽셀을 채우지 않음
- 슬라이드당 하나의 초점
- 전체적인 일관된 그리드 정렬

담당 역할:
1. 각 슬라이드에 올바른 레이아웃 유형 배정
2. 핵심 요소에 강조 설정
3. 의미를 강화하는 액센트 색상 선택 (단순 장식 아님)
4. 일관성을 유지하면서 시각적 다양성 확보

사용 가능한 레이아웃 유형:
- title, section, content_text, content_chart, content_diagram,
  two_column (split_ratio 0.4-0.6), three_column, full_width_chart,
  data_story, comparison_table, quote, closing

모든 슬라이드 인덱스에 대한 layout_assignments를 포함한 DesignSpec을 반환하세요."""


THEMES_DIR = Path(__file__).parent.parent.parent.parent / "themes"


def load_theme(theme_name: str) -> DesignTokens:
    theme_path = THEMES_DIR / f"{theme_name}.json"
    if not theme_path.exists():
        theme_path = THEMES_DIR / "corporate_navy.json"
    data = json.loads(theme_path.read_text())
    return DesignTokens(**data)


class DesignAgent(BaseAgent):
    def __init__(self):
        super().__init__(_SYSTEM)

    def design(
        self,
        slides: list[SlideContent],
        outline: DeckOutline,
        theme_name: str = "corporate_navy",
    ) -> DesignSpec:
        tokens = load_theme(theme_name)

        slides_summary = "\n".join(
            f"Slide {s.index}: type={s.slide_type}, heading='{s.heading}', "
            f"has_chart={s.chart is not None}, has_diagram={s.diagram is not None}, "
            f"has_table={s.table is not None}, background={s.background_variant}"
            for s in slides
        )

        prompt = f""""{outline.title}" {len(slides)}장 덱의 레이아웃을 설계하세요.
테마: {theme_name}

슬라이드 목록:
{slides_summary}

각 슬라이드에 대해 배정하세요:
- layout_type: 콘텐츠 유형에 가장 적합한 레이아웃
- split_ratio: two_column 슬라이드의 경우 (0.4~0.6, 0.5가 균등 분할)
- primary_zone: two_column에서 주요 콘텐츠 위치 "left" 또는 "right"
- emphasis_elements: 강조할 요소 ID 목록
- accent_color: 슬라이드별 선택적 액센트 (핵심 슬라이드에만 드물게 사용)

전체 덱 결정:
- global_accent_color: 이 덱에서 가장 중요한 단일 색상
- use_section_dividers: 섹션 슬라이드에 시각적 구분선 사용 여부
- footer_text: 푸터에 표시할 덱 부제목 또는 회사명 (한국어로)
- logo_position: 로고 위치

완전한 DesignSpec을 반환하세요. tokens 필드는 다음 값을 사용하세요:
{json.dumps(tokens.model_dump(), indent=2, default=str)[:1000]}... (abbreviated)
"""

        spec = self.call_structured(prompt, DesignSpec, max_tokens=8000)

        # Override tokens with the loaded theme (don't let Claude modify tokens)
        spec.tokens = tokens
        return spec
