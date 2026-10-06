---
title: "Proxmox 홈랩"
summary: "미니PC 한 대에 Proxmox를 설치해 VM 두 대로 나누고, 포트를 열지 않고 Tailscale과 SSH 키로만 접속하는 서버 환경을 만들었습니다."
role: "개인 프로젝트, 설계부터 운영까지"
status: "진행 중"
category: "인프라"
stack: ["Proxmox VE", "Ubuntu Server", "Tailscale", "SSH", "Docker", "Nginx", "Cloudflare Tunnel"]
period: "2026.09 ~"
featured: true
weight: 2
mapLabel: "homelab"
isHost: true
aliases: ["/posts/proxmox-homelab/"]
brief:
  why: "AWS에서 매니지드 서비스가 대신 해주던 서버, 네트워크, 접속 관리, 배포를 직접 구성해보면서 그 서비스들이 무엇을 대신하는지 확인하려고 시작했습니다."
  did:
    - "Proxmox VE 설치, VM 두 대로 개인 사이트와 산학 서버 분리"
    - "공유기 포트를 열지 않고 Tailscale 내부망으로만 접속"
    - "SSH 키 인증으로 바꾸고 비밀번호 로그인 차단"
    - "VM마다 Docker 설치, 디스크(LVM) 확장, 기본 세팅 후 스냅샷 저장"
    - "도메인 구매 후 Cloudflare Tunnel로 HTTPS 외부 공개"
  verified:
    - "집 밖 맥북에서 Tailscale 주소로 각 VM에 SSH 접속"
    - "이 사이트가 VM 100의 Docker Nginx 컨테이너에서 서빙됨"
    - "공유기 포트를 열지 않고 Cloudflare Tunnel로 ihaewon.com 외부 공개, 외부 네트워크에서 접속 확인"
servers:
  host:
    name: "pve"
    kind: "Proxmox 호스트"
    spec: "i5-14450HX / RAM 16GB / NVMe 512GB"
    state: "가동 중"
  access: "Tailscale 내부망 · 공유기 포트 개방 없음"
  vms:
    - { id: "VM 100", name: "portfolio", spec: "4코어 / RAM 4GB / 디스크 38GB", role: "이 사이트를 Docker Nginx로 서빙", here: true }
    - { id: "VM 101", name: "산학 서버", spec: "4코어 / RAM 6GB / 디스크 39GB", role: "산학 프로젝트 서버. 팀원은 이 VM에만 접속" }
steps:
  - { name: "Proxmox 설치와 원격 접속", status: "완료", note: "homelab-01-proxmox" }
  - { name: "VM 원격 접속과 Docker", status: "완료", note: "homelab-02-vm-docker" }
  - { name: "포트폴리오 사이트 배포", status: "완료", note: "homelab-03-site-deploy" }
  - { name: "도메인·HTTPS 외부 공개", status: "완료" }
  - { name: "k3s 이전", status: "예정" }
  - { name: "GitHub Actions·Argo CD 자동 배포", status: "예정" }
  - { name: "모니터링", status: "예정" }
next: "정전 후 자동 부팅을 BIOS에서 켜고, k3s로 서비스를 옮길 계획입니다."
draft: false
---

## 개요

최종 목표는 코드를 push하면 홈서버의 서비스까지 자동으로 갱신되는 구조입니다. 지금은 4단계(도메인·HTTPS 외부 공개)까지 마쳤습니다.

<!-- 작성 틀: 선택한 이유 / 배운 점(호스트·VM별) 은 직접 작성. 서버별 배운 점은 front matter servers.*.learn 에 넣으면 펼치기 칸에 표시됨 -->
