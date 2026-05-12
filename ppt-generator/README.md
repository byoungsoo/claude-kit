# ppt-generator

주제를 입력하면 서브에이전트 파이프라인을 통해 한국어 PPTX를 자동 생성하는 kit.

## 배포

`ppt-generator`는 **global 전용 kit**입니다.

```bash
./deploy.sh ppt-generator global
```

배포 후 Claude Code를 재시작하면 활성화됩니다.

### 의존성 설치

```bash
pip3 install -r ppt-generator/skills/ppt/requirements.txt --break-system-packages

# 다이어그램 고품질 렌더링 (선택)
npm install -g @mermaid-js/mermaid-cli
```

---

## 사용법

### 기본 사용

```
/ppt-generator-ppt 쿠버네티스 보안 모범 사례
```

또는 자연어로:

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

---

## 파이프라인

```
1. @ppt-research  — 주제 리서치 (웹 검색, 통계, 시각화 포인트 수집)
2. @ppt-outline   — 내러티브 구조 설계 (슬라이드 목록, 전환 흐름)
3. @ppt-content   — 슬라이드별 콘텐츠 생성 (텍스트, 차트 스펙, 다이어그램)
4. @ppt-design    — 레이아웃·디자인 스펙 결정
5. @ppt-qa        — 품질 검토 (7점 미만 슬라이드 자동 재생성, 최대 2회)
6. Python 렌더러  — JSON → PPTX 조립
```

---

## PPTX 편집 모드

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
