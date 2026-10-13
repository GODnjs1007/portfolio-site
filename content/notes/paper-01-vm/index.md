---
title: "논문 실측 1단계 · paper VM 생성과 원격 접속"
date: 2026-10-08
projects: ["llm-api-policy"]
step: 1
summary: "논문 실측 수집만 맡는 VM을 따로 만들고, Tailscale로 맥에서 원격 접속할 수 있게 한다."
tags: ["구축", "리눅스", "네트워크", "트러블슈팅"]
troubleshooting:
  - "설치 부팅 중 커널 패닉"
  - "Shutdown이 반응 없음"
draft: false
---

## 목표

논문 실측 수집만 맡는 VM을 따로 만들고, Tailscale로 맥에서 원격 접속할 수 있게 한다.

## A. VM 생성과 원격 접속

1. Proxmox에서 VM 102 `paper` 생성 (2코어, 메모리 1024MB, 디스크 20GB, Ubuntu 26.04 ISO)
2. Ubuntu Server 설치 — 설치 중 **Install OpenSSH server** 체크
3. VM 안에 Tailscale 설치 후 로그인

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4
```

1. 맥 터미널에서 `ssh <사용자>@<Tailscale IP>`로 접속

- 왜: Proxmox 콘솔은 복붙이 안 되고 집 밖에서 쓰기 어려움. Tailscale로 내부망 주소를 받으면 공유기 포트를 열지 않고도 어디서든 접속 가능

## B. 메모리 조정

- 설치 때 2GB로 올렸던 메모리를 1GB로 내림 (설치 후 사용률 약 17%)
- Proxmox에서 메모리 변경은 VM을 **완전히 껐다 켜야** 적용됨 (주황색 글씨 = 대기 중인 변경). Revert는 변경 취소 버튼

## 트러블슈팅

### 1. 설치 부팅 중 커널 패닉

- 증상: `Kernel panic - not syncing: No working init found`, 설치 화면이 뜨기 전에 멈춤
- 원인: 메모리 1GB. Ubuntu 설치 프로그램은 ISO 내용을 메모리에 올려서 실행하는데 1GB로는 부족
- 해결: Stop으로 강제 종료 → 메모리 2GB로 올려 설치 → 설치 후 1GB로 복귀
- 재발 방지: 설치할 때는 2GB 이상, 운영 사양은 설치 후에 조정

### 2. Shutdown이 반응 없음

- 증상: Shutdown 확인을 눌러도 VM이 꺼지지 않음
- 원인(추정): QEMU Guest Agent가 없어 VM이 종료 신호를 처리하지 않음
- 해결: Stop으로 강제 종료 후 Start
- 영향: 재시작 동안 10.8 12:50 측정 1회 결측 (10.12 기록 확인)
