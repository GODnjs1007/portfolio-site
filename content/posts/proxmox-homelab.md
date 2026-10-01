---
title: "Proxmox 기반 홈랩 인프라 구축"
date: 2026-10-01
draft: false
summary: "미니PC에 Proxmox VE를 설치하고 VM 2개로 포트폴리오와 산학 환경을 분리했다."
---

## 구성
- Proxmox VE 9.2 (FIREBAT F2, i5-14450HX, RAM 16GB)
- VM 100 portfolio / VM 101 ecg
- Tailscale 원격 접속, SSH 키 인증

## 진행 단계
1. Proxmox 설치와 원격 접속 구성
2. VM 원격 접속과 Docker 환경 구성
3. 포트폴리오 사이트 컨테이너 배포 (진행 중)
