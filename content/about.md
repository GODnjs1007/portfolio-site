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
profile:
  name: "이해원"
  role: "클라우드·인프라 운영 엔지니어 (신입)"
  strengths:
    - "문제가 생기면 추측하지 않고 로그와 시스템 상태부터 확인해, 원인을 단계적으로 좁혀 갑니다."
    - "해결한 문제는 증상·원인·해결 순서로 기록해 두고, 같은 문제가 다시 나오면 그 기록부터 찾아봅니다."
  facts:
    - { label: "학력", value: "연세대학교 미래캠퍼스 소프트웨어학부 · 2027.02 졸업 예정" }
    - { label: "교육", value: "연세대 AI부트캠프 의료AI응용 수료 (2026 여름)" }
    - { label: "어학", value: "OPIc IL (2026.09)" }
  stack:
    - group: "리눅스·네트워크"
      items: [{ n: "Ubuntu", i: "ubuntu" }, { n: "SSH", i: "term" }, { n: "Nginx", i: "nginx" }, { n: "Tailscale", i: "tailscale" }, { n: "Cloudflare Tunnel", i: "cloudflare" }]
    - group: "AWS"
      items: [{ n: "EC2", i: "amazonec2" }, { n: "VPC", i: "amazonwebservices" }, { n: "ALB", i: "awselasticloadbalancing" }, { n: "Auto Scaling", i: "amazonwebservices" }, { n: "RDS", i: "amazonrds" }, { n: "ECS Fargate", i: "awsfargate" }, { n: "ECR", i: "amazonwebservices" }, { n: "CloudWatch", i: "amazoncloudwatch" }]
    - group: "컨테이너·자동화"
      items: [{ n: "Docker", i: "docker" }, { n: "Terraform", i: "terraform" }, { n: "Hugo", i: "hugo" }]
    - group: "가상화·기타"
      items: [{ n: "Proxmox VE", i: "proxmox" }, { n: "Redis Streams", i: "redis" }, { n: "GitHub", i: "github" }]
  activities:
    - { period: "2026.09 ~", title: "AI 산학프로젝트 (팀장)", note: "서버 구조(TCP 수신, Redis Streams, 워커) 설계" }
    - { period: "2026.09 ~", title: "융합캡스톤디자인 (Frozen Stiff)", note: "게임 접속 솔루션 검증, 플레이 기록 수집 서버, 빌드·배포 자동화 담당" }
    - { period: "2026.09 ~", title: "홈 서버 운영, 이 포트폴리오 사이트", note: "Proxmox 위에 Ubuntu VM을 운영하고, Tailscale 원격 접속과 Docker Nginx·Cloudflare Tunnel로 사이트를 공개" }
    - { period: "2026.07 ~", title: "AWS 인프라 구축 실습", note: "EC2·Nginx부터 VPC, ALB, Terraform, ECS Fargate, CloudWatch까지. 장애를 로그로 추적해 기록" }
    - { period: "2026 여름", title: "연세대 AI부트캠프 의료AI응용", note: "비정형데이터분석, AI기반건강보험빅데이터분석, 의료버티컬AI에이전트 수료" }
links:
  - { name: "GitHub", url: "https://github.com/GODnjs1007" }
draft: false
---

<!-- 작성 틀: 경력 / 자격(취득 확정된 것만) / 수상(확정된 것만) / 이력서 링크. 확인된 항목만 front matter에 추가 -->
