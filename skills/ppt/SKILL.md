# PPT 생성 스킬

한국어 고품질 PPTX를 생성하는 멀티 에이전트 파이프라인 스킬입니다.

## 개요

이 스킬은 두 가지 모드를 지원합니다:

| 모드 | 설명 | 사용 시점 |
|------|------|-----------|
| **생성 모드** | 주제를 입력받아 처음부터 PPTX 생성 | 새 발표 자료 제작 |
| **편집 모드** | 기존 PPTX를 언팩하여 XML 직접 수정 | 기존 파일 수정/업데이트 |

---

## 생성 모드

### 실행 명령

```bash
# <SKILL_ROOT> = 이 파일이 위치한 디렉토리 (skills/ppt/)
cd <SKILL_ROOT> && python3 -m src.ppt_generator.cli.main generate "<주제>" [옵션]
```

### 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--slides N` | 12 | 슬라이드 수 |
| `--theme <이름>` | corporate_navy | 테마 선택 |
| `--audience "<청중>"` | "일반 전문가" | 대상 청중 |
| `--output <경로>` | ./output.pptx | 출력 파일 경로 |
| `--url "<URL>"` | - | 참고 URL (반복 사용 가능) |
| `--duration N` | 20 | 발표 시간(분) |
| `--tone <톤>` | professional | 톤 (professional/casual/academic/inspiring) |

### 사용 가능한 테마

| 테마 | 특징 |
|------|------|
| `corporate_navy` | 네이비/오렌지, 기업용 |
| `startup_bold` | 퍼플/핑크, 스타트업용 |
| `dark_tech` | 다크모드, 기술 발표용 |
| `academic_clean` | 화이트/네이비, 학술용 |

### 파이프라인 단계

```
ResearchAgent  → 주제 사실·통계·시각화 수집
OutlineAgent   → 확장 사고로 내러티브 구조 설계
ContentAgent   → 슬라이드별 개별 호출로 콘텐츠 작성
CriticAgent    → 슬라이드 간 흐름·일관성 검토
DesignAgent    → 레이아웃·타이포·강조 설계
Renderer       → OXML 직접 제어로 PPTX 조립
QAAgent        → 점수 7 미만 슬라이드 자동 재생성 (최대 2회)
```

### 예시

```bash
# 기본
python3 -m src.ppt_generator.cli.main generate "생성형 AI가 금융 산업에 미치는 영향"

# 옵션 지정
python3 -m src.ppt_generator.cli.main generate "쿠버네티스 보안 모범 사례" \
  --slides 15 --theme dark_tech --audience "DevOps 엔지니어" \
  --output ./k8s_security.pptx

# 외부 자료 참고
python3 -m src.ppt_generator.cli.main generate "AWS EKS 운영 전략" \
  --url "https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html" \
  --theme corporate_navy
```

---

## 편집 모드

기존 PPTX 파일을 수정할 때는 XML 직접 편집 방식을 사용합니다.

### 워크플로우

#### 1단계: 현황 파악

```bash
cd <SKILL_ROOT>/scripts
python3 thumbnail.py <파일.pptx> thumbnails --cols 4
```

#### 2단계: 언팩

```bash
python3 office/unpack.py <파일.pptx> unpacked/
```

언팩 후 구조:
```
unpacked/
├── ppt/
│   ├── presentation.xml      ← 슬라이드 순서 관리
│   ├── slides/
│   │   ├── slide1.xml        ← 각 슬라이드 XML
│   │   └── _rels/
│   ├── slideLayouts/         ← 레이아웃 템플릿
│   └── theme/
└── [Content_Types].xml
```

#### 3단계: 슬라이드 편집

**슬라이드 추가/복제:**
```bash
python3 add_slide.py unpacked/ slide2.xml          # 기존 슬라이드 복제
python3 add_slide.py unpacked/ slideLayout2.xml    # 레이아웃으로 새 슬라이드 생성
# 출력된 <p:sldId> 요소를 presentation.xml의 <p:sldIdLst>에 추가
```

**XML 직접 편집 원칙:**
- 텍스트 변경: `<a:t>` 태그 내용 수정
- 헤더/인라인 레이블: `b="1"` 속성으로 볼드 적용
- 여러 항목: 하나의 문자열로 합치지 말고 별도 단락 사용
- 스마트 따옴표: `&#x201C;` `&#x201D;` XML 엔티티 사용
- **Edit 도구 사용** (스크립트 대신) — 더 안정적

#### 4단계: 정리

```bash
python3 clean.py unpacked/
```

#### 5단계: 리팩

```bash
python3 office/pack.py unpacked/ output.pptx
python3 office/pack.py unpacked/ output.pptx --original original.pptx  # 검증 포함
```

#### 6단계: QA 검증

```bash
python3 thumbnail.py output.pptx qa_review --cols 4
```

썸네일로 다음을 확인:
- 텍스트 오버플로우 / 겹침
- 플레이스홀더 미치환 ("XXXX", "Lorem Ipsum")
- 오타
- 요소 간 간격·정렬 이상

---

## 스크립트 레퍼런스

| 스크립트 | 위치 | 용도 |
|----------|------|------|
| `thumbnail.py` | `scripts/` | PPTX → 슬라이드 썸네일 그리드 |
| `add_slide.py` | `scripts/` | 슬라이드 복제 또는 레이아웃으로 추가 |
| `clean.py` | `scripts/` | 언팩 디렉토리 고아 파일 정리 |
| `office/unpack.py` | `scripts/office/` | PPTX → XML 디렉토리 |
| `office/pack.py` | `scripts/office/` | XML 디렉토리 → PPTX |
| `office/soffice.py` | `scripts/office/` | LibreOffice 헬퍼 (PDF 변환용) |

---

## 디자인 원칙

생성 및 편집 시 항상 지켜야 할 원칙:

- **텍스트 전용 슬라이드 금지** — 모든 슬라이드에 이미지·차트·아이콘·도형 중 하나 이상 포함
- **색상 전략** — 주 색상(60~70%), 보조 색상, 액센트 1개
- **타이포그래피** — 제목 36~44pt, 본문 14~16pt
- **레이아웃 다양성** — 2단 구성·그리드·콜아웃·전체화면 이미지를 순환
- **단조로운 반복 금지** — 같은 레이아웃을 연속 3장 이상 사용하지 않음
