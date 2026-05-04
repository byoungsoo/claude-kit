# Claude Kit

Claude Code에서 사용하는 커스텀 스킬·에이전트·설정을 관리하는 리포지토리.

## 목적

git clone 후 `./deploy.sh global` 한 번으로 어느 PC에서든 동일한 Claude Code 환경을 구성.
- `~/.claude/` 또는 `<project>/.claude/` 로 배포
- 절대경로 없음 — `commands/*.md.template` 의 `__SKILL_ROOT__` 를 deploy.sh가 실제 경로로 치환

---

## 리포지토리 구조

```
claude-kit/
├── CLAUDE.md              ← 이 파일
├── README.md              ← 전체 구조·설치·배포 가이드
├── settings.json          ← Claude Code 권한 설정
├── deploy.sh              ← 배포 스크립트
├── commands/
│   └── ppt.md.template    ← /ppt slash command (__SKILL_ROOT__ placeholder)
├── skills/
│   └── ppt/               ← PPT 자동 생성 스킬 (멀티 에이전트 파이프라인)
└── agents/                ← 향후 커스텀 에이전트 추가 예정
```

---

## 배포 방법

```bash
./deploy.sh global                     # ~/.claude/ 에 배포
./deploy.sh project /path/to/project   # 프로젝트별 배포
./deploy.sh remove global              # 배포 제거
```

---

## skills/ppt 개요

주제를 입력하면 한국어 고품질 PPTX를 자동 생성하는 멀티 에이전트 파이프라인.

**파이프라인 순서:**
```
ResearchAgent → OutlineAgent → ContentAgent → ContentCriticAgent
→ DesignAgent → Renderer → QAAgent (점수 7 미만 슬라이드 자동 재생성)
```

**핵심 기술:**
- LangGraph StateGraph로 파이프라인 오케스트레이션
- `instructor` 라이브러리로 Pydantic 구조화 출력 강제
- OutlineAgent: `extended thinking` (`betas=["interleaved-thinking-2025-05-14"]`) 사용
- PPTX 렌더링: python-pptx + lxml OXML 직접 제어 (그라디언트·그림자)
- 차트: plotly/matplotlib → PNG BytesIO
- 다이어그램: mmdc CLI → 없으면 matplotlib flowchart renderer 자동 fallback

**디자인 테마:** `corporate_navy`, `startup_bold`, `dark_tech`, `academic_clean`

---

## 주요 파일 경로

| 파일 | 역할 |
|------|------|
| `skills/ppt/src/ppt_generator/agents/base_agent.py` | 모든 에이전트의 기반 (Anthropic 클라이언트 래퍼) |
| `skills/ppt/src/ppt_generator/agents/outline_agent.py` | extended thinking 사용 |
| `skills/ppt/src/ppt_generator/agents/content_agent.py` | 슬라이드별 콘텐츠 생성 + revision_context 주입 |
| `skills/ppt/src/ppt_generator/graph/nodes.py` | LangGraph 노드 함수 |
| `skills/ppt/src/ppt_generator/graph/graph.py` | StateGraph 정의 |
| `skills/ppt/src/ppt_generator/rendering/renderer.py` | PPTX 조립 |
| `skills/ppt/src/ppt_generator/rendering/diagram_render.py` | Mermaid → PNG |
| `skills/ppt/src/ppt_generator/schema/` | Pydantic 데이터 계약 |
| `skills/ppt/themes/` | 디자인 토큰 JSON |
| `skills/ppt/SKILL.md` | Claude 실행 지침 (생성 + 편집 모드) |

---

## 완료된 버그 수정 (시뮬레이션 리뷰 기반)

1. **`bg_shape.line.fill.background()` AttributeError** — `renderer.py` 에서 해당 라인 제거
2. **`DesignSpec.tokens` 필수 필드 오류** — `Optional[DesignTokens] = None` 으로 변경 (DesignAgent가 load_theme()으로 덮어쓰므로)
3. **`revision_context` 미전달** — `content_agent.py` 에 파라미터 추가, `nodes.py` revision_node에서 전달
4. **extended thinking + instructor 호환성** — `call_with_thinking()` 에서 instructor 우회, 직접 `client.beta.messages.create` 사용 후 JSON 파싱
5. **mmdc 미설치 시 빈 다이어그램** — `diagram_render.py` 에 matplotlib 기반 flowchart renderer 추가 (Mermaid 문법 파싱 → 노드/엣지 시각화)

---

## 알려진 제약

- `commands/*.md` 파일은 deploy.sh 재실행 시에만 경로가 업데이트됨 (심링크 아닌 복사)
- extended thinking은 `claude-sonnet-4-6` 이상 모델 필요
- mmdc 없을 때 diagram renderer는 단순 flowchart만 지원 (복잡한 Mermaid 문법은 fallback)

---

## 새 스킬 추가 방법

1. `skills/<name>/` 에 코드 작성
2. `commands/<name>.md.template` 작성 (`__SKILL_ROOT__` 사용)
3. `./deploy.sh global` 재실행
