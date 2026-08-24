---
description: Terraform 코드 작성·수정을 요청할 때 호출. 예: "vpc 만들어줘", "eks 컴포넌트 추가해줘", "terraform 코드 작성해줘", "새 계정 리전에 vpc 추가해줘"
argument-hint: "<컴포넌트 설명> [--account manage|dev|shared] [--region use1|apne2|apne3] [--env dev|manage|shared]"
deploy-scope: both
---

# Terraform 코드 작성 스킬

당신은 이 리포지토리의 Terraform 코드 작성 오케스트레이터입니다.

**반드시** `__PROJECT_ROOT__/.claude/rules/__KIT_NAME__-conventions.md` 파일의 규칙을 먼저 읽고 모든 코드에 적용하세요.

## 파라미터 파싱 및 확인

`$ARGUMENTS`에서 컴포넌트 정보를 파싱한 뒤 사용자에게 확인합니다:

```
아래 설정으로 Terraform 코드를 생성합니다. 변경할 항목이 있으면 말씀해주세요.

- 컴포넌트: {component}
- 계정: {account} (manage | dev | shared)
- 리전: {region_code} (use1 | apne2 | apne3 — AWS AZ ID 접두어)
- 대상 경로: account/aws-{account}-{region_code}/{component}/
```

### 기본값
- `--account` 미지정 → 사용자에게 명시적으로 물어볼 것
- `--region` 미지정 → 사용자에게 명시적으로 물어볼 것

---

## 작업 흐름

### 기존 코드 수정 요청인 경우

1. 대상 파일을 Read 도구로 읽어 현재 상태 파악
2. conventions 규칙에 맞게 수정
3. 변경 내용 요약 보고

### 신규 컴포넌트 생성 요청인 경우

아래 순서로 파일 생성:

**1단계 — 기존 패턴 참조**
- 동일 컴포넌트의 다른 계정/리전 디렉토리가 있으면 먼저 Read
- 없으면 가장 유사한 컴포넌트 참조

**2단계 — 파일 생성**

아래 파일을 순서대로 생성한다:

1. `versions.tf` — Terraform/Provider 버전 제약
2. `provider.tf` — Provider + Backend 설정
3. `var.default.tf` — 공통 변수 (project_code, account, aws_region, aws_region_code, common_tags)
4. `var.{component}.tf` — 컴포넌트 전용 변수
5. `var.{component}.auto.tfvars` — 기본 변수 값
6. `main.tf` — 주요 리소스 정의
7. `output.tf` — 출력 값
8. `environments/{env}.tfvars` — 환경별 오버라이드 (필요시)

**3단계 — 검증**

생성 후 아래 항목을 자체 검토한다:

- [ ] 리소스 이름이 `{project_code}-{account}-{region_code}-{type}-{name}` 패턴을 따르는가
- [ ] IAM Role / Policy 이름은 예외 규칙(§3.1)대로 PascalCase 역할 기반 이름인가 (`KarpenterControllerRole` 형태, `bys-` 접두어 없음)
- [ ] `auto-delete = "no"` 태그가 모든 리소스에 포함되어 있는가
- [ ] `Terraform = "true"` 태그가 포함되어 있는가
- [ ] Backend key가 `aws-{account}/{region}/{component}/terraform.tfstate` 형식인가
- [ ] `local.common_resource_name` locals를 사용하는가
- [ ] `var.default.tf`에 표준 변수가 모두 정의되어 있는가

---

## 완료 보고

```
Terraform 코드 생성 완료

생성된 파일:
- account/aws-{account}-{region}/{component}/versions.tf
- account/aws-{account}-{region}/{component}/provider.tf
- account/aws-{account}-{region}/{component}/var.default.tf
- account/aws-{account}-{region}/{component}/var.{component}.tf
- account/aws-{account}-{region}/{component}/var.{component}.auto.tfvars
- account/aws-{account}-{region}/{component}/main.tf
- account/aws-{account}-{region}/{component}/output.tf

Backend 경로: aws-{account}/{region}/{component}/terraform.tfstate
```
