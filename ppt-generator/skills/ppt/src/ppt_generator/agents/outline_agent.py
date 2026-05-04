"""OutlineAgent: narrative structure with extended thinking."""
from ..schema.research import ResearchBundle
from ..schema.outline import DeckOutline
from .base_agent import BaseAgent


_SYSTEM_PROMPT = """당신은 내러티브 구조와 설득적 커뮤니케이션 전문가인 마스터 발표 전략가입니다.

당신의 역할은 다음을 갖춘 발표 목차를 만드는 것입니다:
1. 단순 주제 나열이 아닌 compelling한 내러티브 호 흐름
2. 각 슬라이드의 명확한 목적(PURPOSE)과 핵심 메시지(KEY MESSAGE)
3. 청중을 이끄는 슬라이드 간 논리적 전환
4. 시각적 다양성을 위한 콘텐츠 유형 균형 (텍스트, 차트, 다이어그램)
5. 임팩트 있는 오프닝과 기억에 남는 클로징

반드시 적용할 내러티브 원칙:
- 문제-심화-해결(PAS): 해결책을 제시하기 전에 문제를 먼저 확립
- 3의 법칙: 가능하면 아이디어를 3개씩 묶기
- 피라미드 원칙: 결론을 먼저, 근거는 그 다음
- 모든 슬라이드는 존재 이유가 있어야 함 — 내러티브를 전진시키지 않으면 제거

슬라이드 유형 가이드:
- title: 덱 오프닝 (1장)
- section: 주요 섹션 구분 (흐름에 여유 제공)
- content_text: 순수 텍스트, 최대 2장
- content_chart: 데이터 기반 인사이트
- content_diagram: 프로세스/아키텍처/관계도
- two_column: 비교 또는 텍스트+비주얼 조합
- three_column: 3개의 병렬 개념
- full_width_chart: 데이터 자체가 메시지일 때
- data_story: 큰 수치 + 보조 비주얼 + 내러티브
- comparison_table: 구조화된 비교
- quote: 임팩트 있는 인용구 또는 증언
- closing: 행동 촉구 + 연락처 (1장)

모든 텍스트 내용은 한국어로 작성하세요."""


class OutlineAgent(BaseAgent):
    def __init__(self):
        super().__init__(_SYSTEM_PROMPT)

    def create_outline(
        self,
        topic: str,
        research: ResearchBundle,
        slide_count: int = 12,
        audience: str = "general professionals",
        tone: str = "professional",
        duration_minutes: int = 20,
    ) -> DeckOutline:
        research_summary = f"""리서치 요약:
- 주제 요약: {research.topic_summary}
- 내러티브 훅: {research.narrative_hook}
- 핵심 테마: {', '.join(research.key_themes)}
- 핵심 주장: {chr(10).join(f'  • {c.claim} (신뢰도: {c.confidence:.0%})' for c in research.key_claims[:7])}
- 시각화 제안: {chr(10).join(f'  • {v.type}: {v.title}' for v in research.suggested_visualizations)}
- 청중 가정: {research.audience_assumptions}"""

        prompt = f"""다음 조건으로 발표 목차를 작성하세요:

주제: {topic}
목표 슬라이드 수: {slide_count}
대상 청중: {audience}
톤: {tone}
발표 시간: {duration_minutes}분

{research_summary}

compelling한 NarrativeArc를 갖춘 DeckOutline을 설계하세요. 각 SlideStub은 반드시:
- 명확한 목적 (이 슬라이드가 왜 존재하는가?)
- 단 하나의 핵심 메시지 (청중이 무엇을 가져가는가?)
- 콘텐츠 작성자를 위한 내용 힌트
- 콘텐츠에 맞는 슬라이드 유형
- has_chart, has_diagram, has_table 플래그

리서치 결과를 자연스럽게 통합하세요. 오프닝에 내러티브 훅을 활용하세요.
데이터 중심 슬라이드와 개념/내러티브 슬라이드의 균형을 맞추세요.
모든 텍스트는 한국어로 작성하세요."""

        try:
            return self.call_with_thinking(prompt, DeckOutline,
                                            thinking_budget=5000,
                                            max_tokens=12000)
        except Exception:
            # Fallback without extended thinking if beta not available
            return self.call_structured(prompt, DeckOutline, max_tokens=10000)
