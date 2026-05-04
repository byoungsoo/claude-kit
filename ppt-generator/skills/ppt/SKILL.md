---
description: 사용자가 PPT, PPTX, 발표자료, 프레젠테이션 생성을 요청할 때 호출. 예: "ppt 만들어줘", "발표자료 만들어줘", "~에 대한 pptx 생성해줘"
argument-hint: "<주제> [--slides N] [--theme 이름] [--audience 청중] [--output 경로]"
---

# PPT 생성 스킬

당신은 PPT 생성 오케스트레이터입니다. 서브에이전트들을 순서대로 실행하여 고품질 PPTX를 만들어냅니다.

## 파라미터 파싱

`$ARGUMENTS`에서 다음을 파싱하세요:
- `주제` — 첫 번째 인수 (필수, 없으면 사용자에게 질문)
- `--slides N` — 슬라이드 수 (기본값: 12)
- `--theme 이름` — 테마 (기본값: corporate_navy)
- `--audience 청중` — 대상 청중 (기본값: 일반 전문가)
- `--output 경로` — 출력 경로 (기본값: ./output.pptx)
- `--duration N` — 발표 시간 분 (기본값: 20)

사용 가능한 테마: `corporate_navy`, `startup_bold`, `dark_tech`, `academic_clean`

---

## 파이프라인

아래 단계를 **순서대로** 실행하세요. 각 단계의 출력을 다음 단계에 전달합니다.

### 1단계 — 리서치

`@ppt-research` 에이전트를 호출합니다:

```
주제: {주제}
청중: {audience}
발표 시간: {duration}분
```

결과를 `research` 변수에 저장합니다.

---

### 2단계 — 아웃라인

`@ppt-outline` 에이전트를 호출합니다:

```
주제: {주제}
청중: {audience}
슬라이드 수: {slides}
발표 시간: {duration}분
리서치 데이터:
{research}
```

결과를 `outline` 변수에 저장합니다.

---

### 3단계 — 콘텐츠 생성

`@ppt-content` 에이전트를 호출합니다:

```
주제: {주제}
청중: {audience}
아웃라인:
{outline}
리서치 데이터:
{research}
```

결과를 `slides_json` 변수에 저장합니다.

---

### 4단계 — 디자인 스펙

`@ppt-design` 에이전트를 호출합니다:

```
테마: {theme}
슬라이드 콘텐츠:
{slides_json}
```

결과를 `design_json` 변수에 저장합니다.

---

### 5단계 — QA 검토

`@ppt-qa` 에이전트를 호출합니다:

```
슬라이드 콘텐츠:
{slides_json}
아웃라인:
{outline}
```

QA 결과에서 `needs_revision: true` 슬라이드가 있으면:

- `@ppt-content`를 재호출하여 해당 슬라이드만 재생성
  ```
  다음 슬라이드를 수정하세요:
  {needs_revision 슬라이드 목록과 revision_instruction}
  
  기존 콘텐츠:
  {slides_json}
  ```
- 재생성된 슬라이드로 `slides_json` 업데이트
- 재검토는 최대 2회

---

### 6단계 — 렌더링

임시 파일에 JSON을 저장하고 렌더러를 실행합니다:

```bash
SKILL_DIR="$(dirname "$0")"
cd "$SKILL_DIR"

# JSON 저장
echo '{slides_json}' > /tmp/ppt_slides.json
echo '{design_json}' > /tmp/ppt_design.json

# 렌더링
python3 -m src.ppt_generator.cli.render \
  --slides /tmp/ppt_slides.json \
  --design /tmp/ppt_design.json \
  --theme {theme} \
  --output {output}

# 임시 파일 정리
rm -f /tmp/ppt_slides.json /tmp/ppt_design.json
```

---

## 완료 보고

렌더링이 성공하면 다음을 출력하세요:

```
✓ PPT 생성 완료: {output}
  - 슬라이드: {slides}장
  - 테마: {theme}
  - QA 점수: {overall_deck_score}/10
  - 수정 횟수: {revision_count}회
```

오류 발생 시 단계와 오류 메시지를 명확히 보고하세요.
