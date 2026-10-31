---
title: "Proxmox 홈랩"
summary: "미니PC 한 대에 Proxmox를 설치해 용도별 VM으로 나누고, 포트를 열지 않고 Tailscale과 SSH 키로만 접속하는 서버 환경을 만들었습니다."
role: "개인 프로젝트, 설계부터 운영까지"
status: "진행 중"
category: "인프라"
stack: ["Proxmox VE", "Ubuntu Server", "Tailscale", "SSH", "Docker", "Nginx", "Cloudflare Tunnel", "Prometheus", "Grafana"]
period: "2026.09 ~"
featured: true
weight: 2
mapLabel: "homelab"
isHost: true
aliases: ["/posts/proxmox-homelab/"]
brief:
  why: "AWS에서 매니지드 서비스가 대신 해주던 서버, 네트워크, 접속 관리, 배포를 직접 구성해보면서 그 서비스들이 무엇을 대신하는지 확인하려고 시작했습니다."
  did:
    - "Proxmox VE 설치, 개인 사이트·산학 서버·논문 실측·팀 프로젝트마다 VM을 따로 분리"
    - "공유기 포트를 열지 않고 Tailscale 내부망으로만 접속"
    - "SSH 키 인증으로 바꾸고 비밀번호 로그인 차단"
    - "VM마다 Docker 설치, 디스크(LVM) 확장, 기본 세팅 후 스냅샷 저장"
    - "도메인 구매 후 Cloudflare Tunnel로 HTTPS 외부 공개"
    - "Prometheus·Grafana로 서버 4대 통합 모니터링, 서버다운·디스크·메모리·CPU 알림 규칙"
  verified:
    - "집 밖 맥북에서 Tailscale 주소로 각 VM에 SSH 접속"
    - "이 사이트가 VM 100의 Docker Nginx 컨테이너에서 서빙됨"
    - "공유기 포트를 열지 않고 Cloudflare Tunnel로 ihaewon.com 외부 공개, 외부 네트워크에서 접속 확인"
    - "Prometheus targets 화면에서 서버 4대 전부 UP, 울리는 알림 0 확인 (10.13)"
servers:
  host:
    name: "pve"
    kind: "Proxmox 호스트"
    spec: "i5-14450HX / RAM 16GB / NVMe 512GB"
    state: "가동 중"
  access: "Tailscale 내부망 · 공유기 포트 개방 없음"
  vms:
    - { id: "VM 100", name: "portfolio", spec: "4코어 / RAM 4GB / 디스크 38GB", role: "이 사이트를 Docker Nginx로 서빙. 처음 만든 VM. 미니PC RAM 16GB를 다른 VM과 나눠 써야 해서 4GB만 배정. 설치 기본값(LVM)이 루트를 18.5GB만 잡아서 lvextend로 38GB까지 늘림. Tailscale·SSH 키 로그인·Docker를 세팅하고 스냅샷을 남긴 뒤 이후 VM도 같은 순서로 만듦.", here: true }
    - { id: "VM 101", name: "산학 서버", spec: "4코어 / RAM 6GB / 디스크 39GB", role: "산학 프로젝트 팀 테스트 서버. 팀원은 이 VM에만 접속. 10.28 팀 서버 이전 후 중지. 부하테스트를 해야 해서 portfolio보다 메모리를 6GB로 더 줌. portfolio에서 겪은 걸 반영해 설치 때 LVM을 끄고 처음부터 39GB 전부 사용. 공개 데이터만 두고, 환자 6~100명 부하테스트와 Prometheus·Grafana 모니터링을 이 VM에서 진행.", off: true }
    - { id: "VM 102", name: "paper", spec: "2코어 / RAM 1GB / 디스크 20GB", role: "논문 실측 데이터 수집 (cron). 10.26 수집 종료 후 중지. cron으로 10분마다 API를 부르는 일 하나만 해서 자원을 최소로 배정. 실측 기록이 다른 작업에 섞이지 않게 VM을 따로 둠. 수집을 끝낸 뒤 데이터를 백업하고 중지, 학술대회 발표 후 삭제 예정.", off: true }
    - { id: "VM 103", name: "careernavi", spec: "2코어 / RAM 4GB / 디스크 28GB", role: "커리어 내비 팀 개발 서버. 팀원 계정과 Tailscale 공유는 이 VM 하나만. RAM 4GB는 FastAPI·Nginx·PostgreSQL에 한국어 임베딩 모델(약 2GB)과 여유분을 더해 잡음. 루트가 13.67GB만 잡혀 있어 lvextend로 28GB까지 늘림. docker 그룹이 사실상 관리자 권한이라 이 VM에는 이 프로젝트만 둠.", }
    - { id: "VM 105", name: "calendar", spec: "2코어 / RAM 4GB / 디스크 28GB", role: "웹프로젝트 사이 캘린더 서버. calendar.ihaewon.com으로 외부 공개. Qemu Agent와 Discard는 켜고, 우분투에 필요 없는 TPM은 끔. 루트가 14GB만 잡혀 있어 28GB까지 늘리고, 기초 세팅이 끝난 상태를 스냅샷 base-setup으로 저장. 저장소 전용 배포 키를 SSH Host 별칭으로 구분해 한 VM에 여러 저장소 키를 둘 수 있게 함." }
steps:
  - { name: "Proxmox 설치와 원격 접속", status: "완료", note: "homelab-01-proxmox" }
  - { name: "VM 원격 접속과 Docker", status: "완료", note: "homelab-02-vm-docker" }
  - { name: "포트폴리오 사이트 배포", status: "완료", note: "homelab-03-site-deploy" }
  - { name: "도메인·HTTPS 외부 공개", status: "완료", note: "homelab-04-domain-https" }
  - { name: "k3s 이전", status: "예정" }
  - { name: "GitHub Actions·Argo CD 자동 배포", status: "예정" }
  - { name: "통합 모니터링 (먼저 진행)", status: "완료", note: "homelab-07-monitoring" }
next: "정전 후 자동 부팅을 BIOS에서 켜고, 알림을 메일이나 메신저로 보내도록 붙인 뒤 k3s로 서비스를 옮길 계획입니다."
draft: false
---

## 개요

최종 목표는 코드를 push하면 홈서버의 서비스까지 자동으로 갱신되는 구조입니다. 지금은 4단계(도메인·HTTPS 외부 공개)와 7단계(통합 모니터링)를 마쳤고, 5·6단계(k3s, 자동 배포)가 남았습니다.

<!-- 작성 틀: 선택한 이유 / 배운 점(호스트·VM별) 은 직접 작성. 서버별 배운 점은 front matter servers.*.learn 에 넣으면 펼치기 칸에 표시됨 -->
