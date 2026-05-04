# Claude Skills

Claude Code에서 사용하는 커스텀 스킬·에이전트·설정을 관리하는 리포지토리입니다.

git clone 후 `deploy.sh` 한 번으로 어느 PC에서든 동일한 환경을 구성할 수 있습니다.

---

## 리포지토리 구조

```
claude/                        ← 이 리포지토리 루트
├── README.md                  ← 이 파일 (전체 구조·설치·배포 가이드)
├── settings.json              ← Claude Code 권한 설정
├── deploy.sh                  ← 배포 스크립트 (경로 치환 + 심링크)
│
├── commands/                  ← Slash command 템플릿
│   └── ppt.md.template        ← /ppt 명령 (__SKILL_ROOT__ placeholder 포함)
│
├── skills/                    ← 각 스킬 디렉토리
│   └── ppt/                   ← PPT 자동 생성 스킬
│       ├── README.md          ← 스킬 상세 설명
│       ├── SKILL.md           ← Claude 실행 지침
│       └── ...
│
└── agents/                    ← 커스텀 에이전트 (추후 추가)
```

---

## 빠른 시작

### 1. Clone

```bash
git clone <repo-url> ~/claude
cd ~/claude
```

> 클론 위치는 자유롭게 지정할 수 있습니다. `deploy.sh`가 실제 경로를 자동으로 감지합니다.

### 2. 스킬 의존성 설치

```bash
# PPT 스킬
pip3 install -r skills/ppt/requirements.txt --break-system-packages

# 다이어그램 고품질 렌더링 (선택)
npm install -g @mermaid-js/mermaid-cli
```

### 3. API 키 설정

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# 영구 적용: ~/.zshrc 또는 ~/.bashrc 에 추가
```

### 4. 배포

```bash
# 전역 배포 (~/.claude/ 에 적용 — 모든 프로젝트에서 사용 가능)
./deploy.sh global

# 특정 프로젝트에만 배포
./deploy.sh project /path/to/my-project
```

배포 후 Claude Code를 재시작하면 slash command가 활성화됩니다.

---

## deploy.sh 상세

### 동작 방식

`deploy.sh`는 세 가지 작업을 수행합니다:

| 작업 | 설명 |
|------|------|
| `settings.json` 심링크 | `<target>/settings.json → <repo>/settings.json` |
| `agents/` 심링크 | `<target>/agents → <repo>/agents` |
| command 파일 생성 | `commands/*.md.template` 의 `__SKILL_ROOT__` 를 실제 경로로 치환 후 `<target>/commands/*.md` 저장 |

**심링크 방식**이므로 `git pull` 후 재배포 없이 변경이 즉시 반영됩니다.  
command 파일만 경로 치환이 필요하여 복사 방식 사용 (변경 시 재배포 필요).

### 사용법

```bash
# 전역 배포
./deploy.sh global

# 프로젝트 배포
./deploy.sh project /path/to/project

# 배포 제거
./deploy.sh remove global
./deploy.sh remove project /path/to/project
```

### 배포 후 생성되는 파일

**`~/.claude/` (global) 기준:**
```
~/.claude/
├── settings.json        → <repo>/settings.json (심링크)
├── agents/              → <repo>/agents/ (심링크)
└── commands/
    └── ppt.md           ← __SKILL_ROOT__ 가 실제 경로로 치환된 파일
```

---

## 하드코딩 경로 없음

이 리포지토리의 모든 파일은 절대경로를 포함하지 않습니다.

| 파일 | 처리 방식 |
|------|-----------|
| `commands/*.md.template` | `__SKILL_ROOT__` placeholder → `deploy.sh`가 실제 경로로 치환 |
| `skills/*/SKILL.md` | `<SKILL_ROOT>` 는 설명용 표기 (Claude가 실행 시 실제 경로는 command 파일에서 주입됨) |
| `settings.json` | 경로 무관한 권한 설정만 포함 |

새 PC에서 clone 위치가 달라져도 `./deploy.sh global` 한 번으로 해결됩니다.

---

## 스킬 목록

| 스킬 | 명령 | 설명 |
|------|------|------|
| PPT 생성 | `/ppt` | 주제 → 한국어 PPTX 자동 생성 (멀티 에이전트 파이프라인) |

각 스킬 상세는 `skills/<name>/README.md` 참고.

---

## 새 스킬 추가 방법

1. `skills/<name>/` 디렉토리 생성 후 코드 작성
2. `commands/<name>.md.template` 작성 (`__SKILL_ROOT__` 사용)
3. `./deploy.sh global` 재실행

---

## settings.json

Claude Code 권한 설정. 배포 시 `~/.claude/settings.json` 또는 `<project>/.claude/settings.json` 으로 심링크됩니다.

```json
{
  "permissions": {
    "allow": ["Bash(python3:*)", "Bash(pip3:*)", "Bash(npm:*)", "Bash(mmdc:*)", "Read", "Write", "Edit"],
    "deny": []
  }
}
```

프로젝트별로 다른 권한이 필요하면 배포 후 심링크를 일반 파일로 교체하여 수정하세요.
