# Claude Kit

Claude Code에서 사용하는 커스텀 kit를 관리하는 리포지토리.

각 kit는 독립적인 디렉토리로 관리되며, `deploy.sh` 한 번으로 어느 PC에서든 동일한 환경을 구성할 수 있습니다.

---

## 컨셉

Claude Code 자체가 AI 역할을 수행합니다. Python은 PPTX 조립 등 순수 렌더링만 담당합니다.

```
사용자 요청
    ↓
SKILL.md (오케스트레이터)
    ↓ 서브에이전트 순차 호출
  @ppt-research → @ppt-outline → @ppt-content → @ppt-design → @ppt-qa
    ↓ JSON 결과
Python 렌더러 (python-pptx)
    ↓
output.pptx
```

별도의 API 키가 필요 없습니다. Claude Code 세션이 곧 AI 엔진입니다.

---

## 리포지토리 구조

```
claude-kit/
├── README.md              ← 이 파일
├── CLAUDE.md              ← Claude 세션 컨텍스트
├── settings.json          ← Claude Code 권한 설정
├── deploy.sh              ← 배포 스크립트 (kit 단위, prefix 적용)
│
└── ppt-generator/                ← PPT 자동 생성 kit
    ├── skills/
    │   └── ppt/                  ← 오케스트레이터 스킬
    │       ├── SKILL.md          ← 파이프라인 실행 지침
    │       ├── src/              ← Python 렌더러 (python-pptx)
    │       │   └── ppt_generator/
    │       │       ├── cli/render.py     ← JSON → PPTX 변환 CLI
    │       │       ├── rendering/        ← 슬라이드 렌더링
    │       │       └── schema/           ← Pydantic 데이터 계약
    │       ├── themes/           ← 디자인 테마 JSON
    │       └── scripts/          ← PPTX 편집 유틸리티
    ├── agents/                   ← Claude 서브에이전트
    │   ├── ppt-research.md       ← 주제 리서치
    │   ├── ppt-outline.md        ← 슬라이드 구조 설계
    │   ├── ppt-content.md        ← 슬라이드별 콘텐츠 생성
    │   ├── ppt-design.md         ← 레이아웃·디자인 스펙
    │   └── ppt-qa.md             ← 품질 검토 및 재생성 판정
    └── rules/
        └── ppt-detail.md         ← PPT 스킬 상세 참조
```

---

## Kit 목록

| Kit | 호출 방법 | 설명 |
|-----|-----------|------|
| `ppt-generator` | `/ppt-generator-ppt <주제>` 또는 자연어 | 주제 → 한국어 PPTX 자동 생성 |

**자연어 호출 예시:**
- `"ppt 만들어줘"`
- `"쿠버네티스 보안에 대한 발표자료 만들어줘"`
- `"AI 트렌드 12장짜리 pptx 생성해줘"`

---

## 빠른 시작

### 1. Clone

```bash
git clone <repo-url> ~/claude-kit
cd ~/claude-kit
```

### 2. Python 렌더러 의존성 설치

```bash
pip3 install -r ppt-generator/skills/ppt/requirements.txt --break-system-packages

# 다이어그램 고품질 렌더링 (선택)
npm install -g @mermaid-js/mermaid-cli
```

### 3. 배포

```bash
# 전역 배포 — 모든 프로젝트에서 사용 가능
./deploy.sh ppt-generator global

# 특정 프로젝트에만 배포
./deploy.sh ppt-generator project /path/to/my-project
```

배포 후 Claude Code를 재시작하면 slash command와 자동 호출이 활성화됩니다.

---

## ppt-generator 사용법

### 기본 사용

```
/ppt-generator-ppt 쿠버네티스 보안 모범 사례
```

또는 그냥 대화하듯:

```
쿠버네티스 보안 모범 사례에 대한 발표자료 만들어줘
```

### 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--slides N` | 12 | 슬라이드 수 |
| `--theme 이름` | corporate_navy | 디자인 테마 |
| `--audience 청중` | 일반 전문가 | 대상 청중 |
| `--output 경로` | ./output.pptx | 출력 파일 경로 |
| `--duration N` | 20 | 발표 시간(분) |

### 테마

| 테마 | 특징 |
|------|------|
| `corporate_navy` | 네이비/오렌지, 기업 발표용 |
| `startup_bold` | 퍼플/핑크, 스타트업용 |
| `dark_tech` | 다크모드, 기술 발표용 |
| `academic_clean` | 화이트/네이비, 학술용 |

### 파이프라인

```
1. @ppt-research  — 주제 리서치 (웹 검색, 통계, 시각화 포인트 수집)
2. @ppt-outline   — 내러티브 구조 설계 (슬라이드 목록, 전환 흐름)
3. @ppt-content   — 슬라이드별 콘텐츠 생성 (텍스트, 차트 스펙, 다이어그램)
4. @ppt-design    — 레이아웃·디자인 스펙 결정
5. @ppt-qa        — 품질 검토 (7점 미만 슬라이드 자동 재생성, 최대 2회)
6. Python 렌더러  — JSON → PPTX 조립
```

### PPTX 편집 모드

기존 파일 수정 시 `scripts/` 유틸리티 사용:

```bash
cd ppt-generator/skills/ppt

# 썸네일로 현황 파악
python3 scripts/thumbnail.py file.pptx thumbnails --cols 4

# XML 편집
python3 scripts/office/unpack.py file.pptx unpacked/
# ... XML 수정 ...
python3 scripts/office/pack.py unpacked/ output.pptx
```

---

## deploy.sh 상세

kit 단위로 배포하며, 모든 파일에 **kit명을 prefix**로 붙여 여러 kit가 충돌하지 않습니다.

| 대상 | 처리 방식 | 배포 후 경로 |
|------|-----------|-------------|
| `skills/<name>/` | 심링크 | `<target>/skills/<kit>-<name>/` |
| `agents/<name>.md` | 심링크 | `<target>/agents/<kit>-<name>.md` |
| `rules/<name>.md` | 심링크 | `<target>/rules/<kit>-<name>.md` |

모두 심링크 방식이므로 `git pull` 후 재배포 없이 변경이 즉시 반영됩니다.

### 사용법

```bash
./deploy.sh <kit-name> global
./deploy.sh <kit-name> project /path/to/project
./deploy.sh <kit-name> remove global
./deploy.sh <kit-name> remove project /path/to/project
```

### 배포 후 생성되는 파일 (`ppt-generator global` 기준)

```
~/.claude/
├── skills/
│   └── ppt-generator-ppt/          → <repo>/ppt-generator/skills/ppt/ (심링크)
├── agents/
│   ├── ppt-generator-ppt-research.md  → <repo>/ppt-generator/agents/ppt-research.md (심링크)
│   ├── ppt-generator-ppt-outline.md
│   ├── ppt-generator-ppt-content.md
│   ├── ppt-generator-ppt-design.md
│   └── ppt-generator-ppt-qa.md
└── rules/
    └── ppt-generator-ppt-detail.md → <repo>/ppt-generator/rules/ppt-detail.md (심링크)
```

---

## 새 Kit 추가 방법

```
claude-kit/
└── <kit-name>/
    ├── skills/<name>/
    │   └── SKILL.md          ← description frontmatter 필수 (자동 호출용)
    ├── agents/<name>.md      ← 선택: 서브에이전트 정의
    └── rules/<name>.md       ← 선택: 조건부 로드 지침
```

1. `<kit-name>/` 디렉토리에 위 구조로 파일 작성
2. `SKILL.md`에 `description` frontmatter 추가 (자연어 자동 호출용)
3. `./deploy.sh <kit-name> global` 실행

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
