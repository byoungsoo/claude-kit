# PPT Generation Skill

Claude Code에서 `/ppt` 명령으로 호출하는 한국어 고품질 PPTX 자동 생성 스킬입니다.

단순한 슬라이드 변환이 아닌 **멀티 에이전트 파이프라인**으로 리서치 → 내러티브 설계 → 슬라이드 작성 → 디자인 → QA까지 전 과정을 자동화합니다.

> 이 README는 `skills/ppt/` 디렉토리 단독 설명입니다.
> 리포지토리 전체 구조·설치·배포는 **루트 README.md** 를 참고하세요.

---

## 빠른 시작

### 1. 의존성 설치

```bash
# skills/ppt/ 디렉토리에서 실행
pip3 install -r requirements.txt --break-system-packages
```

### 2. API 키 설정

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. 실행

```bash
python3 -m src.ppt_generator.cli.main generate "<주제>" [옵션]
```

---

## 디렉토리 구조

```
skills/ppt/
├── README.md                   ← 이 파일
├── SKILL.md                    ← Claude에게 전달하는 실행 지침 (생성 + 편집 모드)
├── pyproject.toml
├── requirements.txt
│
├── src/ppt_generator/          ← 파이프라인 소스
│   ├── agents/                 ← 5개 전문 에이전트
│   │   ├── base_agent.py       ← Anthropic 클라이언트 래퍼 (retry, token 카운팅)
│   │   ├── research_agent.py   ← 주제 리서치, 통계·시각화 수집
│   │   ├── outline_agent.py    ← 확장 사고로 내러티브 구조 설계
│   │   ├── content_agent.py    ← 슬라이드별 개별 콘텐츠 생성 + 크리틱
│   │   ├── design_agent.py     ← 레이아웃·타이포·강조 설계
│   │   └── qa_agent.py         ← 품질 점수화 및 자동 재생성
│   │
│   ├── graph/                  ← LangGraph 파이프라인
│   │   ├── state.py            ← PipelineState (전체 공유 상태)
│   │   ├── nodes.py            ← 각 노드 함수
│   │   ├── conditions.py       ← 조건부 라우팅 (QA 점수 기반)
│   │   └── graph.py            ← StateGraph 정의 + run_pipeline()
│   │
│   ├── rendering/              ← PPTX 렌더러
│   │   ├── oxml_effects.py     ← 그라디언트·그림자·글로우 OXML 직접 제어
│   │   ├── text_render.py      ← 줄간격·자간 OXML 제어
│   │   ├── chart_render.py     ← plotly / matplotlib → PNG
│   │   ├── diagram_render.py   ← Mermaid → PNG (mmdc CLI 또는 matplotlib fallback)
│   │   └── renderer.py         ← SlideRenderer, LayoutGrid (% → EMU)
│   │
│   ├── schema/                 ← Pydantic 데이터 계약
│   │   ├── research.py         ← ResearchBundle
│   │   ├── outline.py          ← DeckOutline, SlideStub, NarrativeArc
│   │   ├── content.py          ← SlideContent, ChartSpec, DiagramSpec
│   │   ├── design.py           ← DesignSpec, DesignTokens, ColorPalette
│   │   └── qa.py               ← QAReport, SlideScore, RevisionRequest
│   │
│   └── cli/
│       └── main.py             ← typer CLI 진입점
│
├── themes/                     ← 디자인 테마 (JSON)
│   ├── corporate_navy.json     ← 네이비/오렌지, 기업용
│   ├── startup_bold.json       ← 퍼플/핑크, 스타트업용
│   ├── dark_tech.json          ← 다크모드, 기술 발표용
│   └── academic_clean.json     ← 화이트/네이비, 학술용
│
├── prompts/                    ← 에이전트별 한국어 시스템 프롬프트 (문서용)
│   ├── research_system.md
│   ├── outline_system.md
│   ├── content_system.md
│   ├── design_system.md
│   └── qa_system.md
│
└── scripts/                    ← PPTX 편집 유틸리티
    ├── thumbnail.py            ← PPTX → 슬라이드 썸네일 그리드 (QA용)
    ├── add_slide.py            ← 슬라이드 복제/레이아웃으로 추가
    ├── clean.py                ← 언팩 디렉토리 고아 파일 정리
    └── office/
        ├── unpack.py           ← PPTX → XML 디렉토리
        ├── pack.py             ← XML 디렉토리 → PPTX
        └── soffice.py          ← LibreOffice 헬퍼 (PDF/썸네일 변환)
```

---

## 파이프라인 상세

### 생성 모드 흐름

```
사용자 입력 (주제, 옵션)
        │
        ▼
  ResearchAgent ──── 주제 관련 사실, 통계, 시각화 제안 수집
        │
        ▼
  OutlineAgent ───── 확장 사고(extended thinking)로 내러티브 호 설계
        │             슬라이드 목적·핵심 메시지·유형 결정
        ▼
  ContentAgent ───── 슬라이드별 개별 Claude 호출 (풀 컨텍스트 유지)
        │             차트 데이터, Mermaid 다이어그램, 발표자 노트 포함
        ▼
  CriticAgent ─────  슬라이드 간 중복·흐름 단절·근거 부재 검토
        │
        ▼
  DesignAgent ─────  레이아웃 유형, 분할 비율, 강조 요소, 액센트 색상 배정
        │
        ▼
  Renderer ────────  python-pptx + lxml OXML 직접 제어로 PPTX 조립
        │             plotly 차트, Mermaid 다이어그램 렌더링 포함
        ▼
  QAAgent ─────────  슬라이드별 1~10점 채점 (시각 균형·명확성·일관성)
        │             점수 7 미만 슬라이드 → 재생성 요청 (최대 2회)
        ▼
  output.pptx
```

### 에이전트별 역할

| 에이전트 | 출력 스키마 | 주요 특징 |
|----------|-------------|-----------|
| ResearchAgent | `ResearchBundle` | 신뢰도 점수 포함 주장, 시각화 제안, 내러티브 훅 |
| OutlineAgent | `DeckOutline` | extended thinking으로 NarrativeArc 설계 |
| ContentAgent | `SlideContent` × N | 슬라이드당 1회 호출, 3~5문장 발표자 노트 |
| DesignAgent | `DesignSpec` | instructor로 구조화 출력 강제, 테마 토큰 로드 |
| QAAgent | `QAReport` | 종합 = 시각균형×0.35 + 명확성×0.45 + 일관성×0.20 |

---

## CLI 옵션

```bash
python3 -m src.ppt_generator.cli.main generate "<주제>" [옵션]
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--slides N` | `12` | 슬라이드 수 |
| `--theme <이름>` | `corporate_navy` | 디자인 테마 |
| `--audience "<청중>"` | `"일반 전문가"` | 대상 청중 |
| `--tone <톤>` | `professional` | professional / casual / academic / inspiring |
| `--output <경로>` | `./output.pptx` | 출력 파일 경로 |
| `--url "<URL>"` | — | 참고 URL (여러 번 반복 가능) |
| `--duration N` | `20` | 발표 시간(분) |

```bash
# 테마 목록 확인
python3 -m src.ppt_generator.cli.main themes
```

---

## 테마

| 테마 이름 | 주 색상 | 용도 |
|-----------|---------|------|
| `corporate_navy` | 네이비 `#1E3A5F` + 오렌지 `#F4A261` | 기업 발표, 보고서 |
| `startup_bold` | 퍼플 `#7C3AED` + 핑크 `#EC4899` | 스타트업 피치, 제품 소개 |
| `dark_tech` | 다크 `#0F172A` + 블루 `#60A5FA` | 기술 컨퍼런스, 개발자 발표 |
| `academic_clean` | 화이트 + 네이비 `#1A365D` + 레드 `#C53030` | 학술 발표, 논문 |

새 테마 추가: `themes/` 폴더에 JSON 파일 추가 후 바로 `--theme <파일명>` 으로 사용 가능.

---

## 의존성

| 패키지 | 용도 |
|--------|------|
| `anthropic` | Claude API 클라이언트 |
| `instructor` | Pydantic 구조화 출력 강제 |
| `langgraph` | 멀티 에이전트 상태 그래프 |
| `python-pptx` | PPTX 생성 |
| `lxml` | OXML 직접 제어 (그라디언트·그림자 등) |
| `plotly` + `kaleido` | 차트 → PNG 렌더링 |
| `matplotlib` | 차트/다이어그램 fallback 렌더링 |
| `pydantic` | 데이터 스키마 검증 |
| `httpx` | ResearchAgent URL 패치 |
| `typer` + `rich` | CLI |

> **다이어그램 렌더링 품질 향상 (선택):**
> `npm install -g @mermaid-js/mermaid-cli` 설치 시 Mermaid 다이어그램이 고품질 PNG로 렌더링됩니다.
> 미설치 시 matplotlib 기반 flowchart renderer가 자동으로 사용됩니다.
