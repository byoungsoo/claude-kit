"""ContentAgent: per-slide content generation + ContentCriticAgent."""
from ..schema.research import ResearchBundle
from ..schema.outline import DeckOutline, SlideStub
from ..schema.content import SlideContent, TextBlock, TextRun
from .base_agent import BaseAgent


_CONTENT_SYSTEM = """당신은 세계 수준의 발표 콘텐츠 작가입니다. 다음 원칙으로 슬라이드를 작성합니다:
1. 5초 안에 스캔 가능 (헤드라인이 핵심을 담당)
2. 필요한 최소한의 단어만 사용 — 절대 내용을 늘리지 않음
3. 발표자 노트는 상세하고 구어체로 작성 (각 3~5문장)
   — 슬라이드에 있는 내용뿐만 아니라 실제로 할 말을 포함
4. 슬라이드 유형에 맞게 텍스트와 비주얼 요소의 균형 조절
5. 구체적인 예시와 숫자 사용, 막연한 주장 금지
6. 각 불릿 포인트에 하나의 아이디어만 (불릿당 최대 15자)

차트의 경우: 핵심 메시지를 뒷받침하는 실제적이고 현실적인 데이터 제공
다이어그램의 경우: 핵심 관계를 전달하는 깔끔한 Mermaid 문법 사용
표의 경우: 최대 6열, 최대 8행

발표자 노트 형식: "시작할 때는... 그 다음 설명할 것은... 강조할 점은... 마무리로..."
모든 슬라이드 텍스트와 발표자 노트는 한국어로 작성하세요.
"""

_CRITIC_SYSTEM = """당신은 냉철한 발표 편집자입니다. 슬라이드 콘텐츠를 다음 기준으로 검토합니다:
1. 중복성: 여러 슬라이드가 같은 말을 하고 있지 않은가?
2. 주장-근거 공백: 뒷받침 데이터 없이 주장이 있지 않은가?
3. 흐름 단절: 순서가 어색하게 느껴지지 않는가?
4. 과부하 슬라이드: 한 슬라이드에 너무 많은 내용이 있지 않은가?
5. 약한 오프닝/클로징: 임팩트 있게 시작하고 끝나는가?

피드백은 구체적으로 작성하고 슬라이드 인덱스를 참조하세요."""


class ContentAgent(BaseAgent):
    def __init__(self):
        super().__init__(_CONTENT_SYSTEM)

    def write_slide(
        self,
        stub: SlideStub,
        research: ResearchBundle,
        outline: DeckOutline,
        adjacent_slides: list[SlideStub] | None = None,
        revision_context: str = "",
    ) -> SlideContent:
        context = f"""덱 제목: {outline.title}
내러티브 흐름: {outline.narrative_arc.opening_hook} → ... → {outline.narrative_arc.closing_impact}
전체 슬라이드 수: {outline.total_slides}

현재 슬라이드 (#{stub.index + 1}):
- 유형: {stub.slide_type}
- 목적: {stub.purpose}
- 핵심 메시지: {stub.key_message}
- 내용 힌트: {chr(10).join(f'  • {h}' for h in stub.content_hints)}
- 차트 필요: {stub.has_chart}
- 다이어그램 필요: {stub.has_diagram}
- 표 필요: {stub.has_table}

인접 슬라이드:
{self._format_adjacent(adjacent_slides)}

활용 가능한 리서치 주장:
{chr(10).join(f'• {c.claim}' for c in research.key_claims[:6])}"""

        revision_section = f"\n\n⚠️ 수정 지침 (이전 버전의 문제점){revision_context}" if revision_context else ""

        prompt = f"""{context}{revision_section}

이 슬라이드의 전체 SlideContent를 작성하세요. 요구사항:
- heading: 임팩트 있게, 최대 15자, 핵심 메시지를 담을 것
- subheading: 선택적 보조 컨텍스트 (최대 30자)
- body_blocks: 스캔 가능한 콘텐츠 (불릿, 짧은 단락)
- chart/diagram/table: has_chart/has_diagram/has_table이 True이면 반드시 포함
- speaker_notes: 3~5문장, 구어체, 실제로 할 말과 강조 포인트 포함
- background_variant: 슬라이드 목적에 맞게 선택 (title/closing → accent, section → dark, 데이터 → default)

Mermaid 다이어그램: 단순하고 깔끔한 문법 사용. flowchart LR 또는 TD 선호.
모든 텍스트 내용은 한국어로 작성하세요."""

        return self.call_structured(prompt, SlideContent, max_tokens=5000)

    def _format_adjacent(self, slides: list[SlideStub] | None) -> str:
        if not slides:
            return "  (none)"
        return "\n".join(f"  #{s.index + 1} ({s.slide_type}): {s.key_message}" for s in slides)


class ContentCriticAgent(BaseAgent):
    def __init__(self):
        super().__init__(_CRITIC_SYSTEM)

    def critique(
        self,
        slides: list[SlideContent],
        outline: DeckOutline,
    ) -> list[dict]:
        slides_summary = "\n".join(
            f"Slide {s.index + 1} ({s.slide_type}): '{s.heading}' — "
            f"body_blocks={len(s.body_blocks)}, "
            f"chart={'yes' if s.chart else 'no'}, "
            f"diagram={'yes' if s.diagram else 'no'}"
            for s in slides
        )

        prompt = f""""{outline.title}" 덱의 슬라이드 {len(slides)}장을 검토하세요:

{slides_summary}

내러티브 흐름: {outline.narrative_arc.opening_hook} → {outline.narrative_arc.closing_impact}

문제점을 JSON 리스트로 식별하세요. 각 항목 형식:
{{"slide_index": int, "severity": "low|medium|high", "issue": "문제 설명", "suggestion": "개선 제안"}}

JSON 리스트만 반환하세요. 문제가 없으면 [] 반환."""

        raw = self.call_raw(prompt, max_tokens=2000)

        import json
        try:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        return []
