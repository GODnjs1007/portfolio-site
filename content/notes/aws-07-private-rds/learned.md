---
title: "배운 점"
---

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
