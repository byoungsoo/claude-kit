# ppt-generator 상세 참조

PPT 스킬 작업 시 참조하는 상세 컨텍스트.

---

## 아키텍처

Claude Code 서브에이전트들이 AI 역할을 수행하고, Python은 PPTX 조립만 담당.

```
SKILL.md (오케스트레이터)
    ↓
  @ppt-generator-ppt-research  — 웹 리서치 → research JSON
  @ppt-generator-ppt-outline   — 내러티브 구조 → outline JSON
  @ppt-generator-ppt-content   — 슬라이드 콘텐츠 → slides JSON
  @ppt-generator-ppt-design    — 레이아웃·테마 → design JSON
  @ppt-generator-ppt-qa        — 품질 검토 → 7점 미만 재생성 (최대 2회)
    ↓
  cli/render.py  — slides JSON + design JSON → output.pptx
```

---

## 주요 파일

| 파일 | 역할 |
|------|------|
| `skills/ppt/SKILL.md` | 파이프라인 오케스트레이터 |
| `agents/ppt-research.md` | 리서치 서브에이전트 |
| `agents/ppt-outline.md` | 아웃라인 서브에이전트 |
| `agents/ppt-content.md` | 콘텐츠 서브에이전트 |
| `agents/ppt-design.md` | 디자인 서브에이전트 |
| `agents/ppt-qa.md` | QA 서브에이전트 |
| `skills/ppt/src/ppt_generator/cli/render.py` | JSON → PPTX 렌더러 CLI |
| `skills/ppt/src/ppt_generator/rendering/` | 슬라이드 렌더링 모듈 |
| `skills/ppt/src/ppt_generator/schema/` | Pydantic 데이터 계약 |
| `skills/ppt/themes/` | 디자인 테마 JSON |
| `skills/ppt/scripts/` | PPTX 편집 유틸리티 |

---

## 디자인 테마

| 테마 | 특징 |
|------|------|
| `corporate_navy` | 네이비/오렌지, 기업 발표용 |
| `startup_bold` | 퍼플/핑크, 스타트업용 |
| `dark_tech` | 다크모드 블루/그린, 기술 발표용 |
| `academic_clean` | 화이트/네이비, 학술용 |

---

## 렌더러 의존성

```
python-pptx   — PPTX 조립
lxml          — OXML 직접 제어 (그라디언트·그림자)
plotly/matplotlib — 차트 → PNG
cairosvg      — SVG 렌더링
mmdc (선택)   — Mermaid → PNG (없으면 matplotlib fallback)
```

---

## 알려진 제약

- mmdc 미설치 시 diagram renderer는 단순 flowchart만 지원
- `commands/*.md` 파일은 deploy.sh 재실행 시에만 경로가 업데이트됨 (복사 방식)
