"""ResearchAgent: gather facts, statistics, and narrative context."""
import httpx
from ..schema.research import ResearchBundle
from .base_agent import BaseAgent


_SYSTEM_PROMPT = """당신은 전문 리서치 애널리스트입니다. 발표 주제를 깊이 분석하여 다음을 추출하는 것이 임무입니다:
1. 높은 신뢰도를 가진 핵심 사실 주장 (데이터/연구에 근거한)
2. 임팩트 있는 통계 수치와 데이터 포인트
3. 시각화 제안 (차트, 다이어그램)
4. 처음 30초 안에 청중을 사로잡을 내러티브 훅
5. 발표 전체를 관통할 핵심 테마

구체적인 숫자를 사용하세요. 막연한 표현보다 구체적인 데이터를 우선시하세요.
URL이 제공된 경우, 해당 출처에서 정보를 추출하세요.
청중이 이미 알고 있는 것과 놀라울 만한 것을 항상 구분하세요.
분석 결과를 구조화된 ResearchBundle로 반환하세요."""


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(_SYSTEM_PROMPT)

    def research(
        self,
        topic: str,
        audience: str = "general professionals",
        urls: list[str] | None = None,
        extra_context: str | None = None,
    ) -> ResearchBundle:
        url_content = ""
        if urls:
            url_content = self._fetch_urls(urls)

        prompt = f"""주제: {topic}
대상 청중: {audience}

{f'추가 컨텍스트: {extra_context}' if extra_context else ''}
{f'참고 자료 (제공된 URL에서 추출):\n{url_content}' if url_content else ''}

이 주제를 철저히 조사하여 다음을 포함한 ResearchBundle을 반환하세요:
- 신뢰도 점수가 포함된 핵심 주장 최소 5개
- 차트와 다이어그램이 혼합된 시각화 제안 최소 3개
- 임팩트 있는 내러티브 훅 1개
- 핵심 테마 3~5개
- 청중의 기존 지식에 대한 가정
모든 내용은 한국어로 작성하세요."""

        return self.call_structured(prompt, ResearchBundle, max_tokens=6000)

    def _fetch_urls(self, urls: list[str]) -> str:
        content_parts = []
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            for url in urls[:5]:  # max 5 URLs
                try:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        text = resp.text[:8000]  # truncate
                        content_parts.append(f"--- {url} ---\n{text}\n")
                except Exception:
                    content_parts.append(f"--- {url} --- (fetch failed)\n")
        return "\n".join(content_parts)
