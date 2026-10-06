---
title: "배운 점"
---

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
