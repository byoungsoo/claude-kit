---
description: draw.io 다이어그램 생성을 요청할 때 호출. AWS 아키텍처, API 흐름, 시스템 구성도 등. 예: "아키텍처 그려줘", "다이어그램 만들어줘", "draw.io로 그려줘"
argument-hint: "<주제 또는 설명> [--output 경로]"
deploy-scope: both
---

# draw.io 다이어그램 생성 스킬

당신은 draw.io 다이어그램 생성 오케스트레이터입니다.

## 사전 확인 — draw.io MCP 연결 여부

**파이프라인 시작 전 반드시** 사용자에게 아래 내용을 확인합니다:

```
draw.io 다이어그램 생성에는 draw.io MCP 연결이 필요합니다.

draw.io MCP가 연결되어 있지 않은 경우 먼저 설치가 필요합니다:
  1. draw.io 데스크탑 앱 설치: https://www.drawio.com
  2. Claude Code에 draw.io MCP 서버 연결

draw.io MCP가 준비되어 있으신가요? (Y/N)
```

- **Y** → 파이프라인 진행
- **N** → 설치 안내 후 종료:
  ```
  draw.io 설치 후 다시 시도해주세요.
  설치: https://www.drawio.com (데스크탑 앱)
  MCP 연결: Claude Code 설정에서 draw.io MCP 서버 추가
  ```

---

## 파라미터 파싱 및 확인

`$ARGUMENTS`에서 주제와 옵션을 파싱한 뒤 사용자에게 확인합니다:

```
아래 설정으로 다이어그램을 생성합니다. 변경할 항목이 있으면 말씀해주세요.

- 주제: {주제}
- 다이어그램 유형: {aws_architecture|api_flow|system_diagram} (자동 감지)
- 출력 경로: {output} (.drawio 파일)
```

### 기본값
- `--output` 미지정 → `./diagram.drawio`

---

## 파이프라인

### 1단계 — 아키텍처 설계

`[1/3] 아키텍처 설계 중...` 을 사용자에게 알린 뒤, `@drawio-generator-architect` 에이전트를 실행합니다:

```
유형: {diagram_type}
주제: {주제}
상세 설명: {사용자가 제공한 전체 설명}
aws4-styles.md 경로: __PROJECT_ROOT__/.claude/skills/drawio-generator-drawio/assets/aws4-styles.md
```

완료되면 결과(아키텍처 스펙)를 `arch_spec`에 저장합니다.

---

### 2단계 — XML 생성

`[2/3] XML 생성 중...` 을 사용자에게 알린 뒤, `@drawio-generator-draw` 에이전트를 실행합니다:

```
아래 아키텍처 스펙을 draw.io XML로 변환해주세요. (MCP 임포트는 아직 하지 마세요)

aws4-styles.md 경로: __PROJECT_ROOT__/.claude/skills/drawio-generator-drawio/assets/aws4-styles.md

{arch_spec}
```

완료되면 반환된 XML을 `drawio_xml`에 저장합니다.

---

### 3단계 — QA 검증

`[3/4] 스타일 검증 중...` 을 사용자에게 알린 뒤, `@drawio-generator-qa` 에이전트를 실행합니다:

```
아래 XML이 aws4-styles.md 스타일 규칙을 준수하는지 검증해주세요.

aws4-styles.md 경로: __PROJECT_ROOT__/.claude/skills/drawio-generator-drawio/assets/aws4-styles.md

{drawio_xml}
```

- **PASS** → 4단계로 진행
- **FAIL** → 위반 목록을 포함해 `@drawio-generator-draw` 에이전트를 재실행합니다 (최대 1회):

```
아래 스타일 위반 사항을 수정하여 XML을 다시 생성해주세요.

aws4-styles.md 경로: __PROJECT_ROOT__/.claude/skills/drawio-generator-drawio/assets/aws4-styles.md

[위반 목록]
{qa_result}

[기존 XML]
{drawio_xml}
```

재생성된 XML로 `drawio_xml`을 업데이트합니다.

---

### 4단계 — draw.io 앱 반영 및 파일 저장

`[4/4] 저장 중...` 을 사용자에게 알린 뒤, 아래를 순서대로 실행합니다.

**draw.io MCP 임포트** — `@drawio-generator-draw` 에이전트를 실행합니다:

```
아래 XML을 MCP로 draw.io 앱에 임포트해주세요.

{drawio_xml}
```

**파일 저장** — `drawio_xml`을 `{output}` 경로에 저장합니다:

```bash
cat > {output} << 'EOF'
{drawio_xml}
EOF
```

---

## 완료 보고

```
✓ 다이어그램 생성 완료
  - draw.io 앱: 반영 완료
  - 파일: {output}
```

오류 발생 시 단계와 오류 메시지를 명확히 보고하세요.
