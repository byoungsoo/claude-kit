"""QAAgent: per-slide scoring and revision requests."""
from ..schema.content import SlideContent
from ..schema.design import DesignSpec
from ..schema.qa import QAReport, SlideScore, RevisionRequest
from .base_agent import BaseAgent


_SYSTEM = """당신은 발표 품질 검토 전문가입니다. 다음 기준으로 발표를 평가합니다:

1. 시각적 균형 (1-10): 요소들이 잘 분배되어 있는가? 적절한 여백이 있는가?
   - 9-10: 완벽한 균형, 전문적인 외관
   - 7-8: 사소한 불균형, 여전히 효과적
   - 5-6: 눈에 띄는 불균형으로 집중력 분산
   - 1-4: 심각한 불균형, 재디자인 필요

2. 콘텐츠 명확성 (1-10): 메시지가 명확하고 간결한가?
   - 9-10: 완벽하게 명확, 청중이 즉시 이해
   - 7-8: 사소한 모호함이 있지만 명확
   - 5-6: 불명확, 청중이 혼란스러울 수 있음
   - 1-4: 혼란스러움, 재작성 필요

3. 일관성 (1-10): 이 슬라이드가 덱의 시각적/콘텐츠 스타일에 맞는가?
   - 9-10: 완벽히 일관됨
   - 7-8: 사소한 불일치
   - 5-6: 덱 스타일과 눈에 띄게 다름
   - 1-4: 완전히 불일치

종합 = (시각적_균형 × 0.35 + 콘텐츠_명확성 × 0.45 + 일관성 × 0.20)

종합 점수 7.0 미만 슬라이드는 구체적이고 실행 가능한 개선 제안과 함께 수정 요청으로 표시하세요."""


class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__(_SYSTEM)

    def review(
        self,
        slides: list[SlideContent],
        design_spec: DesignSpec,
    ) -> QAReport:
        slides_detail = "\n\n".join(
            f"=== Slide {s.index + 1} ({s.slide_type}) ===\n"
            f"Heading: {s.heading}\n"
            f"Subheading: {s.subheading or 'none'}\n"
            f"Body blocks: {len(s.body_blocks)} block(s)\n"
            f"Has chart: {s.chart is not None}\n"
            f"Has diagram: {s.diagram is not None}\n"
            f"Has table: {s.table is not None}\n"
            f"Background: {s.background_variant}\n"
            f"Layout assigned: {self._get_layout_type(s.index, design_spec)}"
            for s in slides
        )

        prompt = f"""{len(slides)}장 발표를 검토하세요:

{slides_detail}

디자인 테마: {design_spec.tokens.name}
전체 액센트 색상: {design_spec.global_accent_color}

모든 슬라이드(인덱스 0~{len(slides)-1})에 점수를 매기세요.
종합 점수 7.0 미만 슬라이드는 구체적이고 실행 가능한 개선 제안이 포함된 수정 요청을 작성하세요.
overall_deck_score는 모든 슬라이드의 가중 평균으로 설정하세요.
덱 전체 품질에 대한 2~3문장 요약을 작성하세요. (한국어로)"""

        report = self.call_structured(prompt, QAReport, max_tokens=6000)

        # Ensure overall scores are computed correctly
        for score in report.scores:
            score.overall = round(
                score.visual_balance * 0.35
                + score.content_clarity * 0.45
                + score.consistency * 0.20,
                1
            )

        report.overall_deck_score = round(
            sum(s.overall for s in report.scores) / max(len(report.scores), 1), 1
        )

        return report

    def _get_layout_type(self, index: int, spec: DesignSpec) -> str:
        for la in spec.layout_assignments:
            if la.slide_index == index:
                return la.layout_type
        return "default"
