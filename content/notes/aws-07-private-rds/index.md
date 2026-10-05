---
title: "AWS 7단계 · Terraform 기반 Private RDS 구축"
date: 2026-08-27
projects: ["aws-infra"]
step: 7
summary: "퍼블릭 EC2와 프라이빗 RDS를 분리해 구성하고, DB가 외부에서 직접 접근되지 않는 구조를 Terraform 코드로 만든다."
tags: ["IaC", "데이터베이스", "네트워크", "보안", "구축"]
troubleshooting: []
draft: false
---

## 목표

퍼블릭 EC2와 프라이빗 RDS를 분리해 구성하고, DB가 외부에서 직접 접근되지 않는 구조를 Terraform 코드로 만든다.

## 사전 계획

### 구성도

```javascript
Internet
   │
   ▼
[EC2]  Public Subnet
   │
   │ MySQL 3306
   │ Source: EC2 보안 그룹
   ▼
[RDS]  Private Subnet × 2 (서로 다른 AZ)
       publicly_accessible = false
```

### 진행 순서

- [ ] Private Subnet 2개 생성 (서로 다른 AZ)
- [ ] DB Subnet Group 구성
- [ ] RDS 전용 보안 그룹 생성 (3306 허용, source = EC2 보안 그룹)
- [ ] RDS MySQL 리소스 작성 (`publicly_accessible = false`)
- [ ] `terraform plan` → `apply`
- [ ] EC2에서 MySQL 접속 확인
- [ ] `CREATE DATABASE` / `CREATE TABLE` / `INSERT` / `SELECT`
- [ ] 내 PC에서 직접 접속 실패 검증
- [ ] `terraform destroy`

### 이번 단계의 핵심

| 항목 | 내용 |
| --- | --- |
| 계층 분리 | 퍼블릭(EC2)과 프라이빗(RDS)을 나누어 DB를 외부에 노출하지 않는다 |
| DB Subnet Group | RDS는 반드시 서로 다른 최소 2개 AZ의 서브넷을 포함해야 한다. Single-AZ로 만들어도 동일 |
| 보안 그룹 참조 | 3306의 source를 IP가 아니라 EC2 보안 그룹으로 지정. 4단계에서 배운 개념을 서비스 계층 간 접근제어에 적용 |
| 외부 접속 실패 검증 | 설정만 하고 끝내지 않고, "외부는 실패 / EC2는 성공"을 실제 결과로 보여준다 |
| 데이터 입력까지 | 접속 성공만으로는 "네트워크 연결 확인"에 그친다. CREATE/INSERT/SELECT까지 해야 8단계 앱 연결로 이어진다 |

### 주의사항

#### skip_final_snapshot

`aws_db_instance`의 기본값은 `false`라, 최종 스냅샷 이름 없이 `destroy`하려 하면 삭제가 막힌다. 실습 환경이므로 동작을 명확히 설정해둔다.

#### DB 비밀번호

`.tf` 파일에 직접 적지 않는다.

```hcl
variable "db_password" {
  sensitive = true
}
```

값은 `.tfvars`로 분리하고 `.gitignore`에 포함한다. 10단계 보안 최적화에서 Secrets Manager로 발전시킨다.

#### NAT Gateway

이번 구성에서는 **필요 없다.** EC2가 퍼블릭에 있어 인터넷으로 패키지를 받을 수 있고, RDS에는 VPC 내부망으로 접근하기 때문이다.

NAT가 필요해지는 것은 EC2 자체를 프라이빗으로 옮길 때이며, 시간당 과금이 발생한다.

#### 비용

RDS는 EC2보다 비싸고 생성에 5\~10분이 걸린다. 한 세션 안에서 apply부터 destroy까지 끝낸다.

## 진행 과정

## A. 네트워크 및 RDS 코드 작성

### 목표

VPC부터 RDS까지 전체 구성을 Terraform 코드로 작성하고, `plan`으로 구조를 검증한다.

### 파일 지도

리소스 12개를 7개 파일에 나눠 적는다.

| 파일 | 한 줄 역할 |
| --- | --- |
| `provider.tf` | 어느 클라우드, 어느 리전에 만들지 |
| `network.tf` | 길을 깐다 — VPC, 서브넷 3개, IGW, 라우팅 |
| `security.tf` | 검문소를 세운다 — 보안 그룹 2개 |
| `variables.tf` / `terraform.tfvars` | 비밀번호를 코드 밖으로 뺀다 |
| `rds.tf` | DB를 프라이빗에 올린다 |
| `ec2.tf` | EC2를 퍼블릭 서브넷에 올린다 |
| `.gitignore` | Git에 올리면 안 되는 것을 막는다 |

### 1. 폴더와 파일 나누기

#### 폴더를 새로 판 이유

```bash
cd .../terraform
mkdir -p step7
cd step7
```

Terraform은 **폴더 단위로 state(장부)를 관리**한다. 폴더가 다르면 장부도 따로다.

- **얻는 것** — step7에서 `apply`나 `destroy`를 해도 step6 리소스는 건드려지지 않는다
- **치르는 대가** — step6에서 만든 리소스를 step7에서 참조할 수 없다. 그래서 7단계는 EC2도 처음부터 다시 작성한다

#### 파일을 나눈 이유

6단계는 `main.tf` 하나였다. 7단계는 리소스가 12개라 한 파일이면 스크롤만 하게 된다.

Terraform은 폴더 안의 모든 `.tf`를 **통째로 하나로 읽는다.** 어떻게 나누든 결과는 똑같고, 나누는 목적은 오직 **사람이 찾기 쉬우라고**다. 파일명이 곧 목차가 된다.

### 2. `provider.tf` — 어느 클라우드에 만들지

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-2"
}
```

- `source = "hashicorp/aws"` — AWS용 플러그인을 쓴다
- `version = "~> 5.0"` — 5.x 안에서만 올라간다. 6.0으로는 안 올라감. **버전을 묶지 않으면 나중에 `init`할 때 최신이 깔려 코드가 깨질 수 있다**
- `region = "ap-northeast-2"` — 서울

거의 고정 양식이라 매번 복붙해도 되는 파일이다.

### 3. `.gitignore` — 올리면 안 되는 것

```plain text
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
*.tfvars.json
crash.log
crash.*.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json
```

이 중 **이번 단계에서 진짜 중요한 건 두 줄**이다.

- `*.tfstate` — state에는 리소스 속성이 그대로 저장되고, **RDS 비밀번호도 평문으로 들어간다**
- `*.tfvars` — 이번에 DB 비밀번호를 적을 파일이 바로 이것이다

나머지는 캐시(`.terraform/`)나 크래시 로그라 올릴 이유가 없는 것들이다.

### 4. `network.tf` — 길 깔기

#### 구성

```plain text
VPC (10.0.0.0/16)
├── 퍼블릭 서브넷  10.0.1.0/24   AZ[0]  ← EC2
├── 프라이빗 A     10.0.11.0/24  AZ[0]  ← RDS
├── 프라이빗 B     10.0.12.0/24  AZ[1]  ← RDS(예비 자리)
├── IGW                                 ← 인터넷 출입구
└── 라우팅 테이블 (0.0.0.0/0 → IGW)     ← 퍼블릭 서브넷에만 연결
```

위에서 아래로 **점점 좁아진다.** 땅(VPC) → 대문(IGW) → 구역 나누기(서브넷) → 길 뚫기(라우팅).

#### AZ를 조회해서 쓴 이유

```hcl
data "aws_availability_zones" "available" {
  state = "available"
}
```

`data`는 **만들지 않고 조회만 한다.** 서울 리전에서 쓸 수 있는 AZ 목록을 AWS에 물어보고, `names[0]` `names[1]`로 순번을 지정해 쓴다.

`"ap-northeast-2a"`라고 직접 적어도 동작은 한다. 하지만 조회해서 쓰면 **리전만 바꿨도 코드가 그대로 돌아간다.** 리전마다 AZ 이름이 다르기 때문이다.

#### CIDR을 나눈 방식

VPC가 `/16`이라 앞 두 칸(`10.0`)이 고정되고, 세 번째 칸으로 구역을 구분했다. `1`번대는 퍼블릭, `11`·`12`번대는 프라이빗.

AWS 규칙이 아니라 **내가 정한 작명 규칙**이다. 서로 겹치지만 않으면 된다.

#### 프라이빗 서브넷이 2개인 이유

RDS는 **서로 다른 AZ의 서브넷 2개 이상**을 묶은 DB 서브넷 그룹을 요구한다. Single-AZ로 만들어도 강제된다.

나중에 Multi-AZ로 바꾸거나 장애 시 옮겨 띄울 자리를 미리 확보해 두라는 뜻이라, **프라이빗 B는 지금 비어 있는 예비 자리**다. 5단계에서 ALB가 서브넷 2개를 요구한 것과 같은 패턴이다.

#### 퍼블릭을 퍼블릭으로 만드는 것

```hcl
resource "aws_route_table" "public" {
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
```

"어디로 가든(`0.0.0.0/0`) IGW로 보내라"는 표를 만들고, `association`으로 **퍼블릭 서브넷에만 연결**했다. 붙이는 행위 자체가 하나의 리소스라 `plan`에서 따로 세어진다.

프라이빗 서브넷에는 연결하지 않았으므로 VPC 기본 라우팅 테이블에 붙는다. 거긴 IGW로 가는 길이 없어 **인터넷으로 나갈 수 없다.**

> 서브넷 자체에 퍼블릭/프라이빗 속성이 있는 것이 아니라, **라우팅 테이블 연결 여부가 둘을 가른다.**

#### 코드에 없는데 자동으로 생기는 규칙

라우팅 테이블에는 `10.0.0.0/16 → local` 규칙이 AWS에 의해 자동으로 들어간다. VPC 내부끼리는 IGW를 거치지 말고 바로 통신하라는 뜻이고, **EC2 → RDS 통신이 바로 이 규칙을 탄다.**

#### map_public_ip_on_launch

퍼블릭 서브넷에만 `true`를 넣었다. 이 서브넷에 생기는 EC2는 퍼블릭 IP를 자동으로 받는다. 프라이빗에는 이 줄이 없고 기본값이 `false`라 **RDS는 퍼블릭 IP를 받지 않는다.**

### 5. `security.tf` — 검문소 세우기

`network.tf`가 길을 깔았다면, `security.tf`는 그 길에 검문소를 세운다.

#### 먼저 알아야 할 3가지

1. **서브넷이 아니라 리소스에 붙는다.** 라우팅 테이블은 서브넷 단위였지만, 보안 그룹은 EC2·RDS 같은 개별 리소스에 붙는다. 같은 서브넷에 있어도 SG가 다르면 규칙이 다르다
2. **허용만 쓸 수 있다.** "막는 규칙"은 아예 문법이 없다. 적은 것만 열리고 나머지는 전부 닫힌다
3. **상태 저장(stateful).** 들여보낸 요청에 대한 응답은 자동으로 나간다. SSH 22를 ingress로 열면 서버의 응답은 egress에 적지 않아도 돌아온다. egress가 필요한 것은 서버가 **먼저 말을 걸 때**(`dnf install` 등)다

또 `from_port` / `to_port`는 포트 **범위**라, 하나만 열 때는 같은 숫자를 두 번 쓴다.

#### EC2 보안 그룹

```hcl
ingress {
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}
```

읽으면 **"어느 IP에서든 TCP 22번으로 오는 건 통과"**다.

`0.0.0.0/0`으로 열어둔 것은 실습 편의를 위한 **의도적 선택**이다. 실무라면 접속할 IP를 `x.x.x.x/32`로 좁힌다. 10단계 보안 최적화에서 손볼 지점이다.

#### egress — Terraform의 함정

콘솔에서 보안 그룹을 만들면 아웃바운드 "전체 허용"이 기본으로 붙는다. 그러나 Terraform의 `aws_security_group`은 `egress` 블록을 쓰지 않으면 **아웃바운드를 전부 제거한다.** 그러면 EC2가 패키지를 받지 못해 MySQL 클라이언트 설치도 안 된다. 그래서 보통 아래를 명시한다.

```hcl
egress {
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}
```

`0 / 0 / "-1"` = 모든 포트, 모든 프로토콜.

#### RDS 보안 그룹 — 이번 단계의 핵심

```hcl
ingress {
  description     = "MySQL from EC2 only"
  from_port       = 3306
  to_port         = 3306
  protocol        = "tcp"
  security_groups = [aws_security_group.ec2.id]
}
```

EC2 것과 비교하면 **마지막 줄만 다르다.**

```plain text
EC2 :  cidr_blocks     = ["0.0.0.0/0"]                  ← 주소로 거른다
RDS :  security_groups = [aws_security_group.ec2.id]   ← 신분으로 거른다
```

| 방식 | 무엇을 보나 | 비유하면 |
| --- | --- | --- |
| cidr_blocks | 어디서 왔나 (주소) | "3층 사무실에서 온 사람만 통과" |
| security_groups | 무엇을 달고 있나 (신분) | "사원증 단 사람만 통과" |

주소로 관리하면 이사 갈 때마다 명단을 고쳐야 하고, 신분으로 관리하면 어디 살든 상관없다. 즉 **특정 EC2 한 대가 아니라 그 그룹을 달고 있는 리소스 전부**가 허용된다. ASG로 10대가 떠도 규칙을 한 글자도 고치지 않는다.

참조 방향이 `RDS SG → EC2 SG` 한쪽뿐이라 순환이 생기지 않고, Terraform이 EC2 SG를 먼저 만든다.

4단계에서 배운 개념을 **서비스 계층 간 접근 제어**에 적용한 것이다.

### 6. `variables.tf` / `terraform.tfvars` — 비밀번호 빼내기

```hcl
variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}
```

`variable` 블록은 **"이런 변수가 있다"는 선언만** 한다. 값은 들어 있지 않다. 값은 `terraform.tfvars`에 따로 적고, 그 파일을 `.gitignore`로 제외한다. 즉 **선언은 Git에 올라가고 값만 빠진다.**

| 항목 | 역할 |
| --- | --- |
| `variables.tf` | 변수가 있다는 선언만. 값은 없음 → Git에 올려도 무방 |
| terraform.tfvars | 실제 값 → Git 제외 |
| sensitive = true | plan/apply 출력에서 값이 가려진다. 터미널을 캡처해도 비밀번호가 찍히지 않는다 |

코드에서는 `var.db_password` 형태로 가져다 쓴다. `default`가 있으면 값을 안 줘도 그게 쓰이므로, `db_username`은 tfvars에 안 적어도 되고 `db_password`는 default가 없어 반드시 줘야 한다.

다만 이게 완전한 방법은 아니다. tfvars 파일 자체는 내 디스크에 평문으로 남는다. 10단계에서 Secrets Manager로 발전시킨다.

### 7. `rds.tf` — DB 올리기

#### DB 서브넷 그룹

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "tf-step7-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}
```

프라이빗 서브넷 2개를 묶어 **"RDS는 이 안에서만 살아라"**를 지정한다.

#### RDS 인스턴스

| 설정 | 의미 |
| --- | --- |
| engine = "mysql" | DB 종류 |
| engine_version = "8.0" | 메이저 버전만 지정. 마이너 버전은 AWS가 기본값으로 채운다 |
| instance_class = "db.t3.micro" | DB 인스턴스 크기 |
| allocated_storage = 20 | 저장 공간 20GB |
| db_name = "portfolio" | 생성할 데이터베이스 이름 |
| publicly_accessible = false | 퍼블릭 IP를 부여하지 않는다. VPC 내부에서만 접근 가능 |
| skip_final_snapshot = true | destroy 시 최종 백업을 건너뛰고 바로 삭제한다 |

이 중 **이번 단계의 의도가 담긴 것은 두 줄**이다.

- `publicly_accessible = false` — 퍼블릭 IP를 안 받는다. 프라이빗 서브넷에 넣은 것과 합쳐 **두 겹으로 외부 접근을 막는다**
- `skip_final_snapshot` — 이름이 `skip_`이라 뜻이 반대로 읽힌다. 기본값 `false` = 건너뛰지 않음 = 스냅샷을 만든다 → 이때 스냅샷 이름이 없으면 에러가 나 **destroy가 실패**한다. 실습이라 `true`로 둔 것

#### RDS를 쓴 이유

지금까지는 Nginx로 HTML 파일만 보여줬지만, 실제 서비스는 회원·게시글·주문 같은 데이터를 저장해야 한다.

EC2에 MySQL을 직접 설치할 수도 있지만, 그러면 백업·패치·장애 복구를 직접 해야 한다. RDS는 그 관리 업무를 AWS에 맡기는 **관리형(managed) 서비스**다.

### 8. `ec2.tf` — 6단계에서 한 줄 추가

6단계 EC2 코드와 거의 같고 이 한 줄이 늘었다.

```hcl
subnet_id = aws_subnet.public.id
```

6단계는 기본 VPC에 자동으로 들어갔지만, 이번에는 **직접 만든 퍼블릭 서브넷**을 지정한다.

### init

```bash
terraform init
```

새 폴더라 provider를 처음부터 받는다. step6은 lock 파일이 있어 `Reusing`이 떴지만, 여기서는 `Finding ... versions matching`으로 시작한다.

<!-- 이미지: terraform init 실행 결과 터미널 화면 (provider를 새로 받는 출력) -->

### plan

```bash
terraform plan
```

결과: `Plan: 12 to add, 0 to change, 0 to destroy.`

| 리소스 | 개수 |
| --- | --- |
| VPC | 1 |
| IGW | 1 |
| 서브넷 | 3 |
| 라우팅 테이블 | 1 |
| 라우팅 연결 | 1 |
| 보안 그룹 | 2 |
| DB 서브넷 그룹 | 1 |
| RDS | 1 |
| EC2 | 1 |

AZ 조회와 AMI 조회 같은 `data` 블록은 **만드는 것이 아니라 조회**라 이 12개에 세어지지 않는다.

#### 확인한 것

- `availability_zone = "ap-northeast-2a"` — `data.aws_availability_zones` 조회 결과가 실제 값으로 채워졌다
- `map_public_ip_on_launch = true` — 퍼블릭 서브넷에만 적용된다
- `vpc_id = (known after apply)` — VPC가 아직 없어 ID를 모른다. 참조 관계상 VPC가 가장 먼저 생성된다
- **비밀번호가 출력 어디에도 보이지 않는다** — `sensitive = true` 적용 확인

<!-- 이미지: terraform plan 결과 터미널 화면 (Plan: 12 to add, 비밀번호가 가려진 출력) -->

## B. 배포 및 접속 검증

### 목표

작성한 코드를 실제로 배포하고, **외부에서는 차단 / EC2에서는 접속 성공**을 실제 결과로 검증한다.

#### 진행 흐름

```plain text
apply → 검증① 외부에서 접속(실패해야 정상)
     → 검증② EC2에서 접속(성공해야 정상)
     → 데이터 입력·조회 → destroy
```

한 쪽만 보여주면 "설정했다"에 그친다. **둘을 대조**해야 차단이 실제로 동작한다는 증명이 된다.

### 1. apply — 실제로 만들기

```bash
terraform apply
```

결과: `Apply complete! Resources: 12 added, 0 changed, 0 destroyed.`

```plain text
ec2_public_ip = "<퍼블릭 IP>"
rds_endpoint  = "<RDS 엔드포인트>:3306"
```

RDS는 IP가 아니라 **도메인 형태의 엔드포인트**를 받는다.

#### 생성 순서

```plain text
① VPC (12s)
     ↓  나머지가 전부 aws_vpc.main.id를 참조하므로 가장 먼저
② IGW, 서브넷 3개, EC2 보안그룹   ← 동시에 진행
     ↓
③ 라우팅 테이블, DB 서브넷 그룹, RDS 보안그룹
     ↓
④ 라우팅 연결(association), RDS (5m 7s), EC2 (13s)
```

**서로 참조 관계가 없는 것들은 동시에 생성된다.** 서브넷 3개가 한꺼번에 `Creating...`으로 뜬 것이 그 예다.

RDS는 5분 7초, EC2는 13초가 걸렸다. RDS는 실제 DB 엔진을 설치·초기화하는 과정이 포함되기 때문이다.

<!-- 이미지: terraform apply 결과 터미널 화면 (Apply complete! Resources: 12 added와 output) -->

### 2. 검증 ① 외부에서 접속 — 실패해야 정상

내 노트북에서 RDS 엔드포인트로 연결을 시도했다.

```bash
nc -zv -w 5 <RDS 엔드포인트> 3306
```

결과:

```plain text
nc: connectx to ... port 3306 (tcp) failed: Operation timed out
```

`nc`는 해당 포트가 열려 있는지만 두드려보는 도구다. 응답이 **어떻게 실패하느냐**가 진단의 핵심이다.

| 응답 | 의미 |
| --- | --- |
| Connection refused | 서버까지 도달했으나 거절당함 |
| Operation timed out | **서버까지 아예 도달하지 못함** |

`timed out`이 나온 경로는 이렇다.

1. 노트북이 RDS 엔드포인트를 DNS로 조회한다
2. `publicly_accessible = false`이므로 **프라이빗 IP(10.0.x.x)** 가 돌아온다
3. 프라이빗 IP는 인터넷에서 라우팅되지 않아 패킷이 어디에도 도달하지 못한다
4. 응답 자체가 없으므로 거절(refused)이 아니라 시간 초과(timed out)가 난다

3단계 장애 진단에서 본 차이와 같다.

<!-- 이미지: 노트북에서 nc로 RDS 3306 접속 시도 시 Operation timed out 결과 터미널 화면 -->

### 3. 검증 ② EC2에서 접속 — 성공해야 정상

#### EC2 접속

AWS 콘솔 → EC2 → 인스턴스 → 연결 → EC2 Instance Connect

프롬프트가 `[ec2-user@<내부 IP> ~]$`로 떴다. **코드에서 지정한 퍼블릭 서브넷(10.0.1.0/24) 범위 안의 주소**다.

#### MySQL 클라이언트 설치

```bash
sudo dnf install -y mariadb105
```

Amazon Linux 2023 기본 저장소에는 MySQL 클라이언트가 없어 MariaDB 클라이언트를 설치한다. MySQL과 호환된다.

`dnf`는 `yum`의 후속 버전으로, Amazon Linux 2023부터 사용한다.

#### RDS 접속

```bash
mysql -h <RDS 엔드포인트> -u admin -p
```

결과:

```plain text
Welcome to the MariaDB monitor.
Your MySQL connection id is 37
Server version: 8.0.46 Source distribution

MySQL [(none)]>
```

코드에는 `engine_version = "8.0"`으로 **메이저 버전만** 지정했고, 마이너 버전(`.46`)은 AWS가 당시 기본값으로 채운 것이다. 마이너까지 고정하지 않으면 이후 apply 시점에 버전이 올라가 코드와 실제 상태가 어긋날 수 있다.

<!-- 이미지: EC2 Instance Connect에서 mysql로 RDS 접속에 성공한 화면 -->

#### 검증 결과 정리

| 위치 | 결과 |
| --- | --- |
| 내 노트북 → RDS | Operation timed out (차단) |
| EC2 → RDS | 접속 성공 |

보안 그룹 참조(`security_groups = [aws_security_group.ec2.id]`)와 `publicly_accessible = false`가 실제로 작동한 것이 확인됐다.

설정했다는 것보다 **실제 결과로 둘을 대조해 보여주는 것**이 이번 단계의 핵심이다.

### 4. 데이터 입력 및 조회

```sql
SHOW DATABASES;
```

목록에 `portfolio`가 보인다. 코드의 `db_name = "portfolio"`가 실물로 만들어진 것이다.

```sql
USE portfolio;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50),
  email VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES ('lee', 'test@example.com');
INSERT INTO users (name, email) VALUES ('kim', 'kim@example.com');

SELECT * FROM users;
```

결과:

```plain text
+----+------+------------------+---------------------+
| id | name | email            | created_at          |
+----+------+------------------+---------------------+
|  1 | lee  | test@example.com | 2026-08-27 05:21:46 |
|  2 | kim  | kim@example.com  | 2026-08-27 05:21:49 |
+----+------+------------------+---------------------+
```

#### 접속 확인에서 멈추지 않은 이유

`mysql -h endpoint` 접속 성공만으로는 "네트워크 경로가 열려 있다"까지만 확인한 것이다.

CREATE → INSERT → SELECT까지 가야 **DB가 실제 데이터를 저장하고 반환한다**는 것이 증명된다. 8단계에서 앱을 붙일 때 이 구조가 그대로 이어진다.

<!-- 이미지: RDS에서 CREATE TABLE·INSERT 후 SELECT 결과가 출력된 화면 -->

### 5. destroy — 정리

```bash
terraform destroy
```

결과: `Destroy complete! Resources: 12 destroyed.`

#### 삭제 순서

```plain text
RDS · EC2 · 라우팅 연결
     ↓
IGW · 서브넷 · DB 서브넷 그룹
     ↓
보안 그룹
     ↓
VPC   ← 가장 마지막
```

생성의 역순이다. 참조하는 쪽을 먼저 지워야 참조당하는 쪽을 지울 수 있기 때문이고, 그래서 VPC가 가장 마지막이다.

#### skip_final_snapshot

RDS 삭제에 1분 51초가 걸렸다. `skip_final_snapshot = true`로 두었기 때문에 최종 백업 없이 바로 삭제됐다.

이 설정이 없었다면 기본값이 `false`이므로 최종 스냅샷 이름을 요구하며 삭제가 실패한다.

<!-- 이미지: terraform destroy 결과 터미널 화면 (Destroy complete! Resources: 12 destroyed) -->

## 7단계 용어

7단계에서 새로 나온 개념과 명령어. **진행 순서대로** 정리했다.

### 프로젝트 구성

| 용어 | 한 줄 설명 |
| --- | --- |
| 파일 분리 | Terraform은 폴더 안 모든 `.tf`를 하나로 읽는다. 역할별로 나누어도 결과는 같으며 사람이 보기 편해진다 |
| state의 폴더 단위 관리 | 폴더가 다르면 state도 별개다. 다른 폴더의 리소스는 참조할 수 없고, 영향도 받지 않는다 |

### 네트워크

| 용어 | 한 줄 설명 |
| --- | --- |
| aws_vpc | VPC를 생성하는 리소스. `cidr_block`으로 전체 주소 범위를 지정한다 |
| enable_dns_support | VPC 안에서 DNS 질의를 해석할 수 있게 한다. false면 이름 자체가 IP로 풀리지 않는다 |
| enable_dns_hostnames | VPC 내 리소스에 DNS 이름을 부여할지 여부. RDS 엔드포인트를 쓰려면 이 둘이 모두 true여야 한다 |
| aws_subnet | VPC 안에 서브넷을 만드는 리소스 |
| map_public_ip_on_launch | 해당 서브넷에 생성되는 인스턴스에 퍼블릭 IP를 자동 부여할지 여부 |
| aws_internet_gateway | VPC와 인터넷을 연결하는 출입구 |
| aws_route_table | 목적지별로 트래픽을 어디로 보낼지 정하는 규칙표 |
| aws_route_table_association | 라우팅 테이블을 특정 서브넷에 연결하는 작업 |
| data "aws_availability_zones" | 현재 리전의 가용 영역 목록을 조회. `names[0]`, `names[1]` 형태로 순번을 지정해 쓴다 |

**퍼블릭/프라이빗을 가르는 것은 서브넷 속성이 아니라 라우팅 테이블 연결 여부다.** `0.0.0.0/0 → IGW` 규칙이 연결된 서브넷만 퍼블릭이 된다.

### 보안 그룹

| 용어 | 한 줄 설명 |
| --- | --- |
| aws_security_group | 리소스 하나하나에 붙는 방화벽. 서브넷이 아니라 EC2·RDS 같은 개별 리소스 단위로 적용된다. 같은 서브넷에 있어도 SG가 다르면 규칙이 다르다 |
| 화이트리스트 방식 | 허용 규칙만 쓸 수 있다. 적지 않은 것은 전부 차단된다. "막는 규칙"은 존재하지 않는다 |
| ingress / egress | 인바운드(밖 → 나) / 아웃바운드(나 → 밖) |
| 상태 저장(stateful) | 들여보낸 요청에 대한 응답은 자동으로 나간다. ingress만 열어도 응답은 egress 규칙 없이 돌아온다. egress가 필요한 것은 서버가 먼저 말을 걸 때(dnf install 등)다 |
| from_port / to_port | 포트 범위를 지정한다. 하나만 열 때는 같은 숫자를 두 번 쓴다 |
| protocol | "tcp", "udp", "icmp" 또는 "-1"(전체 프로토콜) |
| egress 기본값 주의 | Terraform의 aws_security_group은 egress를 명시하지 않으면 아웃바운드를 전부 제거한다. 콘솔에서 만들 때의 기본값(전체 허용)과 다르다 |

#### 허용 대상 지정 방식

| 방식 | 의미 |
| --- | --- |
| cidr_blocks | 특정 IP 범위에서 오는 것만 허용 |
| security_groups | 해당 보안 그룹에 속한 리소스만 허용. IP를 몰라도 되고 대상이 늘어나도 규칙을 안 고쳐도 된다 |

### 변수

| 용어 | 한 줄 설명 |
| --- | --- |
| variable 블록 | 외부에서 값을 받을 변수를 선언. 선언만 있으며 값은 들어있지 않다 |
| terraform.tfvars | 변수의 실제 값을 담는 파일. Git에서 제외한다 |
| sensitive = true | plan/apply 출력에서 값을 가린다. 터미널 캡처 시 비밀번호가 노출되지 않는다 |
| var.변수명 | 코드에서 변수를 가져다 쓰는 방법. 예: `var.db_password` |
| default | 변수에 값이 주어지지 않았을 때 쓰일 기본값 |

### 데이터베이스

| 용어 | 한 줄 설명 |
| --- | --- |
| 데이터베이스(DB) | 회원·게시글·주문 같은 데이터를 저장하는 곳. MySQL, PostgreSQL 등이 DB 프로그램이다 |
| RDS | AWS가 설치·백업·패치·복구를 대신 해주는 관리형(managed) 데이터베이스 서비스 |
| 관리형(managed) 서비스 | 운영·유지보수를 클라우드 제공자가 대신 맡아주는 방식 |
| 3306 | MySQL 기본 포트 번호 |
| aws_db_subnet_group | RDS가 사용할 서브넷들을 묶은 것. 서로 다른 최소 2개 AZ의 서브넷이 필요하다 |
| aws_db_instance | RDS 인스턴스를 생성하는 리소스 |
| db.t3.micro | RDS용 인스턴스 타입. EC2의 t3.micro와 유사한 크기 |
| allocated_storage | 할당할 저장 공간(GB) |
| publicly_accessible | false면 퍼블릭 IP를 부여하지 않아 VPC 내부에서만 접근할 수 있다 |
| skip_final_snapshot | destroy 시 최종 백업을 **건너뛸지** 여부. 이름이 skip_이므로 뜻이 반대로 읽히기 쉽다. 기본값 false = 건너뛰지 않음 = 스냅샷을 만든다 → 이때 이름(final_snapshot_identifier)이 없으면 에러가 나서 삭제가 막힌다. true면 백업 없이 바로 삭제된다 |
| endpoint | RDS에 접속할 때 쓰는 주소. 생성 후 AWS가 부여한다 |

### 구조 개념

| 용어 | 한 줄 설명 |
| --- | --- |
| 계층 분리 | 외부에 노출해야 하는 것(EC2)과 감춰야 하는 것(RDS)을 서브넷으로 나누는 설계 |
| NAT Gateway | 프라이빗 서브넷의 리소스가 인터넷으로 나갈 수 있게 해주는 것. 이번 구성에서는 EC2가 퍼블릭에 있어 필요 없다. 시간당 과금된다 |

## 배운 점

### A 네트워크 및 RDS 코드 작성

- 6단계 terraform 에서는 하나의 코드에서 해결했지만 7단계에선 역할 별로 코드를 나누었다.
    1. provider.tf
        1. 버전 범위 및 리전 위치

        ```hcl
        terraform {
          required_providers {
            aws = {
              source  = "hashicorp/aws"
              version = "~> 5.0"
            }
          }
        }

        provider "aws" {
          region = "ap-northeast-2"
        }
        ```

    2. network.tf
        1. 가용 영역 목록 조회 (data)
            1. 리소스 타입 : aws_availability_zones
            2. 이름 : available
            3. 조회 조건 : state = available (사용 가능한 AZ만)
        2. VPC (resource) —> AWS 안에 내 네트워크 공간 생성
            1. 리소스 타입 : aws_vpc
            2. 이름 : main (vpc 내에서 main)
            3. 코드 해석
                1. cidr_block → VPC가 쓸 범위 10.0.0.0/16 —> 10.0.255.255 까지 사용가능 (내가 IP 쓸 범위, /16→ 앞 16비트 고정, 뒤 16비트 자유)
                2. enable_dns_support → VPC 안에서 도메인 이름을 IP로 바꿀 수 있게 함.
                3. enable_dns_hostnames → 리소스에 DNS 이름 부여.
                4. tags = aws console 에 표시될 이름
            4. VPC → public subnet / private subnet a,b / IGW / routing table
        3. IGW (resource) —> VPC와 인터넷을 연결 시키는 출입구
            1. 리소스 타입 : aws_internet_gateway
            2. 이름 : main
            3. vpc_id : VPC에 id참조해서 대입 —> 이 줄 때문에 VPC가 먼저 만들어지고 IGW가 나중에 만들어짐 (의존 관계)
        4. Public Subnet → VPC를 구역으로 쪼갠 것 (VPC범위 내, 겹치면 안 됨)
            1. vpc_id : vpc 참조 후 id 작성
            2. cidr_block : 10.0.0.0/16 중 10.0.1.0/24만 사용 (앞 24비트 고정, 뒤 8비트만 사용)
            3. availability_zone → 가용 영역 목록 조회하는 곳과 의존관계. 서브넷이 AZ를 걸칠 수 없어 하나에만 속함.
            4. map_public_ip_on_launch : 여기 뜨는 EC2는 자동으로 퍼블릭 IP를 받음
        5. Private Subnet A/B (map_public_ip_on_launch 줄 X)
            1. cidr_block : 세 번째 칸으로 서로 구분 (A : 11 , B : 12)
            2. availability_zone → 가능한지 검사
            3. RDS는 DB 서브넷 그룹에 서로 다른 AZ 서브넷 2개 이상을 요구한다.
        6. Routing table (나가는 패킷을 어디로 보내는지 적어둔 표)
            1. route 블록
                1. cidr_block : 목적지가 0.0.0.0/0 (=전부) 라면
                2. gateway : IGW로 보내라
        7. association
            1. 만든 표를 public subnet에 붙임.
                - AWS에서는 붙이는 행위 자체가 리소스기 때문이다.
                - private subnet a/b는 association을 안 만듦
                    - VPC 만들 때 만들어지는 기본 라우팅 테이블이 자동으로 붙음 —> local만 존재, IGW로 나가는 길이 없어 인터넷으로 나갈 길이 없음 —> private)

        ```hcl
        # 가용 영역 목록 조회
        data "aws_availability_zones" "available" {
          state = "available"
        }

        # VPC
        resource "aws_vpc" "main" {
          cidr_block           = "10.0.0.0/16"
          enable_dns_support   = true
          enable_dns_hostnames = true

          tags = {
            Name = "tf-step7-vpc"
          }
        }

        # 인터넷 게이트웨이
        resource "aws_internet_gateway" "main" {
          vpc_id = aws_vpc.main.id

          tags = {
            Name = "tf-step7-igw"
          }
        }

        # 퍼블릭 서브넷 (EC2용)
        resource "aws_subnet" "public" {
          vpc_id                  = aws_vpc.main.id
          cidr_block              = "10.0.1.0/24"
          availability_zone       = data.aws_availability_zones.available.names[0]
          map_public_ip_on_launch = true

          tags = {
            Name = "tf-step7-public"
          }
        }

        # 프라이빗 서브넷 A (RDS용)
        resource "aws_subnet" "private_a" {
          vpc_id            = aws_vpc.main.id
          cidr_block        = "10.0.11.0/24"
          availability_zone = data.aws_availability_zones.available.names[0]

          tags = {
            Name = "tf-step7-private-a"
          }
        }

        # 프라이빗 서브넷 B (RDS용, 다른 AZ)
        resource "aws_subnet" "private_b" {
          vpc_id            = aws_vpc.main.id
          cidr_block        = "10.0.12.0/24"
          availability_zone = data.aws_availability_zones.available.names[1]

          tags = {
            Name = "tf-step7-private-b"
          }
        }

        # 퍼블릭 라우팅 테이블
        resource "aws_route_table" "public" {
          vpc_id = aws_vpc.main.id

          route {
            cidr_block = "0.0.0.0/0"
            gateway_id = aws_internet_gateway.main.id
          }

          tags = {
            Name = "tf-step7-public-rt"
          }
        }

        # 퍼블릭 서브넷에 라우팅 테이블 연결
        resource "aws_route_table_association" "public" {
          subnet_id      = aws_subnet.public.id
          route_table_id = aws_route_table.public.id
        }
        ```

    3. security.tf
        1. 보안그룹이란?
            1. 리소스 하나하나에 붙는 개인 경비원
                - EX ) subnet - Routing table / EC2 - 보안 그룹
            2. 규칙
                1. ingress : 인바운드 (밖에서 안으로)
                2. egress : 아웃바운드 (내가 밖으로)
            3. EC2에서는?
                1. ingress : from_port , to_port , protocol , cidr_blocks
                2. cidr_blocks = 0.0.0.0/0 ⇒ 모든 IP 허용
        2. RDS security
            1. security_groups
                - ec2 에선 cidr_blocks로 모든 IP 허용
                - RDS는 EC2 보안 그룹 달고 있는 친구로 허용

        ```hcl
        resource "aws_security_group" "ec2" {
          vpc_id = aws_vpc.main.id

          ingress {
            from_port   = 22
            to_port     = 22
            protocol    = "tcp"
            cidr_blocks = ["0.0.0.0/0"]
          }
        }
        ```

    4. variables.tf
        1. 값이 있다 라고 하는 것만 선언.
            1. 실제 값은 terraform.tfvars 에 작성
            2. 선언은 git에 올라가고 값만 빠짐
        2. description : 설명
        3. type : 문자열만 (string, list, number, bool …)
        4. sensitive : 화면에서 가리기
            - 없을 때 plan 실행 시 (db_username에는 없고 default값 존재)
                - \+ password = "<DB 비밀번호>"
            - 있을 때 plan 실행 시 (db_password에는 default값 존재 X)
                - \+ password = (sensitive value)

    ```hcl
    variable "db_username" {
      description = "RDS master username"
      type        = string
      default     = "admin"
    }

    variable "db_password" {
      description = "RDS master password"
      type        = string
      sensitive   = true
    }
    ```

    1. rds.tf
        1. RDS → 운영 업무를 돈 주고 AWS에게 맡기는 것 (관리형 서비스)
            1. 백업, 보안패치, 장애 복구, 설치를 AWS가 자동으로 해줌, OS 레벨은 접근이 힘듦
            2. EC2에서 MySQL 직접 설치시 다 본인이 해야함
            3. 가격은 RDS 비싸고 MySQL은 저렴
        2. aws_db_subnet_group (RDS가 있을 그룹)
            1. RDS는 subnet을 직접 고르지 못 하므로 서브넷 묶음을 먼저 만들고 지정
            2. private_a.id , private_b.id (이 둘 중에서만 살기)
                - subnet을 두 개 만든 이유
        3. aws_db_instance (RDS 인스턴스)
            1. DB
                1. engine : MYSQL
                2. engine_version : 버전 지정
            2. 크기
                1. instance_class : DB 서버의 스펙
                2. allocated_storage : 디스크 크기
            3. 안에 만드는 정보
                1. db_name :  DB 서버 안에 만들 데베 이름
                2. username, password : DB 마스터 계정 아이디, 비밀번호 (내가 SQL로 만드는 정보)
                    1. var. 으로 가져옴
                3. db_subnet_group_name : 위치
                4. vpc_security_group_ids : RDS 보안그룹 지정 (security.tf)
            4. publicly_accessible = false
                1. public IP를 안 줌. —> 인터넷에서 이 DB의 주소 자체가 향하지 않음
                    1. private subnet + publicly_accessible + 보안그룹 세 겹의 방어 체제
            5. skip_final_snapshot = true
                1. 건너뛸지의 여부 —> 건너뛰면 백업 없이 바로 삭제

    ```hcl
    # =====================================
    # rds.tf
    # =====================================

    # ① DB 서브넷 그룹 — RDS가 살 수 있는 범위
    resource "aws_db_subnet_group" "main" {
      name       = "tf-step7-db-subnet-group"
      subnet_ids = [
        aws_subnet.private_a.id,   # AZ[0]
        aws_subnet.private_b.id,   # AZ[1]  ← 서로 다른 AZ 2개 필수
      ]

      tags = {
        Name = "tf-step7-db-subnet-group"
      }
    }


    # ② RDS 인스턴스
    resource "aws_db_instance" "main" {
      identifier = "tf-step7-mysql"          # AWS 콘솔에 표시될 이름

      # --- 어떤 DB인가 ---
      engine         = "mysql"
      engine_version = "8.0"                 # 메이저만 지정, 마이너는 AWS가 채움

      # --- 얼마나 큰가 ---
      instance_class    = "db.t3.micro"      # EC2 t3.micro급. 앞에 db. 붙음
      allocated_storage = 20                 # 20GB

      # --- 안에 뭘 만드는가 ---
      db_name  = "portfolio"                 # 생성될 데이터베이스 이름
      username = var.db_username             # variables.tf에서
      password = var.db_password             # terraform.tfvars에서 (sensitive)

      # --- 어디에 두는가 ---
      db_subnet_group_name   = aws_db_subnet_group.main.name   # ①번 참조
      vpc_security_group_ids = [aws_security_group.rds.id]     # security.tf 참조
      publicly_accessible    = false                           # 퍼블릭 IP 없음

      # --- 삭제 정책 ---
      skip_final_snapshot = true             # 최종 스냅샷 건너뛰고 바로 삭제

      tags = {
        Name = "tf-step7-mysql"
      }
    }


    # ③ 출력 — apply 후 터미널에 표시
    output "rds_endpoint" {
      value = "${aws_db_instance.main.endpoint}"
    }
    ```

    1. ec2.tf
        1. EC2의 역할 —> RDS에 접속하는 통로
            1. 6단계에선 웹 서버였음
        2. AMI 조회
            1. 6이랑 동일
            2. 최신 버전, amazon 버전 사용, 이름 패턴이 al2023-ami\~\~ 인 것
            3. apply 하기 전 data로 조회하면 apply 하는 시점에서 최신 AMI를 가져옴
        3. EC2 본체
            1. 위 조회한 결과의 ami 사용
            2. subnet_id
                1. 6단계에선 서브넷 안 적고 AWS가 만든 기본 VPC의 아무 서브넷 사용
                2. 지금은 내가 VPC를 만들었으니 직접 사용 (network.tf에 만든 public subnet 사용)
            3. 보안그룹
                1. vpc_security_group_ids 사용

        ```hcl
        # =====================================
        # ec2.tf
        # =====================================

        # ① 최신 Amazon Linux 2023 AMI 조회
        data "aws_ami" "amazon_linux" {
          most_recent = true
          owners      = ["amazon"]

          filter {
            name   = "name"
            values = ["al2023-ami-*-x86_64"]
          }
        }


        # ② EC2 인스턴스
        resource "aws_instance" "main" {
          ami           = data.aws_ami.amazon_linux.id
          instance_type = "t3.micro"

          subnet_id              = aws_subnet.public.id            # ← 7단계에서 추가된 줄
          vpc_security_group_ids = [aws_security_group.ec2.id]

          tags = {
            Name = "tf-step7-ec2"
          }
        }


        # ③ 출력
        output "ec2_public_ip" {
          value = aws_instance.main.public_ip
        }
        ```

- init
    - network.tf : 7개 (VPC, IGW, 서브넷 3, 라우팅 테이블 , association)
    - security.tf : 2개 (보안그룹 2개)
    - rds.tf : 2개 (DB 서브넷 그룹 , RDS )
    - ec2.tf : 1개 (EC2)
- plan

### B 배포 및 접속 검증

- apply 후 생성 순서 (Terraform이 스스로 결정)
    1. VPC
    2. IGW , 서브넷 3개, EC2 보안그룹
    3. 라우팅 테이블, DB 서브넷 그룹, RDS 보안 그룹
    4. 라우팅 연결, RDS, EC2
- EC2 VS RDS 비교
    - EC2 : AMI 복사 후 부팅
    - RDS : 서버 띄움 + MySQL 엔진 설치 + 초기화 + 백업 설정 + 파라미터 그룹 적용
- 검증 설계
    1. 외부에서 접속
        1. 터미널에서 입력
            1. nc : netcat → 이 주소의 포트가 열려있는지 확인
            2. -z : 데이터를 안 보내고 연결만 시도
            3. -v : 결과 자세히 출력
            4. -w 5 : 5초 기다리고 포기

        ```bash
        nc -zv -w 5 <RDS 엔드포인트> 3306
        ```

        —> timed out : 돌아오는 IP가 private IP

    2. EC2에서 접속
        1. EC2 인스턴스에 EC2 Instance Connect 접속
            1. `[ec2-user@<내부 IP> ~]$` —> 10.0.1.0/24 범위 안

        ```bash
        sudo dnf install -y mariadb105
        ```

        —> MySQL 클라이언트 설치
        아마존 리눅스는 yum이 아니라 dnf 사용

        ```bash
        mysql -h <RDS 엔드포인트> -u admin -p
        ```

        —> EC2 에서 RDS 접속 성공

    3. 데이터 입력 및 조회

        ```sql
        SHOW DATABASES;
        ```

        ```sql
        USE portfolio;

        CREATE TABLE users (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(50),
          email VARCHAR(100),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        INSERT INTO users (name, email) VALUES ('lee', 'test@example.com');
        SELECT * FROM users;
        ```

    4. 삭제

        ```sql
        terraform destroy
        ```

        —> 생성의 역순
