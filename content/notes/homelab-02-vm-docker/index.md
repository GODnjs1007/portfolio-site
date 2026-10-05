---
title: "홈랩 2단계 · VM 원격 접속과 Docker 환경 구성"
date: 2026-10-01
projects: ["homelab"]
step: 2
summary: "1단계에서 만든 Ubuntu VM에 맥북에서 SSH로 바로 접속할 수 있게 하고, Docker를 설치해 컨테이너를 실행할 수 있는 환경을 만든다."
tags: ["구축", "컨테이너", "보안", "리눅스", "트러블슈팅"]
troubleshooting:
  - "Proxmox 콘솔에 키보드 입력이 안 됨"
  - "docker run 시 permission denied"
  - "디스크를 40GiB 줬는데 18.5GB만 잡힘"
  - "tailscale: command not found"
draft: false
---

## 목표

1단계에서 만든 Ubuntu VM에 맥북에서 SSH로 바로 접속할 수 있게 하고, Docker를 설치해 컨테이너를 실행할 수 있는 환경을 만든다. 같은 구성으로 산학프로젝트용 VM을 하나 더 만들어 개인 포트폴리오와 산학 작업을 VM 단위로 분리한다.

## 진행 과정

## A. VM 원격 접속 (Tailscale·SSH)

### 필요한 이유

- 1단계에서 Tailscale은 Proxmox 호스트에만 설치함. 밖에서 Proxmox 웹 UI는 열리지만 그 안의 VM에는 직접 접속할 수 없음
- VM도 독립된 컴퓨터라 Tailscale을 따로 설치해야 함
- Proxmox 콘솔(noVNC)은 복붙이 안 돼서 작업이 불편함. SSH로 맥북 터미널에서 작업하기 위함

### 1. VM 업데이트 (Proxmox 콘솔)

```bash
sudo apt update && sudo apt upgrade -y
```

- `sudo`: 이번 명령만 관리자 권한으로 실행

### 2. VM에 Tailscale 설치 (Proxmox 콘솔)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4
```

### 3. 맥북에서 SSH 접속

```bash
ssh <사용자>@<VM의 Tailscale 주소>
```

- 처음 접속 시 호스트 확인 질문에 `yes`
- 이후 작업은 맥북 터미널에서 진행

<!-- 이미지: 2-2A-01 맥북에서 Tailscale 주소로 산학 VM(101) SSH 접속 성공 -->

### 접속 주소 정리

| 대상 | 역할 | Tailscale | 집 내부 IP |
| --- | --- | --- | --- |
| pve | Proxmox 호스트 | `<Tailscale IP>` | `<내부 IP>` |
| 100 portfolio | 개인 포트폴리오 | `<Tailscale IP>` | `<내부 IP>` |
| 101 | 산학프로젝트 | `<Tailscale IP>` | `<내부 IP>` |

- 내부 IP는 DHCP로 받은 값이라 바뀔 수 있음

## B. Docker 설치

### 필요한 이유

- 1번 프로젝트 8단계에서는 맥에 Docker를 설치해 이미지를 만들었음. 이번에는 상시 가동하는 서버(VM)에 설치해서 포트폴리오 사이트와 산학 서버를 컨테이너로 띄울 준비

### 1. 설치

```bash
curl -fsSL https://get.docker.com | sudo sh
```

<!-- 이미지: 2-2B-01 get.docker.com 스크립트로 Docker Engine 29.8.2 설치 -->

### 2. sudo 없이 쓰도록 권한 부여

```bash
sudo usermod -aG docker $USER
exit
```

- `docker` 그룹에 현재 사용자를 추가
- 그룹 권한은 로그인할 때 읽기 때문에 나갔다가 다시 접속해야 반영됨

### 3. 동작 확인

```bash
groups
docker run hello-world
```

- `groups` 결과에 `docker`가 있어야 함
- `Hello from Docker!` 출력 확인
- portfolio, 산학 VM 두 VM 모두 완료

## C. 산학용 VM 추가와 디스크 확장

### 1. 산학 VM 생성

| 항목 | 값 |
| --- | --- |
| VM ID | 101 |
| Disk | 40GiB |
| CPU | 4 cores, Type host |
| Memory | 6144 MiB |

- 산학프로젝트는 부하테스트를 해야 해서 portfolio(4096 MiB)보다 메모리를 더 배정
- 기업 데이터는 여기에 두지 않음
- Ubuntu 설치 시 Storage 화면에서 `Set up this disk as an LVM group` 체크 해제 → 루트에 39GB 전부 할당됨
- 이후 과정(업데이트, Tailscale, SSH, Docker)은 portfolio와 동일

### 2. portfolio 디스크 확장

- portfolio는 설치 시 LVM 기본값 그대로라 40GiB 중 18.5GB만 루트에 할당돼 있었음 (트러블슈팅 3)

```bash
sudo lvextend -l +100%FREE -r /dev/ubuntu-vg/ubuntu-lv
df -h /
```

- `+100%FREE`: 남은 공간 전부를 논리 볼륨에 붙임
- `-r`: 파일시스템 크기도 같이 맞춤. 이게 없으면 늘린 공간을 쓸 수 없음
- 결과: 18.5GB → 38GB

## D. 보안·운영 설정

### 1. SSH 키 인증과 비밀번호 로그인 차단

- 비밀번호는 알거나 맞히면 누구나 들어올 수 있음. 키 방식은 맥북에 있는 개인키 파일이 있어야만 접속 가능
- 사이트를 외부에 공개하기 전에 먼저 적용

#### 키 생성과 등록 (맥북)

```bash
ssh-keygen -t ed25519
ssh-copy-id <사용자>@<Tailscale IP>
ssh-copy-id <사용자>@<Tailscale IP>
```

- `ssh-keygen`: 개인키(`id_ed25519`)와 공개키(`id_ed25519.pub`) 생성
- `ssh-copy-id`: 공개키를 VM의 `~/.ssh/authorized_keys`에 등록. 비밀번호는 이때 마지막으로 사용

#### 비밀번호 로그인 차단 (각 VM)

```bash
echo -e "PasswordAuthentication no\nKbdInteractiveAuthentication no" | sudo tee /etc/ssh/sshd_config.d/00-disable-password.conf
sudo sshd -t && sudo systemctl restart ssh
```

- `sshd -t`: 설정 문법 검사. 통과해야 재시작이 실행됨
- 파일 이름을 `00`으로 시작한 이유: sshd는 같은 항목이 여러 번 나오면 먼저 읽은 값을 쓰고, 이 폴더의 파일은 이름순으로 읽음. 다른 설정 파일에 비밀번호 허용이 남아 있어도 이 값이 우선함
- 설정 중에는 기존 접속 창을 닫지 않고 새 창에서 확인함. 설정이 잘못돼도 기존 창에서 되돌릴 수 있게 하기 위함

#### 확인

```bash
ssh -o PubkeyAuthentication=no <사용자>@<Tailscale IP>
```

- 키를 쓰지 않고 접속을 시도하면 `Permission denied (publickey)`로 거부됨. portfolio도 동일

<!-- 이미지: 2-2D-01 키 없이 접속 시 비밀번호를 묻지 않고 바로 거부됨 -->

- 참고
  - 현재 키가 등록된 기기는 맥북뿐. 다른 기기는 그 기기의 공개키를 `authorized_keys`에 추가해야 접속 가능
  - SSH가 막혔을 때는 Proxmox 웹 콘솔로 들어갈 수 있음
  - `sudo`는 여전히 비밀번호를 사용함. 막은 것은 접속 단계의 비밀번호

### 2. 스냅샷 저장

- 기본 세팅이 끝난 시점을 저장해두고, 이후 작업이 꼬이면 이 시점으로 되돌리기 위함
- VM → Snapshots → Take Snapshot (portfolio, 산학 VM 두 VM)

| 항목 | 값 |
| --- | --- |
| Name | base_setup |
| Include RAM | 해제 |
| Description | Ubuntu 26.04 + Tailscale + Docker + SSH 키 인증 |

- RAM을 뺀 이유: 실행 중인 메모리까지 저장하면 용량이 커지고 느려짐. 디스크 상태만 있으면 충분함
- 저장 위치: local-lvm(LVM-thin)에 `snap_vm-100-disk-0_base_setup` 형태로 생성됨

<!-- 이미지: 2-2D-02 portfolio VM의 스냅샷 목록. base_setup 아래 NOW가 현재 상태 -->

### 3. QEMU Guest Agent 설치

- 스냅샷 로그에 경고가 남음

```plain text
skipping guest filesystem freeze - agent configured but not running?
```

- 원인: VM 생성 시 Qemu Agent를 체크한 것은 Proxmox와 VM 사이의 통로만 연 것. VM 안에 에이전트 프로그램을 따로 설치해야 함

```bash
sudo apt install -y qemu-guest-agent && sudo systemctl start qemu-guest-agent
systemctl status qemu-guest-agent
```

- 두 VM 모두 `active (running)` 확인
- 효과: 스냅샷 시 파일시스템을 잠깐 멈춰 일관된 상태로 저장, Proxmox Summary에 VM IP 표시, Proxmox의 Shutdown으로 정상 종료
- base_setup 스냅샷은 에이전트 설치 전 시점임

### 남은 것

- BIOS 정전 후 자동 부팅: Boot 탭 `State After G3`가 현재 `S5 State`(꺼진 채 유지). 서버는 전원이 돌아오면 자동으로 켜져야 해서 `S0 State`로 변경 예정. 모니터 연결 필요

## 트러블슈팅

### 1. Proxmox 콘솔에 키보드 입력이 안 됨

- **증상**: 콘솔 화면을 클릭해도 입력이 들어가지 않음
- **원인**: 콘솔을 새 창(큰 콘솔)으로 열어두고, 실제 입력은 Proxmox 화면 안의 작은 콘솔 쪽으로 들어가고 있었음
- **해결**: 콘솔을 한 곳에서만 열고 그 화면을 클릭한 뒤 입력
- **참고**: 맥 입력기가 한글이면 콘솔이 키를 못 받을 수 있음. 영문으로 전환

### 2. docker run 시 permission denied

- **증상**

```plain text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

- **확인한 것**: `groups` 결과에 `docker`가 없음
- **원인**: `usermod -aG docker` 명령이 적용되지 않음
- **해결**: `sudo usermod -aG docker $USER` 재실행 → `exit` 후 다시 SSH 접속 → `docker run hello-world` 성공
- **재발 방지**: 그룹 변경 후에는 반드시 재로그인. 확인은 `groups`로

### 3. 디스크를 40GiB 줬는데 18.5GB만 잡힘

- **증상**: portfolio 로그인 화면에 `Usage of /: ... of 18.53GB`
- **원인**: Ubuntu Server 설치 시 LVM을 쓰면 기본으로 디스크의 일부만 루트 볼륨에 할당하고 나머지는 비워둠
- **해결**: `lvextend -l +100%FREE -r`로 남은 공간을 루트에 붙임 → 38GB
- **재발 방지**: 산학 VM은 설치 단계에서 LVM을 꺼서 처음부터 전체 할당

### 4. tailscale: command not found

- **원인**: 설치 전에 `tailscale ip -4`를 먼저 실행함
- **해결**: 설치 스크립트 실행 후 다시 실행

## 2단계 용어

- **SSH** : 다른 컴퓨터의 터미널에 암호화된 통로로 접속하는 방식. `ssh 아이디@주소`
- **noVNC** : Proxmox가 브라우저로 보여주는 VM 화면. 모니터를 직접 연결한 것과 같아서 복붙이 안 됨
- **sudo** : 명령 하나를 관리자 권한으로 실행
- **apt update / upgrade** : update는 설치 가능한 목록을 새로 받아오기, upgrade는 실제로 설치된 프로그램을 최신 버전으로 교체
- **그룹 (group)** : 사용자를 묶어 권한을 주는 단위. docker 그룹에 있으면 sudo 없이 docker 명령을 쓸 수 있음
- **docker.sock** : docker 명령이 Docker 데몬에 요청을 보내는 통로 파일. 여기 접근 권한이 없으면 permission denied
- **LVM** : 디스크를 한 번 더 추상화해서 볼륨 크기를 나중에 늘리거나 나눌 수 있게 해주는 방식
- **lvextend** : LVM 논리 볼륨의 크기를 늘리는 명령
- **파일시스템 (ext4)** : 디스크 공간에 파일을 어떻게 저장할지 정한 구조. 볼륨을 늘려도 파일시스템까지 늘려야 실제로 쓸 수 있음
- **df -h** : 디스크 사용량을 사람이 읽기 쉬운 단위(GB)로 보여주는 명령

## 배운 점

### A. VM 원격 접속 (Tailscale·SSH)

- Tailscale은 호스트 서버인 pve 서버에만 설치
  - host : VM을 품고 있는 본체 (pve)
  - BUT 각각의 VM에서도 Tailscale 필요
  - proxmox 콘솔 (noVNC) 은 복붙이 안 됨
    - proxmox가 브라우저로 보여주는 VM화면이라 모니터 꽂은 거랑 같아서 글자를 화면으로 보내는 거라 복붙이 X
- VM 업데이트

  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

  - apt update : 창고에 새 버전 목록만 가져오기
  - && : 앞에 거 성공하면 뒤에 거 실행
  - apt upgrade : 목록보고 실제로 설치
  - -y : 설치하는 질문에 미리 yes
- VM에 Tailscale 설치 (1장이랑 동일)

  ```bash
  curl -fsSL https://tailscale.com/install.sh | sh
  sudo tailscale up
  tailscale ip -4
  ```

- 노트북에서 SSH 접속

  ```bash
  ssh <사용자>@<Tailscale IP>
  ```

  - `<사용자>` : 계정
  - `<Tailscale IP>` : 주소
- 주소 정리
  1. pve : `<Tailscale IP>`
  2. portfolio : `<Tailscale IP>`
  3. 산학 VM(101) : `<Tailscale IP>`

### B. Docker 설치

<!-- 이미지: Docker 설치 부분 그림(캡션 없음). 바로 아래 '물리 서버 → 호스트 → VM → 게스트 OS → docker 엔진 → 컨테이너 → 애플리케이션' 계층 설명과 관련된 것으로 보임 -->

- 기초 개념 (큰 거에서 작은 순으로)
  - 물리 서버 → 호스트 (pve) → VM → 게스트 OS → docker 엔진 → 컨테이너 → 애플리케이션
    - 하이퍼바이저 : 물리서버의 CPU, memory, disk를 나눠서 여러 VM에 주는 프로그램 —> proxmox VE
    - 호스트 : VM들을 품고있는 본체
    - VM : 가상머신 , 하이퍼바이저가 만든 가짜 컴퓨터. CPU, memory, disk를 할당받고 자기 OS를 따로 가짐
    - 게스트 OS : VM에 깔린 OS (ubuntu 26.04)
    - 커널 : 하드웨어랑 프로그램 사이의 통역사.
    - 컨테이너 엔진 : 이미지로 컨테이너를 만들고 실행, 관리하는 프로그램 (docker Engine) —> 컨테이너를 만들고 키고 끄고 지우는 관리자
    - 이미지 : 프로그램 + 실행에 필요한 파일을 묶은 설계도 (nginx 이미지)
    - 컨테이너 : 이미지를 실제로 실행한 것 —> 실행중인 상자
    - 애플리케이션 : 컨테이너 안에서 실제로 일하는 프로그램
- docker 설치

  ```bash
  curl -fsSL https://get.docker.com | sudo sh
  ```

- sudo 없이 쓰도록 권한 부여

  ```bash
  sudo usermod -aG docker $USER
  exit
  ```

  - docker 그룹에 현재 사용자 추가
    - usermod : 사용자 설정 바꿈
    - -aG : 그룹에 추가 (append, Group)
    - docker : 넣을 그룹 이름
    - $USER : 지금 로그인 한 나 —> `<사용자>`로 자동바뀜
  - exit : 그룹 권한은 로그인할 때 읽으므로 재접속
- 동작 확인

  ```bash
  groups
  docker run hello-world
  ```

  - groups : 내가 가진 회원 목록 보기 (docker 있어야함)
  - docker run hello-world
    - hello-world 이미지 확인 —> 없으면 docker hub에서 받아옴 —> 그거로 컨테이너 만들어서 실행 —> Hello from docker! 출력하고 끝
      - docker 가 받고 만들고 실행 전부 되는지 테스트

### C. 산학용 VM 추가와 디스크 확장

- 산학용 VM : 앞 VM 설정과 같이 설정
  - memory만 6144MiB으로 설정 (부하테스트 실행 이유)
    - 부하테스트 : 일부로 일을 많이 줘서 얼마나 버티는지 재는 것
  - set up this disk as an LVM group 체크 해제 —> 루트에 39GB 전부할당
- portfolio 디스크 확장
  - 단어 정리
    - 디스크 : 물리 저장 공간
    - LVM : 땅을 나중에 늘리거나 나눌 수 있게 관리하는 방식
    - 논리 볼륨 : LVM으로 울타리 친 구역
    - 파일 시스템 : ext4 : 파일 정리하는 규칙
    - 루트 : 리눅스의 최상위 폴더

  ```bash
  sudo lvextend -l +100%FREE -r /dev/ubuntu-vg/ubuntu-lv
  df -h /
  ```

  - lvextend : 논리 볼륨 늘리기
  - +100%FREE : 남은 공간 전부를 논리 볼륨에 붙임
  - -r : 파일 시스템 크기도 같이 맞춤
  - /dev/ubuntu-vg/ubuntu-lv : 늘릴 논리 볼륨 이름
  - df -h / : 루트(/)가 지금 크기가 몇 인지 확인 (h는 사람이 읽기 쉬운 단위인 GB로 표현)

### D. 보안·운영 설정

- SSH 키 인증과 비밀번호 로그인 차단
  - 비밀번호는 누구나 알면 들어올 수 있음.
  - 해결방법 : 키 방식
    - 공개키 : 서버에 걸어두는 쪽.
    - 개인키 : 내 컴퓨터에만 있는 쪽.
    - 키 인증 : 개인키로 공개키를 여는 접속 방식
  - ssh-keygen : 공개키와 개인키 한 쌍 만들기
  - -t ed25519 : 만드는 방식
    - 결과 : id_ed25519.pub (공개키, pub → public : 공개) , id_ed25519 (개인키)
  - ssh-copy-id `<사용자>@<Tailscale IP>`
    - 공개키를 자동으로 VM에 걸어주는 명령어
  - ~/.ssh/authorized_keys
    - 내 SSH  설정 폴더에 허락된 공개키 목록 파일

```bash
ssh-keygen -t ed25519
ssh-copy-id <사용자>@<Tailscale IP>
```

- 비밀번호 로그인 차단 (기존 접속 창은 닫지 않고 새로운 창 띄워서 확인)

  ```bash
  echo -e "PasswordAuthentication no\nKbdInteractiveAuthentication no" | sudo tee /etc/ssh/sshd_config.d/00-disable-password.conf

  sudo sshd -t && sudo systemctl restart ssh
  ```

  - echo : 글자 출력
  - -e , \\n : \\n을 줄바꿈으로 인식
  - passwordAuthentication no : 비밀번호 로그인 끄기
  - KbdInteractiveAuthentication no : 비밀번호 다른 입력 방식 끄기
  - | sudo tee SSH서버 설정 폴더 : 글자를 관리자 권한으로 파일에 저장
    - 파일 이름 00으로 시작한 이유 : 00으로 시작하면 제일 먼저 읽혀서 다른 파일에 비밀번호가 허용되는 게 있어도 먼저 이게 읽힘
  - sshd : SSH 접속을 받아주는 서버 프로그램
  - -t : 문법 검사
- 확인

  ```bash
  ssh -o PubkeyAuthentication=no <사용자>@<Tailscale IP>
  ```

  - 키를 쓰지 않고 접속 시도하면 permission denied (publickey)로 거부됨
    - 열쇠 없으면 안 된다는 줄 —> 차단 성공
    - pubkeyAuthentication=no : 열쇠없이 접속 시도
    - -o : 옵션 지정
- 스냅샷 저장
  - 스냅샷 : VM의 지금 상태를 저장한 세이브 포인트
    - include RAM 해제 (디스크 상태만 저장)
    - LVM-thin : 스냅샷을 바뀐 부분만 저장
    - NOW : 지금 현재 상태 위치
- QEMU Guest Agent
  - agent configured but not running? → 통로는 있는데 받는 사람이 없을 때 뜸
  - QEMU : proxmox가 VM을 돌릴 때 쓰는 엔진 이름
  - Guest Agent : VM 안에 있는 도우미 프로그램. proxmox 말을 VM에게 전달

  ```bash
  sudo apt install -y qemu-guest-agent
  ```

  - 스냅샷 때 깨끗하게 저장. proxmox에 VM IP 표시.
