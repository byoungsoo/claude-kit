# Claude Kit

Claude Code에서 사용하는 커스텀 kit를 관리하는 리포지토리.

각 kit는 독립적인 디렉토리로 관리되며, `deploy.sh` 한 번으로 어느 PC에서든 동일한 환경을 구성할 수 있습니다.

---

## 컨셉

Claude Code에서 사용하는 **스킬·에이전트를 kit 단위로 관리**하고, `deploy.sh` 한 번으로 어느 PC에서든 동일한 환경을 재현합니다.

```
claude-kit (이 리포지토리)
    ↓ ./deploy.sh <kit> add global | add project /path
~/.claude/ 또는 <project>/.claude/
    ├── skills/   ← 오케스트레이터 (SKILL.md)
    ├── agents/   ← 역할별 서브에이전트
    └── rules/    ← 조건부 로드 지침
```

- **Claude Code가 AI 엔진** — 별도 API 키 불필요, 세션이 곧 실행 환경
- **kit 단위 독립 관리** — 여러 kit를 같은 대상에 배포해도 kit명 prefix로 충돌 없음
- **global / project 배포** — 모든 프로젝트에서 쓸 kit은 global, 특정 프로젝트에 종속된 kit은 project로 배포
- **항상 copy 배포** — 모든 파일을 복사본으로 배포. 소스 수정 후 재배포하면 반영됨
- **`__PROJECT_ROOT__` placeholder** — 배포 시 실제 경로로 자동 치환 (global → `$HOME`, project → 지정 경로)
- **이름 중복 없음** — kit 내부 파일명에 kit명을 반복하지 않고, prefix는 deploy.sh만 붙입니다

---

## 리포지토리 구조

```
claude-kit/
├── README.md              ← 이 파일
├── CLAUDE.md              ← Claude 세션 컨텍스트
├── settings.json          ← Claude Code 권한 설정
├── deploy.sh              ← 배포 스크립트 (kit 단위, prefix 적용)
│
└── <kit-name>/            ← 독립된 kit 디렉토리 (예: ppt-generator, terraform-generator)
    ├── skills/
    │   └── <kit-name>/    ← 오케스트레이터 스킬 (디렉토리명 = kit명 → 호출은 /<kit-name>)
    │       └── SKILL.md   ← 파이프라인 실행 지침 (description, deploy-scope frontmatter)
    ├── agents/            ← Claude 서브에이전트 (역할명만: architect.md, qa.md …)
    └── rules/             ← 조건부 로드 지침 (역할명만: conventions.md, detail.md …)
```

**네이밍 규칙** — kit 내부 파일명에 kit명을 반복하지 않습니다. prefix는 `deploy.sh`가 붙입니다.

| 소스 | 배포본 |
|------|--------|
| `terraform-generator/skills/terraform-generator/` | `skills/terraform-generator/` |
| `terraform-generator/rules/conventions.md` | `rules/terraform-generator-conventions.md` |
| `drawio-generator/agents/architect.md` | `agents/drawio-generator-architect.md` |

---

## Kit 목록

| Kit | 호출 방법 | 배포 범위 | 설명 |
|-----|-----------|-----------|------|
| `ppt-generator` | `/ppt-generator <주제>` 또는 자연어 | both | 주제 → 한국어 PPTX 자동 생성 |
| `resume-generator` | `/resume-generator <공고>` 또는 자연어 | project | 채용공고 → 맞춤 이력서 자동 작성 |
| `drawio-generator` | `/drawio-generator <주제>` 또는 자연어 | both | AWS 아키텍처·시스템 구성도 draw.io 자동 생성 |
| `terraform-generator` | `/terraform-generator <컴포넌트>` 또는 자연어 | both | Terraform 코드 작성·수정 |

각 kit의 상세 사용법은 kit 디렉토리의 README를 참고하세요:
- [ppt-generator/README.md](ppt-generator/README.md)
- [drawio-generator/README.md](drawio-generator/README.md)
- [resume-generator/README.md](resume-generator/README.md)
- [terraform-generator/README.md](terraform-generator/README.md)

---

## 빠른 시작

### 1. Clone

```bash
git clone <repo-url> ~/claude-kit
cd ~/claude-kit
```

### 2. 배포

```bash
# global kit — 모든 프로젝트에서 사용 가능
./deploy.sh ppt-generator add global

# project kit — 특정 프로젝트 경로를 지정해서 배포
./deploy.sh drawio-generator add project /path/to/my-project
```

배포 후 Claude Code를 재시작하면 slash command와 자동 호출이 활성화됩니다.

---

## deploy.sh 상세

kit 단위로 배포하며, 모든 파일에 **kit명을 prefix**로 붙여 여러 kit가 충돌하지 않습니다.
단, 이름이 **이미 kit명으로 시작하면 prefix를 덧붙이지 않습니다** — 그래서 스킬 디렉토리를 kit명과 동일하게 두면 호출명이 `/<kit-name>` 이 됩니다.

### 파일별 처리 방식

모든 파일은 **복사본(copy)**으로 배포됩니다. 복사 시 아래 placeholder가 실제 값으로 치환됩니다.

| placeholder | 치환값 |
|-------------|--------|
| `__PROJECT_ROOT__` | `global` → `$HOME` / `project /path` → `/path` (지정한 절대경로) |
| `__KIT_NAME__` | kit 디렉토리 이름 (배포 파일에 붙는 prefix와 항상 일치) |

kit 파일이 **배포된 자기 자신의 파일**을 참조할 때는 prefix를 직접 쓰지 말고 `__KIT_NAME__` 을 사용하세요. prefix를 하드코딩하면 kit 디렉토리 이름을 바꾸는 순간 모든 참조가 깨집니다.

```markdown
✗ __PROJECT_ROOT__/.claude/rules/terraform-generator-conventions.md
✓ __PROJECT_ROOT__/.claude/rules/__KIT_NAME__-conventions.md
✓ __PROJECT_ROOT__/.claude/skills/__KIT_NAME__/assets/aws4-styles.md
✓ @__KIT_NAME__-architect
```

소스 파일을 수정한 경우 `deploy.sh`를 다시 실행해야 배포본에 반영됩니다.

### 참조 경로 검증

배포 후 `deploy.sh` 가 배포된 `skills/`·`agents/`·`rules/` 파일에서 `<target>/.claude/...` 형태의 경로 참조를 모두 추출해 실제 존재 여부를 확인합니다. 존재하지 않는 참조가 있으면 경고를 출력하고 exit 1 로 종료하므로, 규칙 파일이 조용히 누락된 상태로 스킬이 동작하는 일을 막습니다.

### deploy-scope

SKILL.md frontmatter의 `deploy-scope`로 배포 가능한 모드를 제한합니다.

| 값 | 동작 |
|----|------|
| `global` | `global` 모드만 허용 |
| `project` | `project` 모드만 허용 |
| `both` 또는 미설정 | 제한 없음 |

### 사용법

```bash
# 전역 배포
./deploy.sh <kit-name> add global

# 프로젝트 배포 — __PROJECT_ROOT__ 를 지정 경로로 치환
./deploy.sh <kit-name> add project /path/to/project

# 배포 제거
./deploy.sh <kit-name> remove global
./deploy.sh <kit-name> remove project /path/to/project
```

### 배포 후 생성되는 파일 예시

**`ppt-generator add global` 기준**

```
~/.claude/
├── skills/
│   └── ppt-generator/                 ← 복사본 (호출: /ppt-generator)
├── agents/
│   ├── ppt-generator-research.md      ← 복사본 (소스: agents/research.md)
│   ├── ppt-generator-outline.md
│   ├── ppt-generator-content.md
│   ├── ppt-generator-design.md
│   ├── ppt-generator-qa.md
│   └── ppt-generator-aws-architect.md
└── rules/
    └── ppt-generator-detail.md        ← 복사본 (소스: rules/detail.md)
```

**`drawio-generator add project ~/workspace/myproject` 기준**

```
~/workspace/myproject/.claude/
├── skills/
│   └── drawio-generator/              ← 복사본 (__PROJECT_ROOT__ → ~/workspace/myproject 치환됨)
│       ├── SKILL.md
│       └── assets/
│           └── aws4-styles.md
└── agents/
    ├── drawio-generator-architect.md  ← 복사본 (소스: agents/architect.md)
    ├── drawio-generator-draw.md       ← 복사본
    └── drawio-generator-qa.md         ← 복사본
```

---

## 새 Kit 추가 방법

```
claude-kit/
└── <kit-name>/
    ├── skills/<kit-name>/
    │   └── SKILL.md          ← description frontmatter 필수 (자동 호출용)
    ├── agents/<role>.md      ← 선택: 서브에이전트 정의 (역할명만)
    └── rules/<role>.md       ← 선택: 조건부 로드 지침 (역할명만)
```

1. `<kit-name>/` 디렉토리에 위 구조로 파일 작성 — 스킬 디렉토리명은 **kit명과 동일하게**
2. `SKILL.md` frontmatter에 아래 항목 추가:
   - `description` — 자연어 자동 호출 트리거 문구 (필수)
   - `deploy-scope: global | project | both` — 배포 범위 제한 (선택, 미설정 시 `both`)
3. `agents/`·`rules/` 파일명에 **kit명을 반복하지 않는다** — prefix는 deploy.sh가 붙임
   - ✗ `rules/terraform-conventions.md` → ✓ `rules/conventions.md`
4. 프로젝트 경로에 의존하는 경우 해당 위치에 `__PROJECT_ROOT__` placeholder 사용
5. 배포된 자기 kit 파일을 참조할 때는 `__KIT_NAME__` placeholder 사용 (prefix 하드코딩 금지)
6. `./deploy.sh <kit-name> add global` 또는 `add project /path` 실행 — 참조 경로 검증까지 통과해야 정상

---

## settings.json

Claude Code 권한 설정. 필요에 따라 `~/.claude/settings.json`에 복사해서 사용합니다.

```json
{
  "permissions": {
    "allow": ["Bash(python3:*)", "Bash(pip3:*)", "Bash(npm:*)", "Bash(mmdc:*)", "Read", "Write", "Edit"],
    "deny": []
  }
}
```
