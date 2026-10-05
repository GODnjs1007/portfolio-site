---
title: "소개"
summary: "할 수 있는 일과 그 근거가 되는 기록을 한 화면에 모았습니다."
layout: "about"
intro: "연세대학교 미래캠퍼스 소프트웨어학부, 2027년 2월 졸업 예정입니다. 클라우드·인프라 운영 직무를 준비하고 있고, 반복되는 운영을 자동화하는 엔지니어를 목표로 합니다."
skills:
  - area: "리눅스 서버 운영"
    what: "패키지·서비스 관리, 파일 권한, 디스크(LVM) 확장, 로그로 원인 찾기"
    notes: ["aws-01-ec2-nginx", "aws-03-troubleshooting", "homelab-02-vm-docker"]
  - area: "네트워크와 접근 통제"
    what: "VPC·서브넷·보안 그룹 설계, 포트 개방 없는 사설망 접속, SSH 키 인증"
    notes: ["aws-04-vpc-security", "aws-07-private-rds", "homelab-01-proxmox", "homelab-02-vm-docker"]
  - area: "가용성과 장애 대응"
    what: "ALB·Auto Scaling 다중 AZ 구성, 일부러 장애를 내고 자동 복구 확인"
    notes: ["aws-03-troubleshooting", "aws-05-alb-asg", "aws-08-docker-ecs"]
  - area: "인프라 코드화 (IaC)"
    what: "Terraform으로 EC2·VPC·RDS·ECS 생성과 삭제"
    notes: ["aws-06-terraform", "aws-07-private-rds", "aws-08-docker-ecs"]
  - area: "컨테이너"
    what: "Docker 이미지 빌드, ECR 푸시, ECS Fargate 배포, VM에서 Nginx 컨테이너 운영"
    notes: ["aws-08-docker-ecs", "homelab-02-vm-docker", "homelab-03-site-deploy"]
  - area: "가상화"
    what: "Proxmox VE 설치, VM 분리, 스냅샷"
    notes: ["homelab-01-proxmox", "homelab-02-vm-docker"]
  - area: "모니터링"
    what: "CloudWatch 로그 확인, 알람을 실제로 발생시켜 이메일 수신 확인"
    notes: ["aws-09-cloudwatch"]
links:
  - { name: "GitHub", url: "https://github.com/GODnjs1007" }
draft: false
---

<!-- 작성 틀: 경력 / 자격(취득 확정된 것만) / 수상(확정된 것만) / 이력서 링크. 확인된 항목만 front matter에 추가 -->
