# Claude Kit

Claude Code에서 사용하는 커스텀 kit·스킬·에이전트·설정을 관리하는 리포지토리.


## 목적
claude code 를 회사 PC, 개인 PC 등 어려 곳에서 사용하는데 git으로 skill, agents 등을 기능단위 kit로 묶어서 관리하고 PC마다 동일하게 가져다 사용할 수 있도록 하는 것이 최종 목적임. 

git clone 후 `./deploy.sh <kit-name> add global` 또는 `./deploy.sh <kit-name> add project project/path`한 번으로 어느 PC에서든 동일한 Claude Code 환경을 구성.
- kit 단위로 독립 관리 — 여러 kit를 같은 대상에 배포해도 충돌 없음
- kit명 prefix로 `~/.claude/` 내 파일 구분 (예: `ppt-generator-ppt-research`)
- 절대경로 없음 — `__PROJECT_ROOT__` placeholder를 deploy.sh가 실제 경로로 치환
- `deploy-scope: global | project | both` — SKILL.md frontmatter로 배포 범위 제한

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
./deploy.sh <kit-name> add global                     # ~/.claude/ 에 배포 (global kit)
./deploy.sh <kit-name> add project /path/to/project   # 프로젝트별 배포 (project kit, __PROJECT_ROOT__ 치환)
./deploy.sh <kit-name> remove global                  # 배포 제거
./deploy.sh <kit-name> remove project /path/to/project
```

---

## Kit 목록

| Kit | 호출 | 상세 |
|-----|------|------|
| `ppt-generator` | `/ppt-generator-ppt` 또는 자연어 | `ppt-generator/rules/ppt-detail.md` 참조 |
| `resume-manager` | `/resume-manager-resume` 또는 자연어 | 채용공고 기반 이력서 작성 파이프라인 |
| `drawio-generator` | `/drawio-generator-drawio` 또는 자연어 | AWS 아키텍처·시스템 구성도 draw.io 자동 생성 |

## 새 Kit 추가 방법

1. `<kit-name>/` 에 `skills/`, `agents/`, `rules/` 작성
2. `SKILL.md` frontmatter에 `description`(필수), `deploy-scope`(선택) 추가
3. 프로젝트 경로 의존 시 해당 위치에 `__PROJECT_ROOT__` placeholder 사용
4. 서브에이전트는 `agents/<name>.md`에 역할·도구·출력 형식 정의
5. `./deploy.sh <kit-name> add global` 또는 `add project /path` 실행
