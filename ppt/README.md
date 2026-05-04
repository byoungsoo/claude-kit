# PPT Generation Skill

Claude Code에서 `/ppt` 명령으로 호출하는 한국어 고품질 PPTX 자동 생성 스킬입니다.

단순한 슬라이드 변환이 아닌 **멀티 에이전트 파이프라인**으로 리서치 → 내러티브 설계 → 슬라이드 작성 → 디자인 → QA까지 전 과정을 자동화합니다.

---

## 빠른 시작

### 1. 의존성 설치

```bash
cd /Users/bys/workspace/code_repo/gitlab/claude-skills/ppt
python3 -m pip install -r requirements.txt --break-system-packages
```

### 2. API 키 설정

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Claude Code에서 사용

```
/ppt "생성형 AI가 금융 산업에 미치는 영향"
/ppt "쿠버네티스 보안 모범 사례" --slides 15 --theme dark_tech
/ppt "스타트업 투자 유치 전략" --theme startup_bold --audience "초기 창업자"
```

---

## 디렉토리 구조

```
ppt/
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
│   │   ├── diagram_render.py   ← Mermaid → PNG (mmdc CLI)
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
        │             URL 제공 시 해당 자료도 파싱
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

## PPTX 편집 모드

기존 PPTX를 수정할 때는 XML 직접 편집 방식을 사용합니다.

```bash
cd scripts/

# 1. 현황 파악 (썸네일 그리드)
python3 thumbnail.py input.pptx thumbnails --cols 4

# 2. 언팩
python3 office/unpack.py input.pptx unpacked/

# 3. 슬라이드 추가
python3 add_slide.py unpacked/ slide2.xml          # 기존 슬라이드 복제
python3 add_slide.py unpacked/ slideLayout3.xml    # 레이아웃으로 신규 생성
# → 출력된 <p:sldId> 를 unpacked/ppt/presentation.xml 의 <p:sldIdLst> 에 추가

# 4. XML 직접 편집 (Edit 도구 사용)
# unpacked/ppt/slides/slide1.xml 등 수정

# 5. 정리
python3 clean.py unpacked/

# 6. 리팩
python3 office/pack.py unpacked/ output.pptx

# 7. QA 확인
python3 thumbnail.py output.pptx qa_result --cols 4
```

---

## Claude Code 연동

이 스킬은 `~/.claude/commands/ppt.md` 또는 프로젝트 `.claude/commands/ppt.md`에 등록하여 사용합니다.

```markdown
# .claude/commands/ppt.md 예시
cd /Users/bys/workspace/code_repo/gitlab/claude-skills/ppt && \
python3 -m src.ppt_generator.cli.main generate $ARGUMENTS
```

등록 후 Claude Code에서 `/ppt` 명령으로 즉시 호출 가능합니다.

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
| `matplotlib` | 차트 fallback 렌더링 |
| `pydantic` | 데이터 스키마 검증 |
| `httpx` | ResearchAgent URL 패치 |
| `typer` + `rich` | CLI |
