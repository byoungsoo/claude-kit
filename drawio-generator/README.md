# drawio-generator

AWS 아키텍처·시스템 구성도를 자연어로 요청하면 서브에이전트 파이프라인을 통해 draw.io 다이어그램을 자동 생성하는 kit.

## 사전 요구사항

- draw.io 데스크탑 앱 설치: https://www.drawio.com
- Claude Code에 draw.io MCP 서버 연결

---

## 배포

`drawio-generator`는 **global/project 모두 지원**합니다.

```bash
# global 배포 — 모든 프로젝트에서 사용
./deploy.sh drawio-generator add global

# project 배포 — 특정 프로젝트에서만 사용
./deploy.sh drawio-generator add project /path/to/project
```

배포 후 Claude Code를 재시작하면 활성화됩니다.

---

## 사용법

### 기본 사용

```
/drawio-generator-drawio 3-tier 웹 아키텍처 (2 AZ, ALB + EC2 + RDS)
```

또는 자연어로:

```
AWS 아키텍처 그려줘. EKS 기반 마이크로서비스, ap-northeast-2, 2 AZ
```

### 출력 경로 지정

```
/drawio-generator-drawio VPC 기본 구조 --output ./my-arch.drawio
```

`--output` 미지정 시 `./diagram.drawio`에 저장됩니다.

---

## 파이프라인

```
SKILL.md (오케스트레이터)
    ↓
[1/4] @drawio-generator-architect  — 요구사항 분석 → 아키텍처 스펙
[2/4] @drawio-generator-draw       — 스펙 → draw.io XML + MCP 임포트
[3/4] @drawio-generator-qa         — 스타일 위반 검증 (PASS/FAIL)
[4/4] 파일 저장                    — .drawio 파일 출력
```

---

## 주요 파일

| 파일 | 역할 |
|------|------|
| `skills/drawio/SKILL.md` | 파이프라인 오케스트레이터 |
| `agents/architect.md` | 아키텍처 설계 서브에이전트 |
| `agents/draw.md` | draw.io XML 생성 서브에이전트 |
| `agents/qa.md` | 스타일 검증 서브에이전트 |
| `skills/drawio/assets/aws4-styles.md` | AWS4 아이콘·그룹 스타일 단일 소스 |
| `skills/drawio/assets/sample/` | 참고용 샘플 다이어그램 |

---

## 레이아웃 방향

| 조건 | 방향 |
|------|------|
| VPC / AZ / Subnet 포함 | 위→아래 (top-down) |
| 관리형 서비스만 (VPC 없음) | 좌→우 (left-right) |

---

## 스타일 정책

- 모든 스타일은 `aws4-styles.md`에서만 읽음 — 임의 변경 금지
- 아이콘 크기: 80×80
- 그룹 크기: 아키텍처 규모에 따라 동적 계산
- 연결선: 화살표만 표시 (레이블 없음)
- Multi-AZ 구조: 모든 AZ 크기 대칭 유지
