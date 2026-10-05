---
title: "AWS 인프라 10단계"
summary: "EC2 한 대에서 시작해 VPC, ALB·Auto Scaling, Terraform, Private RDS, ECS, CloudWatch까지 단계별로 확장한 실습입니다."
role: "개인 프로젝트"
status: "진행 중"
category: "인프라"
stack: ["EC2", "VPC", "ALB", "Auto Scaling", "Terraform", "RDS", "Docker", "ECS Fargate", "CloudWatch"]
period: "2026.07 ~ 2026.09"
featured: true
weight: 1
mapLabel: "aws"
relations: ["다음 단계 → 홈랩"]
brief:
  why: "콘솔에서 서버 한 대를 띄우는 것부터 시작해, 서버를 늘리고 코드로 만들고 컨테이너로 옮기고 감시하는 과정을 한 단계씩 직접 해봤습니다."
  did:
    - "EC2에 Nginx 배포, 일부러 장애 4종을 만들어 로그로 원인 찾기"
    - "VPC·보안 그룹·탄력적 IP로 접근 범위 좁히기"
    - "ALB + Auto Scaling으로 두 AZ에 서버 분산"
    - "Terraform으로 인프라 코드화, 퍼블릭 EC2와 Private RDS 분리"
    - "Docker 이미지 → ECR → ECS Fargate 배포"
    - "CloudWatch 로그 확인과 이메일 알람 구성"
  verified:
    - "ALB 주소를 새로고침하면 AZ-2a, 2b 서버가 번갈아 응답"
    - "서버의 Nginx를 중지시켜 자동 복구 동작 확인"
    - "ECS 태스크를 강제로 중지시켜 새 태스크로 자동 교체되는 것 확인"
    - "알람을 실제로 발생시켜 이메일 수신까지 확인"
steps:
  - { name: "EC2 + Nginx 기본 배포", status: "완료", note: "aws-01-ec2-nginx" }
  - { name: "커스텀 웹페이지 배포", status: "완료", note: "aws-02-custom-page" }
  - { name: "장애 발생 및 트러블슈팅", status: "완료", note: "aws-03-troubleshooting" }
  - { name: "VPC·보안 설정", status: "완료", note: "aws-04-vpc-security" }
  - { name: "ALB·Auto Scaling", status: "완료", note: "aws-05-alb-asg" }
  - { name: "Terraform 자동화", status: "완료", note: "aws-06-terraform" }
  - { name: "Terraform 기반 Private RDS", status: "완료", note: "aws-07-private-rds" }
  - { name: "Docker·ECS", status: "완료", note: "aws-08-docker-ecs" }
  - { name: "CloudWatch 모니터링", status: "완료", note: "aws-09-cloudwatch" }
  - { name: "비용·보안 최적화", status: "예정" }
next: "10단계 비용·보안 최적화를 진행합니다."
draft: false
---

## 개요

단계마다 앞 단계의 구조를 그대로 이어받아 한 가지씩 바꿨습니다. 서버 1대 → 네트워크 정리 → 여러 대 → 코드화 → DB 분리 → 컨테이너 → 감시 순서입니다. 각 단계의 진행 과정과 트러블슈팅은 진행 단계 목록에 연결된 기록에 있습니다.

<!-- 작성 틀: 선택한 이유 / 배운 점 은 직접 작성 -->
