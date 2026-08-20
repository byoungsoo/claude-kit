# resume-generator

채용공고를 입력하면 서브에이전트 파이프라인을 통해 맞춤 이력서를 자동 작성하는 kit.

## 배포

`resume-generator`는 **project 전용 kit**입니다. resume 프로젝트 경로를 지정해서 배포해야 합니다.

```bash
./deploy.sh resume-generator add project /path/to/resume-project
```

배포 시 `SKILL.md` 내의 `__PROJECT_ROOT__` placeholder가 지정한 경로로 자동 치환됩니다.
배포 후 Claude Code를 재시작하면 활성화됩니다.

---

## 사용법

### 기본 사용

```
/resume-generator 아래 채용공고로 이력서 작성해줘
```

또는 자연어로:

```
이력서 작성해줘 (채용공고 붙여넣기)
```

---

## 파이프라인

```
1. @resume-generator-company-researcher — 회사·직무 분석 보고서 작성 (content/015.research/ 저장)
2. @resume-generator-writer             — 분석 결과 + 프로필 기반 이력서 작성 (content/010.resume/ 저장)
3. @resume-generator-reviewer           — 문법·AI 투 표현·공고 적합성 QA
4. @resume-generator-hr-leader          — 합격 가능성 판정 (낮음이면 2~4단계 최대 2회 재작업)
```

---

## 참고 파일 (resume 프로젝트)

에이전트들이 읽는 지원자 프로필 파일:

| 파일 | 내용 |
|------|------|
| `content/000.profile/001-resume_kr-intro.md` | 인적사항, 학력, 경력 요약, 자격증 |
| `content/000.profile/002-resume_kr-job.md` | 직무별 상세 경력 기술 |
| `content/100.posts/it/**/*.md` | 프로젝트 경험 요약 |

출력 파일:

| 경로 | 내용 |
|------|------|
| `content/015.research/<회사명>_<직무>_<날짜>.md` | 회사 분석 보고서 |
| `content/010.resume/<날짜>-<회사명>.md` | 작성된 이력서 |
