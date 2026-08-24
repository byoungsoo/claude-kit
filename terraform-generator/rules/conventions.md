# Terraform 코드 규칙

이 리포지토리에서 Terraform 코드를 작성할 때 반드시 따라야 하는 구조·네이밍·코드 스타일 규칙.

---

## 1. 디렉토리 구조

```
account/
└── aws-{env}-{region}/        # 예: aws-dev-apne2, aws-manage-use1
    └── {component}/           # 예: vpc, eks, tgw, vpc-endpoint
        ├── provider.tf
        ├── main.tf
        ├── output.tf
        ├── versions.tf
        ├── var.default.tf
        ├── var.{component}.tf
        ├── var.{component}.auto.tfvars
        └── environments/
            └── {env}.tfvars   # 예: dev.tfvars
```

**규칙:**
- 계정+리전 디렉토리: `aws-{env}-{region}` 패턴 필수
- 컴포넌트 디렉토리: 단일 기능 단위 (vpc, eks, tgw 등)
- 설정 가능한 변수는 tfvars 파일로 관리

---

## 2. 환경 및 리전 식별자

### 환경 (계정)

| 식별자 | 설명 | Account ID |
|--------|------|------------|
| `manage` | 관리 계정 | 692806374063 |
| `dev` | 개발 계정 | 558846430793 |
| `shared` | 공유 계정 | 202949997891 |

### 리전

**리전 코드는 AWS 공식 AZ ID의 접두어를 그대로 사용한다.** 임의 축약(`ue1`, `ap2` 등)을 만들지 않는다.

| 리전 코드 | AWS 리전 | 지역 |
|-----------|----------|------|
| `use1` | us-east-1 | 버지니아 |
| `apne2` | ap-northeast-2 | 서울 |
| `apne3` | ap-northeast-3 | 오사카 |

기준 문서: [AWS Availability Zone IDs](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-availability-zones.html)
새 리전을 추가할 때도 위 문서의 AZ ID 접두어를 그대로 리전 코드로 쓴다.

리전 식별에는 이 접두어만 사용한다.

---

## 3. 리소스 네이밍 규칙

### 기본 패턴
```
{project_code}-{account}-{region_code}-{resource_type}-{name}
```

- **project_code**: 항상 `bys`
- **account**: `manage` | `dev` | `shared`
- **region_code**: AWS AZ ID 접두어 — `use1` | `apne2` | `apne3` (§2 참조)
- **resource_type**: 리소스 타입 약어 (아래 표 참조)
- **name**: 용도 식별자 (예: `main`, `dmz`, `app`, `db`)

### 리소스 타입 약어

| 타입 | 약어 | 예시 |
|------|------|------|
| VPC | `vpc` | `bys-dev-apne2-vpc-main` |
| Subnet | `sbn` | `bys-dev-use1-sbn-1d-db` (AZ 이름 접미사 포함) |
| Transit Gateway | `tgw` | `bys-manage-use1-tgw-main` |
| TGW Attachment | `tgw-attach` | `bys-manage-use1-tgw-attach-dev-apne2` |
| TGW Peering | `tgw-peering` | `bys-manage-use1-tgw-peering-to-apne2` |
| EKS Cluster | `eks` | `bys-dev-apne2-eks-main` |
| S3 Bucket | `s3` | `bys-shared-apne2-s3-terraform` |
| Security Group | `sg` | `bys-dev-apne2-sg-eks-node` |

> IAM Role / Policy 는 이 패턴을 쓰지 않는다. §3.1 예외 규칙을 따른다.

### 서브넷 타입 (name 값)

| name | 용도 | 가시성 |
|------|------|--------|
| `dmz` | 공용 DMZ (IGW 라우팅) | Public |
| `extelb` | 외부 로드밸런서 | Public |
| `app` | 애플리케이션 / Karpenter | Private |
| `intelb` | 내부 로드밸런서 (AWS LBC) | Private |
| `db` | 데이터베이스 | Private |
| `prvonly` | NAT 없는 완전 Private | Private |

---

## 3.1 IAM Role / Policy 네이밍 예외

**IAM Role 과 IAM Policy 는 §3 기본 패턴(`bys-{account}-{region}-...`)을 적용하지 않는다.**
IAM은 글로벌 리소스이고 콘솔·정책 문서·assume role 신뢰관계에서 사람이 읽는 경우가 많으므로,
**이름만 보고 역할을 알 수 있는 PascalCase 이름**을 사용한다.

### 규칙

- **PascalCase** — 하이픈·언더스코어·소문자 접두어 없음
- `project_code` / `account` / `region_code` 접두어를 **붙이지 않는다**
- 접미사로 리소스 종류를 명시: Role → `...Role`, Policy → `...Policy`
- 이름은 **무슨 일을 하는 역할인지** 드러나게 구성 (서비스명 + 대상/기능 + Role)
  - AWS 서비스/제품 이름은 공식 표기를 그대로 사용 — `AmazonEKS`, `AmazonBedrock`, `AWSLambda`, `Karpenter`, `Argocd`
- 계정·환경 구분이 필요하면 이름 안에 단어로 포함 — `AdminDevAccountRole`, `ArgocdDevAccessRole`
- 같은 역할의 변형(테스트·데모 등)은 언더스코어 접미사로 구분 — `..._Demo`
- 하드코딩된 문자열로 직접 지정한다. `local.common_resource_name` 을 쓰지 않는다

### 예시

| 이름 | 용도 |
|------|------|
| `EKSClusterRole` | EKS 클러스터 서비스 롤 |
| `EKSAutoModeClusterRole` | EKS Auto Mode 클러스터 롤 |
| `AmazonEKSWorkerNodeAutoModeRole` | EKS Auto Mode 워커 노드 롤 |
| `AmazonEKSWorkerNodeAutoModeRole_Demo` | 위 롤의 데모용 변형 |
| `KarpenterControllerRole` | Karpenter 컨트롤러 IRSA 롤 |
| `AmazonEKSLoadBalancerControllerRole` | AWS Load Balancer Controller 롤 |
| `AdminDevAccountRole` | dev 계정 관리자 롤 |
| `ArgocdDevAccessRole` | ArgoCD의 dev 계정 접근 롤 |
| `AmazonBedrockFullAccessRole` | Bedrock 전체 권한 롤 |
| `AWSLambdaFullAccessRole` | Lambda 전체 권한 롤 |
| `KarpenterControllerPolicy` | Karpenter 컨트롤러 정책 |

### 코드 예시

```hcl
resource "aws_iam_role" "karpenter_controller" {
  name = "KarpenterControllerRole"

  assume_role_policy = data.aws_iam_policy_document.karpenter_controller_assume.json

  tags = merge(
    { "Name" = "KarpenterControllerRole" },
    var.common_tags,
  )
}

resource "aws_iam_policy" "karpenter_controller" {
  name = "KarpenterControllerPolicy"

  policy = data.aws_iam_policy_document.karpenter_controller.json

  tags = merge(
    { "Name" = "KarpenterControllerPolicy" },
    var.common_tags,
  )
}
```

`Name` 태그도 IAM 이름과 동일하게 맞춘다 (§8의 `common_resource_name` 패턴 예외).

**적용 대상 리소스:** `aws_iam_role`, `aws_iam_policy`, `aws_iam_instance_profile`
(instance profile 은 대응하는 Role 이름 + `Profile` — 예: `AmazonEKSWorkerNodeRoleProfile`)

**적용 대상이 아닌 것:** IAM 이외의 모든 리소스는 §3 기본 패턴을 그대로 따른다.

---

## 4. 표준 변수 정의

모든 컴포넌트는 아래 변수를 반드시 포함해야 한다.

### var.default.tf (공통 변수)

```hcl
variable "project_code" {
  type    = string
  default = "bys"
}

variable "account" {
  type    = string
  # "manage" | "dev" | "shared"
}

variable "aws_region" {
  type    = string
  # 예: "ap-northeast-2"
}

variable "aws_region_code" {
  type    = string
  # 예: "apne2"
}

variable "common_tags" {
  type = map(string)
  default = {
    "Terraform"   = "true"
    "auto-delete" = "no"
  }
}
```

**공통 리소스 이름 패턴 (locals 사용):**
```hcl
locals {
  common_resource_name = "${var.project_code}-${var.account}-${var.aws_region_code}"
}
```

---

## 5. 파일 명명 규칙

| 파일 | 역할 |
|------|------|
| `provider.tf` | Provider 설정 + Backend 설정 |
| `main.tf` | 주요 리소스 및 모듈 호출 |
| `output.tf` | Output 값 정의 |
| `versions.tf` | Terraform/Provider 버전 제약 |
| `var.default.tf` | 공통 변수 (project_code, account, region 등) |
| `var.{component}.tf` | 컴포넌트 전용 변수 선언 |
| `var.{component}.auto.tfvars` | 기본 변수 값 (자동 로드) |
| `{purpose}.tf` | 목적별 분리 (예: `addons.tf`, `endpoint.tf`, `peering.tf`) |
| `environments/{env}.tfvars` | 환경별 오버라이드 값 |

---

## 6. Backend 설정 패턴

```hcl
terraform {
  backend "s3" {
    bucket  = "bys-shared-apne2-s3-terraform"
    key     = "aws-{env}-{region-code}/{project-name}/{service-name}/terraform.tfstate"
    region  = "ap-northeast-2"
    encrypt = true
  }
}
```

### Key 구조

```
aws-{env}-{region-code}/{project-name}/{service-name}/terraform.tfstate
```

| 세그먼트 | 설명 | 예시 |
|----------|------|------|
| `{env}-{region-code}` | 계정 환경 + 리전 코드 | `dev-use1`, `dev-apne2`, `manage-use1` |
| `{project-name}` | 프로젝트 이름. 공통 인프라는 `common` | `common`, `aws-whats-new` |
| `{service-name}` | 서비스/컴포넌트 이름 | `vpc-endpoint`, `eks`, `vpc` |

### Key 예시

**기본 공통 인프라** (`common` 프로젝트):
- `aws-dev-use1/common/vpc-endpoint/terraform.tfstate`
- `aws-dev-apne2/common/vpc/terraform.tfstate`
- `aws-manage-use1/common/tgw/terraform.tfstate`
- `aws-shared-apne2/common/vpc/terraform.tfstate`

**특정 프로젝트**:
- `aws-dev-apne2/aws-whats-new/eks/terraform.tfstate`
- `aws-dev-apne2/aws-whats-new/rds/terraform.tfstate`

---

## 7. Provider 설정 패턴

### 단일 계정/리전
```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::{account_id}:role/{Env}TerraformRole"
  }
}
```

### 멀티 계정/리전 (alias 사용)
```hcl
provider "aws" {
  alias  = "dev-apne2"
  region = "ap-northeast-2"

  assume_role {
    role_arn = "arn:aws:iam::558846430793:role/DevTerraformRole"
  }
}

provider "aws" {
  alias  = "shared-apne2"
  region = "ap-northeast-2"

  assume_role {
    role_arn = "arn:aws:iam::202949997891:role/SharedTerraformRole"
  }
}
```

**IAM Role 명명:**
- manage: `ManageTerraformRole`
- dev: `DevTerraformRole`
- shared: `SharedTerraformRole`

---

## 8. 태그 규칙

모든 리소스에 아래 태그를 필수 적용한다.

```hcl
tags = merge(
  { "Name" = "${local.common_resource_name}-{resource_identifier}" },
  var.common_tags,
)
```

**필수 태그:**
- `Name`: `{common_resource_name}-{식별자}` 패턴
- `Terraform`: `"true"`
- `auto-delete`: `"no"` ← 자동 삭제 방지, 반드시 포함
- `Environment`: `"dev"` | `"manage"` | `"shared"`

**예외:** IAM Role / Policy 의 `Name` 태그는 IAM 리소스 이름과 동일하게 쓴다 (§3.1 참조).
나머지 필수 태그는 IAM 리소스에도 동일하게 적용한다.

---

## 9. Versions 설정

```hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

모듈에서는 더 구체적인 버전 제약 사용 가능: `>= 5.46`

---

## 10. Locals 사용 패턴

```hcl
locals {
  common_resource_name = "${var.project_code}-${var.account}-${var.aws_region_code}"

  # 서브넷 필터링 예시
  nat_subnets = [
    for subnet in aws_subnet.public_subnets : subnet.id
    if strcontains(subnet.tags["Name"], "dmz")
  ]
}
```

---

## 12. CIDR 블록 현황

| 계정-리전 | VPC CIDR | 비고 |
|-----------|----------|------|
| manage-use1 | 10.5.0.0/16 | + secondary: 100.64.0.0/16 |
| manage-apne2 | 10.0.0.0/16 | |
| manage-apne3 | 10.3.0.0/16 | |
| dev-apne2 | 10.20.0.0/16 | |
| dev-apne3 | 10.30.0.0/16 | |
| dev-use1 | 10.25.0.0/16 | |
| shared-apne2 | 10.10.0.0/16 | |

**서브넷 CIDR 크기 기준:**
- `dmz`, `extelb`, `intelb`, `db`, `prvonly`: `/24`
- `app` (Karpenter): `/21`

---

## 13. 코드 스타일

- 들여쓰기: 스페이스 2칸
- 블록 내 속성 정렬: 값 기준 정렬 권장
- 변수 설명: `description` 필드 필수
- `for` 표현식으로 리소스 반복 처리 (count보다 `for_each` 선호)
- cross-account 참조는 `locals`에 명시적으로 하드코딩 후 참조
