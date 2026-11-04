---
title: "홈랩 8단계 · 홈랩 운영 점검"
date: 2026-11-02
projects: ["homelab"]
step: 8
summary: "운영 중인 VM 4대(portfolio, careernavi, yeoulmok, calendar)의 상태를 한 번에 점검하고, 시간대·스냅샷·Guest Agent·커널 버전을 통일해서 관리하기 쉬운 상태로 만든다."
tags: ["운영", "리눅스", "트러블슈팅"]
troubleshooting:
  - "엉뚱한 VM이 재부팅됨"
  - "yeoulmok \"Guest Agent not running\""
draft: false
---

## 목표

- 운영 중인 VM 4대(portfolio, careernavi, yeoulmok, calendar)의 상태를 한 번에 점검하고 설정 맞추기
- 시간대·스냅샷·Guest Agent·커널 버전을 통일해서 관리하기 쉬운 상태로 만들기

## A. 서버 현황 점검

- Mac에서 반복문 한 줄로 VM 3대(portfolio, careernavi, yeoulmok)의 상태를 한 번에 모음
  - 확인한 항목: OS, 커널, 시간대, 디스크, 계정, IP, Docker/Compose/cloudflared 버전, 컨테이너와 포트

```bash
for h in portfolio careernavi yeoulmok; do echo "=== $h"; ssh haewonlee@$h '
lsb_release -ds; uname -r; timedatectl show -p Timezone --value
df -h / | tail -1; ls /home; tailscale ip -4; hostname -I | cut -d" " -f1
docker --version; docker compose version --short; cloudflared --version | head -1
docker ps --format "{{.Names}} | {{.Image}} | {{.Ports}}"'; done
```

- VM 사양(코어·메모리·디스크·스냅샷)은 Proxmox 호스트 Shell에서 `qm`으로 확인
  - `qm`: Proxmox에서 VM을 다루는 명령어. VM 안이나 Mac이 아니라 **pve 호스트**에서만 동작함

```bash
for i in 100 103 104 105; do echo "=== $i"; qm config $i | grep -E '^(name|cores|memory|scsi0|net0|agent)'; qm listsnapshot $i; done
```

- 점검 당시 결과 (업데이트 전)

| 항목 | portfolio | careernavi | yeoulmok |
| --- | --- | --- | --- |
| 커널 | 7.0.0-34 | 7.0.0-38 | 7.0.0-42 |
| 시간대 | Etc/UTC | Etc/UTC | Etc/UTC |
| 디스크 사용 | 12G / 38G (33%) | 9.1G / 28G (35%) | 6.7G / 28G (26%) |
| Docker / Compose | 29.8.2 / 5.5.1 | 29.9.2 / 5.6.1 | 29.9.2 / 5.6.1 |
| cloudflared | 2026.10.0 | 2026.10.5 | 2026.10.7 |
| 대기 중 업데이트 | 48개 + 재시작 필요 | 18개 | 0개 |

- 정리한 결과로 각 프로젝트 페이지에 **서버 구성** 표를 추가함
- 발견한 점 (급하지 않음)
  - portfolio의 Grafana(3000)·Prometheus(9090), careernavi·yeoulmok의 API(8000)가 `0.0.0.0`으로 열려 있음 → 같은 공유기(LAN) 안에서 바로 접속 가능
  - 터널로만 쓰면 되니 나중에 `127.0.0.1`로 묶는 게 안전함
  - `0.0.0.0`: 모든 네트워크 인터페이스에서 접속을 받겠다는 뜻
  - `127.0.0.1`: 자기 자신(서버 내부)에서만 접속 가능

## B. 운영 설정 맞추기

- 시간대를 4대 모두 한국 시간으로 통일
  - 이유: 로그·크론 시간이 UTC면 9시간씩 헷갈림. 장애 볼 때 시간 맞추기가 제일 중요함

```bash
sudo timedatectl set-timezone Asia/Seoul && date
# Mon Nov  2 11:43:25 AM KST 2026
```

- 스냅샷 생성: careernavi(103), yeoulmok(104)에 `base_setup` 추가 (pve Shell)
  - 스냅샷: 특정 시점의 VM 상태를 저장해두는 것. 업데이트하다 망가지면 그 시점으로 되돌릴 수 있음
  - 업데이트 **전에** 찍어둔 게 포인트

```bash
qm snapshot 103 base_setup
qm snapshot 104 base_setup
```

| VM | 스냅샷 |
| --- | --- |
| 100 portfolio | base_setup (10/1) |
| 103 careernavi | base_setup (11/2) |
| 104 yeoulmok | base_setup (11/2) |
| 105 calendar | base-setup |

- yeoulmok에 Qemu Guest Agent 설치
  - Qemu Guest Agent: VM 안에서 돌면서 Proxmox에 IP·상태를 알려주고, 정상 종료·스냅샷을 도와주는 프로그램

```bash
sudo apt install -y qemu-guest-agent && sudo systemctl start qemu-guest-agent
systemctl is-active qemu-guest-agent   # active
```

- careernavi는 Proxmox 설정에서 Agent가 꺼져 있음 → 켜려면 VM 재시작이 필요해서 11/16 발표 이후로 미룸
- 저장소(thin pool) 사용량 확인: 23%로 여유 있음
  - thin LVM: 디스크를 실제로 쓴 만큼만 차지하는 방식. VM들에 할당한 합계가 실제 용량보다 커도 됨(오버프로비저닝)
  - 그래서 경고가 뜨지만, 실제 사용률이 높아지기 전엔 문제없음. 사용률만 주기적으로 보면 됨

```bash
lvs   # data  pve  twi-aotz--  Data% 23
```

## C. 커널 업데이트와 재부팅

- 업데이트가 밀려 있던 portfolio(48개, 재시작 필요)와 careernavi(18개)를 업데이트하고 재부팅

```bash
sudo apt update && sudo apt upgrade -y && sudo reboot
```

- 커널: OS의 핵심. 커널이 바뀌면 재부팅해야 새 버전이 적용됨
- `*** System restart required ***`: 업데이트는 됐는데 재부팅해야 적용된다는 표시
- 재부팅 후 확인한 것
  - 커널 버전, 컨테이너가 자동으로 다시 떴는지

```bash
uname -r          # 7.0.0-42-generic
docker ps         # 모든 컨테이너 Up
```

- careernavi: 약 1분 만에 복구. db / web / api 모두 Up
- portfolio: site, Grafana, Prometheus, cAdvisor, node-exporter 5개 모두 Up
- 컨테이너가 알아서 다시 뜬 이유: compose에 `restart` 정책이 걸려 있어서 Docker가 부팅 때 자동으로 올림
- 결과: VM 4대 모두 커널 `7.0.0-42`로 통일

| VM | 커널 | Docker / Compose | cloudflared |
| --- | --- | --- | --- |
| portfolio | 7.0.0-34 → 7.0.0-42 | 29.8.2 / 5.5.1 → 29.9.2 / 5.6.1 | 2026.10.0 → 2026.10.7 |
| careernavi | 7.0.0-38 → 7.0.0-42 | 29.9.2 / 5.6.1 | 2026.10.5 → 2026.10.7 |
| yeoulmok | 7.0.0-42 | 29.9.2 / 5.6.1 | 2026.10.7 |

## 트러블슈팅

### 1. 엉뚱한 VM이 재부팅됨

- 증상 : portfolio를 업데이트·재부팅하려고 했는데, careernavi가 재부팅됨
- 확인한 것
  - 이미 careernavi에 접속한 상태에서 `ssh haewonlee@portfolio`를 입력함
  - careernavi에는 portfolio로 가는 키가 없어서 접속이 실패함 (`Permission denied (publickey)`)
  - 그 다음 줄 `sudo apt upgrade -y && sudo reboot`이 careernavi에서 그대로 실행됨
- 원인
  - 프롬프트(`haewonlee@careernavi:~$`)를 확인하지 않고 명령어를 이어서 붙여넣음
  - 접속 실패를 못 보고 넘어감
- 해결
  - careernavi는 약 1분 뒤 정상 복구됨 (db / web / api Up, 커널 7.0.0-42로 업데이트됨)
  - `exit`로 Mac에 돌아온 뒤 portfolio에 다시 접속해서 업데이트·재부팅함
- 재발 방지
  - 재부팅·삭제처럼 되돌리기 어려운 명령 전에는 **프롬프트 확인** 또는 `hostname` 실행
  - 다른 서버로 갈 땐 서버 안에서 또 ssh하지 말고, `exit`로 Mac에 돌아와서 접속
  - ssh와 위험한 명령을 한 번에 붙여넣지 않기

### 2. yeoulmok "Guest Agent not running"

- 증상 : Proxmox 요약 화면에 yeoulmok의 IP가 안 뜨고 Agent가 실행 중이 아니라고 나옴
- 확인한 것
  - `qm config 104`에 `agent: 1` (Proxmox 쪽 설정은 켜져 있음)
  - VM 안에는 `qemu-guest-agent` 패키지가 설치돼 있지 않음
- 원인
  - Proxmox 설정만 켜고, VM 안에 Agent 프로그램을 설치하지 않음
  - 설치 직후에도 `disabled or a static unit, not starting it`이라며 자동 시작이 안 됨
- 해결

```bash
sudo apt install -y qemu-guest-agent && sudo systemctl start qemu-guest-agent
systemctl is-active qemu-guest-agent   # active
```

- 재발 방지
  - 새 VM 체크리스트에 "Proxmox Agent 체크 + VM 안에 qemu-guest-agent 설치" 둘 다 포함
  - 설치 후 `systemctl is-active`로 확인까지

## 남은 작업

- [ ] 외부에 열린 포트(3000, 9090, 8000)를 127.0.0.1로 묶기
- [ ] careernavi Qemu Guest Agent 켜기 (11/16 발표 이후)
