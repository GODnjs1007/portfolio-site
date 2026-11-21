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
    - "먼저 복구하고, 원인과 해결 과정은 기록으로 남겨 같은 장애가 반복되지 않게 합니다."
    - "단계마다 증상·원인·해결을 기록하고, 배운 점은 제가 직접 씁니다. AI의 도움을 받은 부분도 제 말로 다시 정리해서 설명할 수 있는 상태로 남기고, 모아 둔 기록을 다시 읽으며 복습합니다."
  facts:
    - { label: "학력", value: "연세대학교 미래캠퍼스 소프트웨어학부 · 2027.02 졸업 예정" }
    - { label: "교육", value: "연세대 AI부트캠프 의료AI응용 수료 (2026 여름)" }
  stack:
    - group: "리눅스·네트워크"
      items: [{ n: "Ubuntu", i: "ubuntu" }, { n: "SSH", i: "term" }, { n: "Nginx", i: "nginx" }, { n: "Tailscale", i: "tailscale" }, { n: "Cloudflare Tunnel", i: "cloudflare" }]
    - group: "AWS"
      items: [{ n: "EC2", i: "amazonec2" }, { n: "VPC", i: "amazonwebservices" }, { n: "ALB", i: "awselasticloadbalancing" }, { n: "Auto Scaling", i: "amazonwebservices" }, { n: "RDS", i: "amazonrds" }, { n: "ECS Fargate", i: "awsfargate" }, { n: "ECR", i: "amazonwebservices" }, { n: "CloudWatch", i: "amazoncloudwatch" }]
    - group: "컨테이너·자동화"
      items: [{ n: "Docker", i: "docker" }, { n: "Terraform", i: "terraform" }, { n: "Hugo", i: "hugo" }]
    - group: "가상화·기타"
      items: [{ n: "Proxmox VE", i: "proxmox" }, { n: "Redis Streams", i: "redis" }, { n: "GitHub", i: "github" }]
    - group: "백엔드"
      items: [{ n: "FastAPI", i: "fastapi" }, { n: "Django", i: "django" }, { n: "PostgreSQL", i: "postgresql" }]
  activities:
    - { period: "2026.09 ~", title: "AI 산학프로젝트 (팀장)", note: "서버 구조(TCP 수신, Redis Streams, 워커) 설계, 환자 100명 부하테스트 실측 → 학회 우수 발표 논문상" }
    - { period: "2026.09 ~", title: "융합캡스톤디자인 (Frozen Stiff)", note: "게임 접속 솔루션 검증, 플레이 기록 수집 서버, 빌드·배포 자동화 담당" }
    - { period: "2026.09 ~", title: "Proxmox 홈랩 운영, ihaewon.com 포트폴리오 사이트", note: "Proxmox 위에 Ubuntu VM을 운영하고, Tailscale 원격 접속과 Docker Nginx·Cloudflare Tunnel로 사이트를 공개" }
    - { period: "2026.07 ~", title: "AWS 인프라 구축 실습", note: "EC2·Nginx부터 VPC, ALB, Terraform, ECS Fargate, CloudWatch까지. 장애를 로그로 추적해 기록" }
    - { period: "2026 여름", title: "연세대 AI부트캠프 의료AI응용", note: "비정형데이터분석, AI기반건강보험빅데이터분석, 의료버티컬AI에이전트 수료" }
  awards:
    - { period: "2026.11", title: "우수 발표 논문상 · 2026 한국인공지능융합기술학회 추계학술대회", note: "산학 심전도 서버 처리 지연 실측 논문, 제1저자", link: "/projects/sanhak-paper/" }
    - { period: "2026.11", title: "수상 · 2026 AI 기술 혁신 챌린지(반려·돌봄) 결선", note: "반려동물 위탁돌봄 지시 점검 논문, 제1저자 · 구두 발표", link: "/projects/pet-handover-ai/" }
    - { period: "2026.11", title: "우수상 · 2026 캡스톤디자인 경진대회", note: "커리어 내비, 웹 서비스와 배포·운영 담당", link: "/projects/career-navi/" }
  papers:
    - { period: "2026.11", title: "다중 환자 동시 심전도 부정맥 실시간 모니터링을 위한 큐 기반 서버의 처리 지연 실측", note: "2026 한국인공지능융합기술학회 추계학술대회 · 제1저자 (공저 7명) · 우수 발표 논문상", link: "/projects/sanhak-paper/" }
    - { period: "2026.11", title: "반려동물 위탁 돌봄 지시 정리에서 LLM 구조화 추출과 규칙 기반 검증의 효과 비교", note: "같은 학회 AI 기술 혁신 챌린지(반려·돌봄) 결선 구두 발표 · 제1저자 · 수상. 학술지 「인공지능융합기술연구」 심사 중", link: "/projects/pet-handover-ai/" }
    - { period: "2026.11", title: "LLM API 응답 지연 대응 정책의 실측 기반 비교: 대기, 재시도, 대체 모델 전환", note: "2026 한국인공지능융합기술학회 추계학술대회 포스터 발표 · 단독 저자", link: "/projects/llm-api-policy/" }
links:
  - { name: "GitHub", url: "https://github.com/GODnjs1007" }
draft: false
---

<!-- 작성 틀: 경력 / 자격(취득 확정된 것만) / 수상(확정된 것만) / 이력서 링크. 확인된 항목만 front matter에 추가 -->
