# terraform-generator

Terraform 코드 작성 시 일관된 디렉토리 구조, 네이밍, 코드 스타일을 유지하도록 돕는 kit.

## 특징

- **global / project 배포 모두 지원** — 여러 Terraform 리포에서 쓰려면 global, 특정 리포에만 적용하려면 project
- **conventions 규칙 선행 로드** — 스킬이 실행 시 `rules/conventions.md`를 먼저 읽고 코드에 적용
- **신규 컴포넌트 스캐폴딩** — 표준 파일 구조(7개 파일)를 자동 생성
- **기존 코드 검토/수정** — conventions 규칙 기반으로 네이밍·태그 일관성 유지

## 배포 방법

```bash
# 모든 프로젝트에서 사용 (global)
./deploy.sh terraform-generator add global

# 특정 Terraform 리포지토리에만 적용 (project)
./deploy.sh terraform-generator add project /path/to/terraform

# 제거
./deploy.sh terraform-generator remove global
./deploy.sh terraform-generator remove project /path/to/terraform
```

## 사용 방법

배포 후 Terraform 리포지토리에서:

```
# 자연어
vpc 만들어줘 --account dev --region apne2
eks 컴포넌트 추가해줘

# 슬래시 커맨드
/terraform-generator vpc --account manage --region use1
```

## 규칙 요약

`rules/conventions.md` (배포 후 `<project>/.claude/rules/terraform-generator-conventions.md`) 에 상세 규칙이 정의되어 있으며, 아래를 다룹니다:

| 규칙 | 내용 |
|------|------|
| 디렉토리 구조 | `account/aws-{env}-{region}/{component}/` |
| 리소스 네이밍 | `bys-{account}-{region_code}-{type}-{name}` |
| 표준 파일 | `provider.tf`, `main.tf`, `output.tf`, `versions.tf`, `var.*.tf` |
| 태그 | `Name`, `Terraform: "true"`, `auto-delete: "no"` 필수 |
| Backend | S3 key: `aws-{account}/{region}/{component}/terraform.tfstate` |
| 서브넷 타입 | dmz / extelb / app / intelb / db / prvonly |
| 리전 코드 | AWS AZ ID 접두어 사용 — use1 (버지니아), apne2 (서울), apne3 (오사카) |
| CIDR 현황 | manage-use1: 10.5/16, dev-apne2: 10.20/16 등 |
