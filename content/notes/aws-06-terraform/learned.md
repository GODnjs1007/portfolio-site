---
title: "배운 점"
---

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
