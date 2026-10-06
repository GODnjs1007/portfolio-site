---
title: "홈랩 1단계 · Proxmox 설치와 원격 접속 구성"
date: 2026-09-30
projects: ["homelab"]
step: 1
summary: "미니PC(FIREBAT F2)에 Proxmox VE를 설치해 물리 서버 한 대 위에서 여러 VM을 운영할 수 있는 기반을 만든다."
tags: ["구축", "네트워크", "리눅스", "트러블슈팅"]
troubleshooting:
  - "USB로 부팅해도 윈도우로 넘어감"
  - "설치 직후 apt-get update 실패"
  - "No-Subscription 저장소 연결 실패 (IPv6)"
  - "Tailscale 인증 링크 404"
draft: false
---

## 목표

미니PC(FIREBAT F2)에 Proxmox VE를 설치해 물리 서버 한 대 위에서 여러 VM을 운영할 수 있는 기반을 만든다. 모니터 없이 웹 UI로 관리하고, Tailscale로 집 밖에서도 접속할 수 있게 구성한 뒤 첫 Ubuntu Server VM을 만든다. 1번 프로젝트에서 AWS가 대신 해주던 가상화와 네트워크를 직접 운영해보는 것이 목적이다.

## A. Proxmox 설치와 초기 설정

### 개요

- 장비: FIREBAT F2 (Intel i5-14450HX, RAM 16GB, NVMe 512GB), 유선 LAN
- OS: Proxmox VE 9.2 (Debian 13 trixie 기반)
- 기존 윈도우는 삭제하고 디스크 전체를 Proxmox에 할당

### 1. 설치 USB 준비

- Proxmox VE ISO를 받아 balenaEtcher로 USB에 구움
- ISO를 USB에 파일로 복사하는 것과 구우는 것은 다르다. 처음에 복사만 해서 부팅이 되지 않았음 (트러블슈팅 1)

### 2. BIOS 확인

- Advanced → CPU Configuration → Intel (VMX) Virtualization Technology: Enabled 확인
  - CPU의 가상화 기능. 꺼져 있으면 Proxmox에서 VM이 뜨지 않는다
- Boot → Boot Option #1: USB (UEFI)
- Security → Secure Boot: Disabled

### 3. 설치

- Install Proxmox VE (Graphical) 선택

| 항목 | 값 |
| --- | --- |
| Filesystem | ext4 |
| Disk | /dev/nvme0n1 |
| Country / Timezone | South Korea / Asia/Seoul |
| Keymap | en-us |
| Hostname | pve.home.lan |
| IP | `<내부 IP>`/24 |
| Gateway | `<내부 IP>` |

- 설치 후 재부팅 시 USB 제거. 콘솔에 웹 UI 주소가 표시되면 성공

### 4. 웹 UI 접속

- 데스크톱 브라우저에서 `https://<내부 IP>:8006` 접속
- 인증서 경고는 Proxmox가 직접 만든 자체 서명 인증서라서 뜨는 것. 집 안 네트워크라 그대로 진행
- root / Linux PAM으로 로그인
- No valid subscription 창은 유료 지원 안내일 뿐 기능 제한 없음
- 이후 모니터·키보드는 분리. 네트워크 설정이 꼬여 웹 접속이 안 될 때만 다시 연결

<!-- 이미지: 2-1A-01 Proxmox 웹 UI. VM 2개(portfolio, 산학 VM) 실행 중 -->

### 5. 저장소 설정과 업데이트

- pve → Updates → Repositories
  - pve-enterprise, ceph enterprise 비활성화
  - No-Subscription 저장소 추가
- Refresh 시 IPv6 연결 실패 → apt를 IPv4로 고정 (트러블슈팅 3)
- Upgrade 결과: Your System is up-to-date (받은 ISO가 최신이라 받을 것 없음)

## B. Tailscale 원격 접속

### 필요한 이유

- `<내부 IP>`는 집 안(사설망)에서만 통하는 주소라 밖에서는 접속할 수 없다
- Tailscale은 내 기기끼리만 쓰는 전용 통로(VPN)를 만든다. 같은 계정으로 로그인한 기기끼리 어디서든 같은 네트워크에 있는 것처럼 연결된다
- 공유기 포트를 열 필요가 없어서 Proxmox 관리 화면이 인터넷에 노출되지 않는다

### 1. Proxmox 호스트에 설치

- pve → Shell

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

- 출력된 인증 링크를 브라우저에서 열고 구글 계정으로 로그인 → `Success.`
- 인증 대기 중 셀에서 Ctrl+C를 누르면 인증이 취소된다 (트러블슈팅 4)

```bash
tailscale ip -4
```

- Tailscale 주소(100.x.x.x) 확인. 밖에서는 이 주소로 접속

### 2. 맥북에 설치

- App Store에서 Tailscale 설치 → 같은 구글 계정으로 로그인
- 앱스토어용 애플 아이디와 Tailscale 로그인 계정은 별개

### 3. 접속 확인

- 맥북 브라우저에서 `https://<Tailscale 주소>:8006` → Proxmox 로그인 화면 확인

## C. Ubuntu Server VM 생성

### 1. ISO 업로드

- pve → local (pve) → ISO Images → Upload
- ubuntu-26.04.1-live-server-amd64.iso (2.73GiB)
- VM도 컴퓨터라 OS 설치 디스크가 필요하다. USB 대신 Proxmox 저장소에 ISO를 넣어두고 거기서 설치한다

### 2. VM 생성

| 항목 | 값 |
| --- | --- |
| VM ID / Name | 100 / portfolio |
| OS | Ubuntu Server 26.04.1 ISO |
| Qemu Agent | 체크 |
| Disk | 40GiB (local-lvm, SCSI) |
| CPU | 4 cores, Type host |
| Memory | 4096 MiB |
| Network | vmbr0, VirtIO |

- 미니PC RAM 16GB를 이후 만들 산학용 VM과 나눠 써야 해서 자원을 적당히만 배정. 필요하면 나중에 늘릴 수 있다

### 3. Ubuntu 설치

- Type of install: Ubuntu Server
- Network: DHCP로 `<내부 IP>` 할당
- Server name: portfolio
- OpenSSH server 설치 체크. 이후 맥북 터미널에서 SSH로 접속하기 위함

### 4. 로그인 확인

- Proxmox → 100 (portfolio) → Console에서 로그인 성공
- Ubuntu 26.04.1 LTS, IPv4 `<내부 IP>`

### 5. 이후 처리 (2단계에서 완료)

- 맥북에서 SSH 접속: VM에 Tailscale 설치 후 접속 성공
- 업데이트 적용: 21개 → 0개
- 루트 파티션 확장: 18.5GB → 38GB (`lvextend`)
- 자세한 내용은 2. VM 원격 접속과 Docker 환경 구성 참고

## 트러블슈팅

### 1. USB로 부팅해도 윈도우로 넘어감

- **증상**: BIOS에서 Boot Option #1이 USB인데도 윈도우 복구 화면이 뜨거나 윈도우로 부팅됨. Use a device로 USB를 골라도 동일
- **확인한 것**
  - BIOS Boot 탭에 USB(UEFI)는 정상 인식됨 → 부팅 순서 문제 아님
  - Secure Boot 비활성화 후에도 동일
  - USB를 데스크톱에 꼽아보니 기존 파일이 그대로 보임
- **원인**: ISO를 USB에 파일로 복사만 하고 굽지 않음. USB 안에 파일 하나가 들어간 것일 뿐 부팅 가능한 디스크가 아니었음
- **해결**: balenaEtcher로 ISO를 USB에 구움 → Proxmox 설치 화면 진입
- **재발 방지**: 제대로 구운 USB는 윈도우에서 열리지 않고 포맷 요청이 뜨는 게 정상. 기존 파일이 보이면 굽기가 안 된 것

### 2. 설치 직후 apt-get update 실패

- **증상**: Tasks에 `Error: command 'apt-get update' failed`
- **원인**: Proxmox 기본 저장소가 유료 구독자용 enterprise 저장소. 구독이 없어 거절됨
- **해결**: Updates → Repositories에서 enterprise 2개 비활성화, No-Subscription 저장소 추가

### 3. No-Subscription 저장소 연결 실패 (IPv6)

- **증상**

```plain text
Err:5 http://download.proxmox.com/debian/pve trixie Release
  Cannot initiate the connection to download.proxmox.com:80 (<퍼블릭 IP>). - connect (101: Network is unreachable)
```

- **확인한 것**: Debian 저장소([deb.debian.org](http://deb.debian.org), [security.debian.org](http://security.debian.org))는 정상으로 받아짐. Proxmox 저장소만 IPv6 주소(2400:...)로 접속을 시도하다 실패
- **원인**: 집 네트워크에 IPv6 경로가 없는데 apt가 IPv6로 접속을 시도함
- **해결**: apt가 IPv4만 쓰도록 설정 파일 추가

```bash
echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4
apt update
```

- **결과**: 이후 Update package database OK
- **참고**: Tasks 목록은 맨 위가 최신. 아래 빨간 줄은 수정 전 기록

### 4. Tailscale 인증 링크 404

- **증상**: `tailscale up` 후 링크를 복사하려고 Ctrl+C를 누름 → `context canceled`. 그 링크로 접속하면 Error 404 (만료)
- **원인**: 터미널에서 Ctrl+C는 복사가 아니라 실행 중인 프로그램을 중단하는 신호. 인증 링크는 해당 `tailscale up`이 대기하는 동안만 유효함
- **해결**: `tailscale up` 재실행 후 셀은 건드리지 않고 링크를 바로 인증 → `Success.`

## 1단계 용어

- **Proxmox VE** : 물리 서버 한 대 위에서 VM과 컨테이너를 만들고 관리하는 가상화 플랫폼. Debian 기반
- **하이퍼바이저** : 물리 컴퓨터의 자원(CPU, 메모리, 디스크)을 나눠 여러 VM에 나눠주는 소프트웨어. AWS에서 EC2를 띄울 때도 뒤에서 하이퍼바이저가 돌고 있다
- **VM** : 컴퓨터 안에 만든 가상 컴퓨터. 자기 OS를 통째로 가진다
- **ISO** : OS 설치 디스크를 파일 하나로 만든 것
- **굽기 (Flash)** : ISO를 USB에 썬서 USB 자체를 부팅 가능한 설치 디스크로 만드는 것. 파일 복사와 다르다
- **BIOS / UEFI** : 컴퓨터를 켜면 OS보다 먼저 실행되는 설정 화면. 부팅 순서, 하드웨어 기능을 여기서 켜고 끈다
- **VT-x (VMX)** : Intel CPU의 가상화 지원 기능. 꺼져 있으면 VM이 뜨지 않는다
- **Secure Boot** : 인증된 부팅 프로그램만 실행하게 막는 BIOS 보안 기능
- **저장소 (Repository)** : 패키지(프로그램)를 받아오는 서버. apt가 여기서 업데이트를 받는다
- **apt** : Debian/Ubuntu의 패키지 관리 도구. 설치·업데이트·삭제를 담당
- **IPv4 / IPv6** : 인터넷 주소 체계. IPv4는 192.168.x.x 같은 형식, IPv6는 2400:... 같은 긴 형식
- **사설 IP** : 집·회사 네트워크 안에서만 통하는 주소 (192.168.x.x 등). 밖에서는 접속할 수 없다
- **DHCP** : 공유기가 기기에 IP를 자동으로 나눠주는 방식
- **자체 서명 인증서** : 공인 기관이 아니라 서버가 스스로 만든 HTTPS 인증서. 암호화는 되지만 브라우저가 경고를 띄운다
- **Tailscale** : 내 기기끼리만 연결되는 VPN. 포트포워딩 없이 밖에서 집 서버에 접속할 수 있게 해준다
- **vmbr0** : Proxmox의 가상 네트워크 브리지. VM을 집 공유기 네트워크에 연결해주는 가상 스위치
- **VirtIO** : VM용으로 만든 가상 장치 방식. 실제 하드웨어를 흉내 내는 것보다 빠르다
- **SSH** : 다른 컴퓨터의 터미널에 암호화된 통로로 접속하는 방식. OpenSSH는 그 서버 프로그램
