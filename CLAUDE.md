# Claude Kit

Claude Code에서 사용하는 커스텀 kit·스킬·에이전트·설정을 관리하는 리포지토리.


## 목적
claude code 를 회사 PC, 개인 PC 등 어려 곳에서 사용하는데 git으로 skill, agents 등을 기능단위 kit로 묶어서 관리하고 PC마다 동일하게 가져다 사용할 수 있도록 하는 것이 최종 목적임. 

git clone 후 `./deploy.sh <kit-name> add global` 또는 `./deploy.sh <kit-name> add project project/path`한 번으로 어느 PC에서든 동일한 Claude Code 환경을 구성.
- kit 단위로 독립 관리 — 여러 kit를 같은 대상에 배포해도 충돌 없음
- kit명 prefix로 `~/.claude/` 내 파일 구분 (예: `ppt-generator-research`)
- **kit 내부 파일명에 kit명을 반복하지 않는다** — prefix는 deploy.sh만 붙인다 (`rules/conventions.md` → `terraform-generator-conventions.md`)
- 스킬 디렉토리는 kit명과 동일하게 — 이미 kit명으로 시작하는 이름에는 prefix를 덧붙이지 않으므로 호출명이 `/<kit-name>` 이 된다
- 절대경로 없음 — `__PROJECT_ROOT__` placeholder를 deploy.sh가 실제 경로로 치환
- prefix 하드코딩 없음 — kit 파일이 배포된 자기 자신을 참조할 때는 `__KIT_NAME__` placeholder 사용 (deploy.sh가 kit 디렉토리명으로 치환)
- 배포 후 deploy.sh가 참조 경로 존재 여부를 검증 — 깨진 참조가 있으면 실패로 보고
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
└── <kit-name>/                 ← 독립된 kit 디렉토리 (예: terraform-generator)
    ├── skills/
    │   └── <kit-name>/         ← 스킬 디렉토리명 = kit명 → 호출은 /<kit-name>
    │       └── SKILL.md
    ├── agents/                 ← 역할명만 사용 (architect.md, qa.md …)
    └── rules/                  ← 역할명만 사용 (conventions.md, detail.md …)
```

배포 시 `agents/`·`rules/` 파일명 앞에 `<kit-name>-` 이 붙습니다.
`skills/<kit-name>/` 처럼 이미 kit명으로 시작하는 이름은 그대로 유지됩니다.

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

| Kit | 호출 | scope | 상세 |
|-----|------|-------|------|
| `ppt-generator` | `/ppt-generator` 또는 자연어 | both | `ppt-generator/rules/detail.md` 참조 |
| `resume-generator` | `/resume-generator` 또는 자연어 | project | 채용공고 기반 이력서 작성 파이프라인 |
| `drawio-generator` | `/drawio-generator` 또는 자연어 | both | AWS 아키텍처·시스템 구성도 draw.io 자동 생성 |
| `terraform-generator` | `/terraform-generator` 또는 자연어 | both | Terraform 코드 작성·수정 |

## 새 Kit 추가 방법

1. `<kit-name>/skills/<kit-name>/SKILL.md` 작성 — 스킬 디렉토리명은 kit명과 동일하게
2. `SKILL.md` frontmatter에 `description`(필수), `deploy-scope`(선택) 추가
3. `agents/`·`rules/` 파일명은 **역할명만** 사용 — kit명을 반복하지 않는다
   - ✗ `rules/terraform-conventions.md` → ✓ `rules/conventions.md`
4. 배포된 자기 kit의 파일을 참조할 때는 prefix를 직접 쓰지 말고 `__KIT_NAME__` 사용
   - 예: `__PROJECT_ROOT__/.claude/rules/__KIT_NAME__-conventions.md`, `@__KIT_NAME__-architect`
   - 스킬 자신의 asset은 `__PROJECT_ROOT__/.claude/skills/__KIT_NAME__/assets/...`
5. 서브에이전트는 `agents/<role>.md`에 역할·도구·출력 형식 정의 (frontmatter `name: __KIT_NAME__-<role>`)
6. `./deploy.sh <kit-name> add global` 또는 `add project /path` 실행 — 참조 경로 검증까지 통과해야 정상
