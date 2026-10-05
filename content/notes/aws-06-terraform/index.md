---
title: "AWS 6단계 · Terraform 자동화"
date: 2026-08-25
projects: ["aws-infra"]
step: 6
summary: "1~5단계에서 콘솔로 구축한 인프라를 Terraform 코드로 재작성하여, 명령어 한 줄로 생성·삭제할 수 있는 구조로 전환한다."
tags: ["IaC", "구축", "보안", "트러블슈팅"]
troubleshooting:
  - "액세스 키 노출"
  - "로컬 state로 인한 다중 기기 작업 제약"
draft: false
---

## 목표

1\~5단계에서 콘솔로 구축한 인프라를 Terraform 코드로 재작성하여, 명령어 한 줄로 생성·삭제할 수 있는 구조로 전환한다.

## 진행 과정

## A. Terraform 환경 구성 및 AWS 연결

### 상황

1\~5단계는 전부 AWS 콘솔에서 마우스로 클릭해 만들었다. 같은 구성을 다시 만들려면 수십 번의 클릭을 순서대로 반복해야 하고, 무엇을 어떤 값으로 설정했는지는 기억과 스크린샷에만 남는다.
Terraform은 인프라 구성을 코드 파일로 적어두고, 명령어 한 줄로 생성·삭제하는 도구다. A 구간에서는 실제 리소스를 만들기 전에 도구 설치와 AWS 연결까지만 확인한다.

### 설치 및 인증

#### 설치 확인

```javascript
terraform --version
```

- Terraform v1.15.8 (darwin_arm64)
- AWS CLI 2.36.16

#### IAM 사용자 준비

- 사용자명 `terraform-user`
- 권한 `AdministratorAccess` (실습용. 9단계 비용·보안 최적화에서 최소 권한으로 축소 예정)
- `aws configure`로 자격 증명 등록 — 리전 `ap-northeast-2`, 출력 형식 `json`

#### 연결 확인

```javascript
aws sts get-caller-identity
```

- Account / UserId / Arn 정상 출력 확인

### 작업 폴더 생성

```javascript
mkdir -p ~/terraform/step6
cd ~/terraform/step6
pwd
```

- 경로: `/Users/<사용자>/terraform/step6`

Terraform은 **현재 폴더에 있는 모든 `.tf` 파일**을 하나의 인프라 단위로 읽는다. 폴더가 곧 프로젝트의 경계이므로 단계별로 분리해서 작업한다.

### main.tf 작성

첫 파일은 의도적으로 **리소스를 하나도 생성하지 않는 코드**로 작성했다. AWS에 아무 영향을 주지 않는 상태에서 문법과 연결만 검증하기 위해서다.

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

data "aws_caller_identity" "current" {}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}
```

| 블록 | 역할 |
| --- | --- |
| terraform / required_providers | 사용할 provider와 버전 범위를 선언. `~> 5.0`은 5.x 중 최신을 의미 |
| provider "aws" | AWS 접속 설정. 리전을 서울로 지정 |
| data | 조회 전용. 생성하지 않고 기존 정보만 읽어온다. 조회할 대상 하나당 블록 하나를 작성한다 |
| output | apply 완료 후 화면에 출력할 값 |

이 코드에는 `resource` 블록이 없다. Terraform에서 실제로 무언가를 생성하는 것은 `resource`뿐이며, `data`는 읽기만 한다.

### init → plan → apply

#### terraform init

```javascript
terraform init
```

- 코드에 선언한 provider 플러그인을 실제로 내려받는 단계
- `hashicorp/aws v5.100.0` 설치됨
- `.terraform/` 디렉토리와 `.terraform.lock.hcl` 생성
- `Terraform has been successfully initialized!` 확인

<!-- 이미지: terraform init 실행 결과 (hashicorp/aws v5.100.0 설치, successfully initialized) -->

#### terraform plan

```javascript
terraform plan
```

- **적용하면 무엇이 어떻게 바뀌는지 미리 보여주는 단계.** AWS에는 아무 변경도 가하지 않는다
- 출력: `Changes to Outputs: + account_id = "<계정 ID>"`
- `without changing any real infrastructure` — 실제 인프라 변경 없음을 Terraform이 명시
- 리소스를 생성하는 코드였다면 `Plan: n to add, ...` 형태로 표시된다

##### 실행 순서

plan은 **data를 먼저 처리하고 그 다음 resource를 계산**한다. resource가 data 결과를 참조하므로, 조회값을 모르면 무엇을 만들지 계산할 수 없기 때문이다.

| 블록 | plan 때 동작 |
| --- | --- |
| data | **실제로 AWS에 조회한다.** 읽기만 하므로 안전하며, 그래서 조회 결과가 실제 값으로 찍힌다 |
| resource | **계산만 한다.** 실제로 만들지 않고 "이렇게 될 것"만 보여준다 |

이것이 plan이 AWS에 아무 변경을 주지 않는 이유다.

<!-- 이미지: terraform plan 실행 결과 (Changes to Outputs, without changing any real infrastructure) -->

#### terraform apply

```javascript
terraform apply
```

- **코드대로 실제 리소스를 생성·변경·삭제한다.**
- 확인 프롬프트에 소문자 `yes` 입력
- 결과: `Apply complete! Resources: 0 added, 0 changed, 0 destroyed.`
- `terraform.tfstate` 생성됨

<!-- 이미지: terraform apply 실행 결과 (Resources: 0 added, 0 changed, 0 destroyed) -->

### 생성된 파일과 관리 기준

```javascript
ls -la
```

| 파일 | 역할 | Git 업로드 |
| --- | --- | --- |
| main.tf | 작성한 인프라 코드 | О |
| .terraform.lock.hcl | provider 버전 고정 파일 | О |
| .terraform/ | 내려받은 플러그인. init으로 재생성 가능 | X |
| terraform.tfstate | 생성한 리소스의 기록(장부) | X — 절대 금지 |

`.` 으로 시작하는 파일은 숨김 파일이다. 평소에는 보이지 않으며 `ls -la`의 `-a` 옵션을 붙여야 나타난다. 설정 파일이나 도구가 자동으로 생성하는 파일을 숨겨두는 관례다.
Git 업로드 기준은 "다른 사람이 이 코드를 받아 동일하게 재현할 수 있는가"이다. `.terraform/`은 용량이 크고 `init`으로 다시 받을 수 있어 제외하고, `terraform.tfstate`는 리소스 속성이 평문으로 저장되므로 반드시 제외한다

#### tfstate를 올리면 안 되는 이유

state 파일에는 생성한 리소스의 식별자와 속성이 그대로 저장된다. RDS 비밀번호처럼 민감한 값도 평문으로 기록되므로 공개 저장소에 올라가면 그대로 노출된다.

#### state 파일이 로컬에만 있다는 것의 의미

Terraform은 `코드 ↔ state ↔ 실제 AWS` 세 가지를 비교해 차이만큼만 작업한다. state가 없는 다른 컴퓨터에서 같은 코드로 apply하면 "아직 아무것도 만들지 않았다"고 판단해 **리소스를 중복 생성**한다. 6단계는 한 대의 장비에서만 진행한다.

### .gitignore 작성

```javascript
# Terraform 플러그인 디렉토리
.terraform/

# state 파일 - 민감 정보 포함. 절대 커밋 금지
*.tfstate
*.tfstate.*
*.tfstate.backup

# 변수 파일 - 키나 비밀번호가 들어갈 수 있음
*.tfvars
*.tfvars.json

# 크래시 로그
crash.log
crash.*.log

# 로컬 재정의 파일
override.tf
override.tf.json
*_override.tf
*_override.tf.json
```

`.terraform.lock.hcl`은 의도적으로 제외했다. 이 파일은 provider 버전을 고정하는 역할이므로 오히려 저장소에 포함해야 한다.

## B. 첫 리소스 생성 및 삭제

### 목표

`resource` 블록을 사용해 AWS에 실제 리소스를 생성하고, 콘솔에서 확인한 뒤 코드로 삭제하는 전체 사이클을 검증한다.

### data와 resource의 차이

A 구간에서 작성한 코드에는 `data` 블록만 있었기 때문에 apply 결과가 `0 added`였다.

| 블록 | 역할 |
| --- | --- |
| data | 조회 전용. 기존 정보를 읽기만 한다 |
| resource | 생성. AWS에 실제로 리소스를 만든다 |

Terraform에서 무언가를 생성하는 것은 `resource` 블록뿐이다.

### 작업 폴더 이전

작업 환경을 노트북과 데스크톱 양쪽에서 쓰기 위해 작업 폴더를 구글 드라이브 동기화 경로로 이동했다.

```javascript
mv ~/terraform/step6 <구글드라이브>/클라우드 포트폴리오/terraform/
rm -rf .terraform
terraform init
```

- `.terraform/`은 용량이 크고 `init`으로 재생성되므로 삭제 후 재설치했다
- 재설치 시 `Reusing previous version ... from the dependency lock file` 출력 — `.terraform.lock.hcl`이 provider 버전을 5.100.0으로 고정하고 있음을 확인

#### 로컬 state의 한계

state 파일은 "실제로 무엇을 만들었는가"의 기록이다. Terraform은 apply 시 `코드 ↔ state ↔ 실제 AWS`를 비교해 차이만큼만 작업한다.
state가 한 컴퓨터에만 있으면 다른 컴퓨터에서는 "아직 아무것도 만들지 않았다"고 판단해 리소스를 중복 생성한다. 키가 같아도 마찬가지다 — 키는 권한이고 state는 기록이므로 별개의 문제다.
구글 드라이브는 동기화에 시차가 있고 동시 작업을 막는 잠금 기능이 없다. 단시간 내에 두 기기를 번갈아 쓰지 않는 사용 패턴이라 현재는 감수하고, 추후 S3 원격 백엔드로 전환할 예정이다.
작업 전 확인 사항:

- 구글 드라이브 동기화가 완료된 상태에서 명령어 실행
- `terraform.tfstate (1)` 같은 충돌 파일이 생기면 작업 중단

### 보안 그룹 코드 작성

첫 리소스로 보안 그룹을 선택했다. 과금이 없고, 생성되어도 다른 리소스에 연결되지 않아 영향이 없기 때문이다.

```hcl
resource "aws_security_group" "web" {
  name        = "tf-web-sg"
  description = "Managed by Terraform"

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "tf-web-sg"
  }
}
```

| 항목 | 의미 |
| --- | --- |
| aws_security_group | 리소스 타입 |
| "web" | Terraform 내부에서만 쓰는 이름표. AWS에는 전달되지 않음 |
| ingress | 들어오는 트래픽. 80번 포트(HTTP) 개방 |
| egress | 나가는 트래픽. protocol "-1"은 모든 프로토콜을 의미 |
| 0.0.0.0/0 | 모든 IP |

#### 보안 그룹의 성질

| 성질 | 설명 |
| --- | --- |
| 기본은 전부 차단 | 허용 규칙을 적은 것만 통과한다. "막는 규칙"은 쓸 수 없고 "여는 규칙"만 있다 |
| 상태 저장(stateful) | 들어온 요청에 대한 응답은 자동으로 나갈 수 있다. 그래서 egress를 따로 손대지 않아도 웹이 동작한다 |
| 소스에 보안 그룹 지정 가능 | 허용 대상을 IP가 아니라 다른 보안 그룹으로 지정할 수 있다. 그 그룹에 속한 리소스가 자동으로 대상이 되므로, 서버가 늘어나도 규칙을 고치지 않아도 된다 (7단계 RDS에서 사용) |

#### 코드 입력 방식 — heredoc

```javascript
cat >> main.tf << 'EOF'
여러 줄 내용
EOF
```

| 기호 | 의미 |
| --- | --- |
| &gt; | 덮어쓰기. 기존 내용이 사라진다 |
| &gt;&gt; | 이어붙이기. 기존 코드 뒤에 추가된다 |
| &lt;&lt; | 여기서부터 입력을 받겠다는 표시 |
| 'EOF' | End Of File. 이 단어가 나오면 입력 종료. 다른 단어를 써도 동작하며 EOF는 관례다 |

따옴표로 감싸면(`'EOF'`) 내용 안의 `$` 같은 특수문자를 셀이 해석하지 않고 그대로 유지한다. Terraform 코드에는 `$`가 들어갈 수 있으므로 붙이는 것이 안전하다.
기존 코드를 유지해야 하므로 덮어쓰기(`>`)가 아닌 추가(`>>`)를 사용한다.

#### 이름표가 필요한 이유

```hcl
resource "aws_security_group" "web" {
```

앞의 `aws_security_group`은 **무엇을 만드는지**(리소스 타입), 뒤의 `"web"`은 **그것을 부를 이름**이다.
이름표는 AWS에 전달되지 않고 Terraform 내부에서만 쓰인다. AWS 콘솔에 보이는 이름은 블록 안의 `name`이나 `tags`로 지정한다.
이번 단계에서는 리소스가 하나뿐이라 이름표를 쓸 일이 없었다. **C 구간에서 EC2가 이 이름을 불러다 쓰면서** 이름표의 역할이 드러난다.

### plan

```javascript
terraform plan
```

결과: `Plan: 1 to add, 0 to change, 0 to destroy.`

- `+ create` 표시로 생성될 항목이 전부 출력된다
- `(known after apply)` — `arn`, `id`, `vpc_id`, `owner_id`는 AWS가 생성 시 부여하는 값이므로 아직 알 수 없다
- 직접 작성하지 않은 항목(`ipv6_cidr_blocks`, `self`, `prefix_list_ids` 등)도 함께 표시된다. Terraform이 기본값을 채운 것으로, 콘솔에서는 보이지 않던 설정까지 모두 드러난다

<!-- 이미지: 보안 그룹 terraform plan 결과 (Plan: 1 to add, known after apply 항목) -->

### apply

```javascript
terraform apply
```

결과:

```javascript
aws_security_group.web: Creating...
aws_security_group.web: Creation complete after 4s [id=sg-072c44e3272b4da8d]
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

plan에서 `(known after apply)`였던 ID가 실제 값으로 채워졌다.

<!-- 이미지: 보안 그룹 terraform apply 결과 (Resources: 1 added) -->

### 콘솔 확인

EC2 → 네트워크 및 보안 → 보안 그룹

| 코드 | 콘솔 |
| --- | --- |
| name = "tf-web-sg" | 보안 그룹 이름: tf-web-sg |
| description = "Managed by Terraform" | 설명: Managed by Terraform |
| from_port 80 / protocol tcp | 유형 HTTP, 프로토콜 TCP, 포트 80 |

VPC를 코드에 명시하지 않았지만 기본 VPC(`vpc-0a554abdad04c9620`)에 자동 생성됐다. plan에서 `vpc_id = (known after apply)`로 표시되던 부분이다.

<!-- 이미지: EC2 콘솔 보안 그룹 목록에서 tf-web-sg 생성 확인 -->

### destroy

```javascript
terraform destroy
```

결과: `Destroy complete! Resources: 1 destroyed.`

- `- destroy` 표시로 삭제될 항목을 먼저 보여준다
- 모든 속성이 `-> null`로 표시된다
- `There is no undo` 경고 — 되돌릴 수 없으므로 실행 전 반드시 내용을 확인해야 한다
- output도 함께 제거된다

삭제 후 콘솔에는 기존 보안 그룹 3개(`default`, `alb-sg`, `launch-wizard-1`)만 남았다. Terraform은 **자신의 state에 기록된 리소스만** 삭제하며, 콘솔로 만든 다른 리소스는 건드리지 않는다.

<!-- 이미지: terraform destroy 실행 결과 (Resources: 1 destroyed) -->
<!-- 이미지: 삭제 후 콘솔 보안 그룹 목록 (default, alb-sg, launch-wizard-1만 남음) -->

### 작업 사이클

```javascript
코드 작성 → plan → apply → 콘솔 확인 → destroy
```

Terraform 작업의 기본 단위이며, 이후 모든 리소스 작업에 동일하게 적용된다. 특히 `plan` 없이 `apply`하지 않는 것을 원칙으로 한다.

## C. EC2 코드화

### 목표

보안 그룹에 이어 EC2를 코드로 생성하고, 리소스 간 **참조**와 **의존성 자동 해결**을 확인한다.

### AMI 조회 (data)

AMI는 서버의 초기 이미지다. 1단계에서 콘솔로 EC2를 만들 때 "Amazon Linux"를 골랐던 그것이다.

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}
```

| 항목 | 의미 |
| --- | --- |
| owners = ["amazon"] | 아마존이 발행한 공식 이미지만 대상 |
| filter | 이름이 al2023-ami-\*-x86_64 패턴인 것 (Amazon Linux 2023) |
| most_recent = true | 조건에 맞는 것 중 최신 버전 |

#### AMI ID를 직접 쓰지 않는 이유

AMI ID(`ami-072139fac78f90345`)는 **리전마다 다르고, 이미지가 갱신될 때마다 바뀜다.** 코드에 고정해두면 시간이 지난 뒤 사용할 수 없거나 다른 리전에서 동작하지 않는다.
`data`로 조회하면 apply 시점의 최신 이미지를 자동으로 찾아서 쓴다.

#### data 블록은 조회 대상마다 하나씩

현재 코드에는 `data` 블록이 두 개다.

| 블록 | 물어보는 것 | 조건 |
| --- | --- | --- |
| data "aws_caller_identity" "current" | 내 계정 정보 | 없음 — 내 계정은 하나뿐이라 답이 하나다 |
| data "aws_ami" "amazon_linux" | 최신 Amazon Linux AMI | 있음 — AMI는 후보가 수천 개라 필터로 걸러야 한다 |

구조는 `resource`와 동일하게 `data "타입" "이름표" { 조건 }` 형태다. 조회할 대상이 다르면 블록도 따로 작성한다.
AWS provider에는 이 외에도 `aws_vpc`, `aws_subnet`, `aws_availability_zones`, `aws_region` 등 조회용 타입이 많다.

### EC2 생성 (resource)

```hcl
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web.id]

  tags = {
    Name = "tf-web-server"
  }
}

output "instance_public_ip" {
  value = aws_instance.web.public_ip
}
```

#### 참조 (reference)

값을 직접 적지 않고 **다른 블록을 가리키는 방식**이다.
B 구간에서 보안 그룹에 `"web"`이라는 이름표를 붙였다. 여기서는 그 이름을 **불러다 쓴다.**

| 구분 | 하는 일 |
| --- | --- |
| 이름표 (B) | 블록에 이름을 붙임. `resource "aws_security_group" "web"` |
| 참조 (C) | 붙여둔 이름을 다른 곳에서 불러 씁. `aws_security_group.web.id` |

| 코드 | 가리키는 것 |
| --- | --- |
| data.aws_ami.amazon_linux.id | 위에서 조회한 AMI의 ID |
| aws_security_group.web.id | 앞서 정의한 보안 그룹의 ID |
| aws_instance.web.public_ip | 생성된 EC2의 퍼블릭 IP |

**장점**

- 리소스 ID를 알 필요가 없다. 삭제 후 재생성해 ID가 바뀌어도 코드는 그대로 동작한다
- Terraform이 참조 관계를 보고 **생성·삭제 순서를 자동으로 결정**한다

#### 참조를 안 쓰면 생기는 문제

값을 직접 박으면 이렇게 된다.

```hcl
vpc_security_group_ids = ["sg-0e0fb182ce5db6f51"]
```

- 이 ID는 **apply 전에는 존재하지 않는다.** AWS가 생성하면서 부여하는 값이다
- destroy 후 다시 만들면 ID가 바뀌어 코드를 고쳐야 한다

참조를 쓰면 `"web이라는 보안 그룹의 ID, 그게 뭐든"`을 의미하므로 ID를 몰라도 되고 바뀌어도 상관없다.

#### 순서가 자동으로 정해지는 이유

Terraform이 `vpc_security_group_ids = [aws_security_group.web.id]` 을 읽으면:

> "EC2가 web 보안 그룹의 ID를 필요로 하네? 그럼 web을 먼저 만들어야 ID가 생기겠구나"

이렇게 판단해 순서를 정한다. 코드에 순서를 적지 않았지만 보안 그룹이 먼저 생성된 이유다.

### plan

```javascript
terraform plan
```

결과: `Plan: 2 to add, 0 to change, 0 to destroy.`

#### data 조회 결과

```javascript
data.aws_ami.amazon_linux: Reading...
data.aws_caller_identity.current: Reading...
data.aws_caller_identity.current: Read complete [id=<계정 ID>]
data.aws_ami.amazon_linux: Read complete [id=ami-072139fac78f90345]

Terraform will perform the following actions:
  + resource "aws_instance" "web" {
      ami = "ami-072139fac78f90345"      ← data 결과가 여기 들어감
```

필터 조건으로 검색한 AMI ID가 실제로 조회되어 EC2의 `ami` 값으로 들어갔다.
**plan은 data를 먼저 처리하고 그 다음 resource를 계산한다.** resource가 data 결과를 참조하므로, AMI ID를 모르면 EC2를 어떻게 만들지 계산할 수 없기 때문이다.

| 블록 | plan 때 동작 |
| --- | --- |
| data | 실제로 AWS에 조회한다. 읽기만 하므로 안전하며, 그래서 실제 값이 출력된다 |
| resource | 계산만 한다. 실제로 만들지 않고 "이렇게 될 것"만 보여준다 |

#### 관찰된 것

- EC2는 속성이 50개 이상으로 보안 그룹보다 훨씬 많다. 콘솔에서는 보이지 않던 기본 설정까지 전부 드러난다
- `vpc_security_group_ids = (known after apply)` — 보안 그룹이 아직 생성되지 않아 ID를 알 수 없는 상태
- `instance_public_ip = (known after apply)` — EC2 생성 시 AWS가 부여하는 값

<!-- 이미지: EC2 terraform plan 결과 — data 조회와 aws_instance 생성 계획 -->
<!-- 이미지: EC2 terraform plan 결과 — Plan: 2 to add, known after apply 항목 -->

### apply

```javascript
terraform apply
```

결과:

```javascript
aws_security_group.web: Creating...
aws_security_group.web: Creation complete after 2s [id=sg-0e0fb182ce5db6f51]
aws_instance.web: Creating...
aws_instance.web: Still creating... [00m10s elapsed]
aws_instance.web: Creation complete after 13s [id=i-02dab0891961bf371]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:
account_id = "<계정 ID>"
instance_public_ip = "<퍼블릭 IP>"
```

#### 생성 순서

**보안 그룹 → EC2** 순서로 생성됐다. 코드에 순서를 명시하지 않았지만, EC2가 `aws_security_group.web.id`를 참조하므로 Terraform이 보안 그룹을 먼저 만들어야 함을 판단한 것이다.
콘솔에서 수동으로 작업할 때는 사용자가 순서를 기억해야 했던 부분이다.

<!-- 이미지: EC2 terraform apply 결과 (보안 그룹 → EC2 순서로 생성, Resources: 2 added) -->

### 콘솔 확인

EC2 → 인스턴스

| 이름 | 상태 | 만든 방법 |
| --- | --- | --- |
| my_first_nginx | 중지됨 | 콘솔 클릭 (1단계) |
| tf-web-server | 실행 중, 3/3 검사 통과 | 코드 (6단계) |

둘 다 동일한 t3.micro이지만 생성 방식이 다르다. 인스턴스 ID와 퍼블릭 DNS가 apply 출력과 일치한다.
배포된 웹서버가 없으므로 브라우저로 접속해도 응답하지 않는다. 보안 그룹이 80번 포트를 열어두었지만 서버 내부에 Nginx가 설치되어 있지 않기 때문이다. 이번 단계는 "EC2가 코드로 생성되었는가"까지를 확인한다.

<!-- 이미지: EC2 콘솔 인스턴스 목록 (my_first_nginx 중지됨, tf-web-server 실행 중) -->

### destroy

```javascript
terraform destroy
```

결과:

```javascript
aws_instance.web: Destroying... [id=i-02dab0891961bf371]
aws_instance.web: Still destroying... [00m30s elapsed]
aws_instance.web: Destruction complete after 30s
aws_security_group.web: Destroying... [id=sg-0e0fb182ce5db6f51]
aws_security_group.web: Destruction complete after 1s

Destroy complete! Resources: 2 destroyed.
```

#### 삭제 순서

**EC2 → 보안 그룹** 순서로, 생성과 정확히 반대다. 보안 그룹이 EC2에 연결되어 있으므로 EC2가 먼저 제거되어야 보안 그룹을 삭제할 수 있다.
Terraform은 참조 관계를 보고 생성 순서를 정한 뒤, 삭제 시에는 그 역순으로 진행한다.
소요 시간도 다르다 — EC2는 실제 서버를 종료하므로 30초, 보안 그룹은 1초.

<!-- 이미지: EC2 terraform destroy 결과 (EC2 → 보안 그룹 순서로 삭제, Resources: 2 destroyed) -->

### 과금 관리

보안 그룹과 달리 EC2는 실행되는 동안 과금된다. 실습은 한 세션 안에서 apply부터 destroy까지 끝내는 것을 원칙으로 한다.
이번 실습 실행 시간은 약 5분이며, 프리티어 크레딧에서 차감된다.

## 트러블슈팅

### 1. 액세스 키 노출

#### 증상

`aws configure` 실행 화면을 캐처해 외부에 공유했는데, 해당 화면에 Secret Access Key가 그대로 출력되어 있었다.

#### 원인

`aws configure`는 입력한 키 값을 터미널에 그대로 표시한다. 비밀번호처럼 가려지지 않기 때문에 화면 캐처 시 그대로 남는다.
Secret Access Key는 발급 시점에 단 한 번만 표시되는 값이며, 이것과 Access Key ID가 함께 노출되면 제3자가 해당 권한으로 AWS API를 호출할 수 있다. 당시 사용한 IAM 사용자 `terraform-user`는 실습 편의를 위해 `AdministratorAccess` 권한을 가지고 있어 위험도가 더 컸다.

#### 조치

1. IAM → 사용자 → 보안 자격 증명에서 해당 액세스 키 **비활성화**
2. 비활성화 확인 후 **삭제**
3. 새 액세스 키 발급
4. `aws configure`로 재등록
5. `aws sts get-caller-identity`로 연결 정상 확인

비활성화를 먼저 한 뒤 삭제하는 이유는, 해당 키를 쓰는 곳이 있을 경우 영향을 먼저 확인하기 위해서다.

#### 재발 방지

- 터미널 캐처 시 `aws configure` 실행 구간은 잘라낸다
- 스크린샷을 공유하기 전 키 값이 포함되었는지 확인하는 절차를 거친다
- 액세스 키 CSV 파일은 `aws configure` 등록 후 삭제한다
- 9단계(보안 최적화)에서 IAM 권한을 `AdministratorAccess`에서 최소 권한으로 축소한다

#### 안전한 값 / 위험한 값

| 노출되면 위험 | 노출돼도 무방 |
| --- | --- |
| Secret Access Key | 계정 번호 (12자리 숫자) |
| Access Key ID | 리전 (ap-northeast-2) |
| .pem 키 파일 내용 | 인스턴스 ID, 리소스 ID |
| 콘솔 비밀번호 | ARN, 리소스 이름 |

판단 기준은 "그 값만으로 인증이 가능한가"다.

---

### 2. 로컬 state로 인한 다중 기기 작업 제약

#### 증상

포트폴리오 작업을 노트북과 데스크톱에서 번갈아 진행하려 했으나, Terraform 작업 폴더를 단순히 복사하는 방식으로는 리소스 중복 생성 위험이 있음을 확인했다.

#### 원인

Terraform은 apply 시 `코드 ↔ state ↔ 실제 AWS` 세 가지를 비교해 차이만큼만 작업한다. 이때 state(`terraform.tfstate`)는 "실제로 무엇을 만들었는가"의 기록 역할을 한다.
state가 한 컴퓨터에만 있으면, 다른 컴퓨터에서는 기록이 없으므로 "아직 아무것도 만들지 않았다"고 판단해 동일한 리소스를 다시 생성한다.
**키가 같아도 해결되지 않는다.** 키는 AWS에 접근할 수 있는 권한이고, state는 무엇을 만들었는지에 대한 기록이므로 별개의 문제다.
발생 가능한 문제:

- 리소스 중복 생성 → 요금 증가
- 한쪽에서 `destroy`해도 다른 쪽이 만든 리소스는 남아 계속 과금되는 유령 리소스 발생
- 두 기기가 동시에 apply하면 state 손상

#### 조치

현재 단계에서는 작업 폴더를 클라우드 드라이브 동기화 경로로 이동해 사용하되, 제약을 인지하고 운용 규칙을 두기로 했다.

```javascript
mv ~/terraform/step6 <구글드라이브>/클라우드 포트폴리오/terraform/
rm -rf .terraform
terraform init
```

운용 규칙:

- 동기화가 완료된 상태에서만 명령어 실행
- 단시간 내에 두 기기를 번갈아 쓰지 않는다
- `terraform.tfstate (1)` 같은 충돌 파일이 생기면 작업을 중단한다

#### 근본 해결책 (예정)

state를 S3 버킷에 두는 **원격 백엔드**로 전환한다.

| 구분 | 방식 | 시차 | 동시 작업 방지 |
| --- | --- | --- | --- |
| 클라우드 드라이브 | 각 기기에 사본을 두고 동기화 | 있음 | 없음 |
| S3 원격 백엔드 | 원본 하나를 직접 읽고 씁 | 없음 | 있음 (잠금) |

S3 백엔드는 apply 시마다 최신 state를 직접 가져오므로 사본이 생기지 않고, 한쪽이 작업 중이면 다른 쪽은 잠금으로 차단된다. Terraform 1.10 이상은 DynamoDB 없이 S3만으로 잠금이 가능하다.

#### 재발 방지

- state를 단순 파일 복사로 공유하지 않는다
- `terraform.tfstate`는 Git에 올리지 않는다 (`.gitignore` 적용)
- 다중 기기·팀 작업이 필요해지면 원격 백엔드를 먼저 구성한다

## 6단계 용어

6단계에서 새로 나온 개념과 명령어. **A → B → C 진행 순서대로** 정리했다.

### A. 환경 구성 및 AWS 연결

#### 도구 개념

| 용어 | 한 줄 설명 |
| --- | --- |
| Terraform | 인프라 구성을 코드로 적어두고 명령어로 생성·삭제하는 도구. HashiCorp가 만들었으며 AWS 전용이 아니다 |
| IaC (Infrastructure as Code) | 인프라를 코드로 기술하고 관리하는 방식 |
| 선언형(Declarative) | "순서대로 하라"가 아니라 "결과가 이런 상태여야 한다"를 쓰는 방식. 이미 그 상태면 아무 작업도 하지 않는다 |
| HCL | Terraform 코드를 쓰는 설정 언어. `.tf` 확장자를 사용한다 |
| provider | Terraform이 어떤 플랫폼을 다룰지 결정하는 플러그인. AWS용은 `hashicorp/aws` |

#### 자격 증명

| 용어 | 한 줄 설명 |
| --- | --- |
| 액세스 키 | CLI나 Terraform이 AWS API를 호출할 때 쓰는 자격 증명. Access Key ID + Secret Access Key 한 쌍 |
| Secret Access Key | 발급 시 단 한 번만 표시되며 이후 재확인할 수 없다. 분실 시 재발급해야 한다 |

자격 증명은 Terraform이 아니라 AWS CLI가 `~/.aws/credentials`에 저장한다. 그래서 `.tf` 파일에는 키가 들어가지 않는다.

#### 명령어 — 설치·인증

| 명령어 | 뜻 |
| --- | --- |
| terraform --version | 설치된 Terraform 버전 확인 |
| aws configure | AWS CLI에 액세스 키·리전·출력 형식을 등록 |
| aws sts get-caller-identity | 현재 자격 증명으로 AWS에 정상 연결되는지 확인 |

#### 명령어 — 폴더·파일 작업

| 명령어 | 뜻 |
| --- | --- |
| mkdir -p | 폴더 생성. -p는 중간 경로가 없어도 함께 생성 |
| pwd | 현재 작업 경로 출력 |
| ls -a | 숨김 파일까지 포함해 목록 표시 |
| ls -la | 숨김 파일 + 권한·소유자·크기·수정시간 상세 표시 |
| mv | 파일·폴더 이동 또는 이름 변경 |
| rm -rf | 폴더와 내용물 강제 삭제. 되돌릴 수 없음 |
| cat &gt; 파일 &lt;&lt; 'EOF' | 여러 줄 내용을 한 번에 파일로 작성 (덮어쓰기) |
| cat &gt;&gt; 파일 &lt;&lt; 'EOF' | 기존 내용 뒤에 이어붙이기 |

#### 핵심 명령어 3종

| 명령어 | 뜻 | AWS 변화 |
| --- | --- | --- |
| terraform init | provider 플러그인을 내려받아 작업 폴더를 초기화 | 없음 |
| terraform plan | 적용 시 리소스가 어떻게 변경되는지 미리 보여준다 | 없음 |
| terraform apply | 코드대로 실제 리소스를 생성·변경·삭제한다 | 있음 |

#### 생성되는 파일

| 용어 | 한 줄 설명 |
| --- | --- |
| 숨김 파일 | 이름이 `.`으로 시작하는 파일. 평소에는 보이지 않으며 `ls -a`로 확인한다 |
| .terraform/ | init이 내려받은 provider 플러그인이 저장되는 폴더 |
| .terraform.lock.hcl | provider 버전을 고정해 다른 환경에서도 동일한 버전을 받게 하는 파일 |
| .gitignore | Git이 무시할 파일 목록을 적어둔 파일 |

---

### B. 첫 리소스 생성 및 삭제

#### 블록의 종류

| 용어 | 한 줄 설명 |
| --- | --- |
| resource 블록 | 실제로 리소스를 생성하는 블록. Terraform에서 무언가를 만드는 것은 이것뿐이다 |
| data 블록 | 조회 전용 블록. 기존 정보를 읽기만 하고 생성하지 않는다 |
| output 블록 | apply 완료 후 화면에 출력할 값을 지정하는 블록 |

#### plan 출력 읽기

| 표시 | 의미 |
| --- | --- |
| + | 생성 |
| - | 삭제 |
| \~ | 변경 |
| (known after apply) | AWS가 생성 시에 부여하는 값이라 plan 단계에서는 알 수 없다는 표시 |

#### state

| 용어 | 한 줄 설명 |
| --- | --- |
| state (terraform.tfstate) | Terraform이 무엇을 만들었는지 기록해둔 파일. 이것과 코드를 비교해 차이만큼만 작업한다 |
| terraform destroy | state에 기록된 리소스를 삭제한다. 콘솔로 만든 다른 리소스는 건드리지 않는다 |
| 원격 백엔드 | state를 로컬이 아닌 S3 등 공용 위치에 두어 여러 기기·팀이 공유하는 방식 |
| 잠금(lock) | 한쪽이 apply 중일 때 다른 쪽의 작업을 차단해 state 손상을 막는 기능 |

---

### C. EC2 코드화

| 용어 | 한 줄 설명 |
| --- | --- |
| 참조(reference) | 값을 직접 쓰지 않고 다른 블록을 가리키는 것. 예: `aws_security_group.web.id` |
| 의존성 자동 해결 | 참조 관계를 보고 Terraform이 생성·삭제 순서를 스스로 결정하는 것 |

생성은 참조되는 쪽부터(보안 그룹 → EC2), 삭제는 그 역순(EC2 → 보안 그룹)으로 진행된다.

## 배운 점

### A. Terraform 환경 구성 및 AWS 연결

- Terraform 이란 이전까지 인프라의 수작업들을 코드로 작성해 둠으로써 추후에 인프라 만들 때 명령어로 쉽게 생성 및 제거하는 기술이다. 이 방식을 IaC (Infrastructure as Code) 라 불리며 HCL 코드로 작성된다. (확장자는 .tf)
- 연결 확인 명령어

```hcl
aws sts get-caller-identity
```

- main.tf 작성

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

data "aws_caller_identity" "current" {}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}
```

required_providers → 버전 범위 및 사용 provider 선언

provider “aws” → 리전 위치 설정

data → 조회전용, 읽기만

output → apply 후 화면에 출력하는 값

- terraform 실행 명령어
  1. terraform init —> 플러그인 내려받음. provider 거침
     1. 생성파일
        1. .terraform/ : provider 플로그인이 저장되는 폴더
        2. .terraform.lock.hcl : provider 버전을 고정해 다른  환경에서도 동일한 버전 다운 받게 하는 파일
  2. terraform plan —> 적용 후 어떻게 적용되는지 보여주는 미리보기 단계
     1. data조회와 resource 계산 후 보여줌. 지금은 리소스가 없어 데이터 코드만 거친다.
  3. terraform apply —> 코드대로 리소스 생성, 추가, 변경, 삭제
     1. terraform.tfstate 생성 : terraform이 무엇을 만들었는지 기록해두는 파일 (장부)
        1. state 파일은 리소스의 식별자와 속성이 그대로 나타나 공개하면 그대로 노출됨.
        2. state가 없는 컴퓨터에서 apply 하면 리소스가 중복 생성된다.

### B. 첫 리소스 생성 및 삭제 (보안그룹)

```hcl
resource "aws_security_group" "web" {
  name        = "tf-web-sg"
  description = "Managed by Terraform"

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "tf-web-sg"
  }
}
```

- resource → AWS에서 실제로 리소스를 만듦
- 보안 그룹 코드 작성 : cat \>\> main.tf \<\< ‘EOF’ ( \>\>는 이어쓰기, \>는 덮어쓰기, EOF는 End Of File의 약자로 이 단어 나올 때 입력 종료라는 뜻 —\> heredoc구조, 다른 단어도 가능)
  1. aws_security_group : 리소스 타입
     1. web : terraform 에서 사용하는 이름표. aws엔 전달 안 됨
  2. ingress : 들어오는 트래픽 (포트 번호, 프로토콜 ,ip 등을 정의)
  3. egress : 나가는 트래픽
- 이후 plan → apply 하면 plan에서 known after apply 였던 ID가 실제값으로 채워진다.
  - EC2 console에 들어가 보안그룹을 확인하면 자동으로 생성된 걸 확인했다.
  - 후 destroy하면 자신의 state 기록된 리소스만 삭제하고 콘솔로 만든 다른 리소스는 안 건드린다.

### C. EC2 코드화

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web.id]

  tags = {
    Name = "tf-web-server"
  }
}

output "instance_public_ip" {
  value = aws_instance.web.public_ip
}
```

- AMI 조회
  - data “aws_ami” “amazon_linux” —\> aws_ami : 데이터 타입 / amazon_linux : 이름표
    - owner = \[”amazon”\] : 아마존이 발행한 공식 이미지만 대상
    - most_recent : 조건에 맞는 것 중 최신 버전
  - filter : name 이 value 패턴인 것을 필터 처리함.
  - AMI ID는 리전마다 다르고 이미지가 갱신될 때마다 바뀌기 때문에 ID를 직접 쓰지 않는다.
- EC2 생성 (resource)
  - resource “aws_instance” “web”
    - ami : 위에서 조회한 AMI ID
    - instance type : t3.micro
    - vpc_security_group_ids : 앞에 정의한 보안 그룹 ID
  - output “instance_public_ip”
    - 생성된 EC2의 퍼블릭 IP
  - 참조 : 값을 쓰지 않고 다른 블록을 가르키는 것
    - terraform이 참조관계를 보고 생성 및 삭제 순서 자동으로 결정 (위에 정의한 web을 이용)
- terraform plan 실행
  - data 조회 (지금까지 작성했던 data 코드들 조회, 실제 AWS에서 조회)
  - resource 계산 : data 결과 참조, 계산만 실행. 실제로 만들지는 않음
  - 아직 apply를 실행하지 않아서 보안 그룹과 인스턴스가 생성되지 않은 상태.
    - vpc_security_group_ids = (known after apply)
    - instance_public_ip = (known after apply)
- terraform apply
  - 보안 그룹, 인스턴스 생성
  - output에 account_id, instance_public_ip 조회
  - 생성순서는 보안 그룹 → EC2 순서
- terraform destroy
  - EC2 → 보안 그룹 순서로 삭제. 보안그룹이 EC2에 연결돼있으므로 EC2가 먼저 제거되어야 함.
