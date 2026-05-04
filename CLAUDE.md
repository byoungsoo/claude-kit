# Claude Kit

Claude Code에서 사용하는 커스텀 kit·스킬·에이전트·설정을 관리하는 리포지토리.

## 컨셉

Claude Code 자체가 AI 역할을 수행. Python은 PPTX 조립 등 순수 렌더링만 담당.
별도 API 키 불필요 — Claude Code 세션이 곧 AI 엔진.

## 목적

git clone 후 `./deploy.sh <kit-name> global` 한 번으로 어느 PC에서든 동일한 Claude Code 환경을 구성.
- kit 단위로 독립 관리 — 여러 kit를 같은 대상에 배포해도 충돌 없음
- kit명 prefix로 `~/.claude/` 내 파일 구분 (예: `ppt-generator-ppt-research`)
- 절대경로 없음 — `__KIT_ROOT__` placeholder를 deploy.sh가 실제 경로로 치환

---

## 리포지토리 구조

```
claude-kit/
├── CLAUDE.md              ← 이 파일 (200줄 이하 유지)
├── README.md              ← 전체 구조·설치·배포·사용법 가이드
├── settings.json          ← Claude Code 권한 설정
├── deploy.sh              ← 배포 스크립트 (kit 단위, prefix 적용)
│
└── <kit-name>/            ← 독립된 kit 디렉토리
    ├── skills/            ← 오케스트레이터 스킬 (SKILL.md + 렌더러)
    ├── agents/            ← Claude 서브에이전트 (각 역할별 .md)
    └── rules/             ← 조건부 로드 지침
```

---

## 배포 방법

```bash
./deploy.sh <kit-name> global                     # ~/.claude/ 에 배포
./deploy.sh <kit-name> project /path/to/project   # 프로젝트별 배포
./deploy.sh <kit-name> remove global              # 배포 제거
```

---

## Kit 목록

| Kit | 호출 | 상세 |
|-----|------|------|
| `ppt-generator` | `/ppt-generator-ppt` 또는 자연어 | `ppt-generator/rules/ppt-detail.md` 참조 |

## 새 Kit 추가 방법

1. `<kit-name>/` 에 `skills/`, `agents/`, `rules/` 작성
2. `SKILL.md`에 `description` frontmatter 추가 (자연어 자동 호출용)
3. 서브에이전트는 `agents/<name>.md`에 역할·도구·출력 형식 정의
4. `./deploy.sh <kit-name> global` 실행
