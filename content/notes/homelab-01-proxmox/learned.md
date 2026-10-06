---
title: "배운 점"
---

### A. Proxmox 설치와 초기 설정

- Proxmox VE : 가상컴퓨터 (VM)를 만들고 관리하는 데 특화된 OS
  - Debian : 리눅스 종류 중 하나. Proxmox 는 Debian 위에 만들어짐
  - ISO : 설치 CD를 파일 하나 만든 것
    - balenaEtcher : ISO를 USB에 굽는 프로그램 —> Proxmox VE ISO를 이 프로그램에 넣어서 USB 자체를 설치 CD로 바꿈
- BIOS : 전원 누르자마자 OS보다 먼저 켜지는 프로그램
  1. Advanced에서 VMX (Virtualization Technology) 활성화 : CPU의 가상 컴퓨터 만들기 기능 활성
     - proxmox는 이 cpu 기능을 빌려서 VM을 만듦. 꺼져있으면 빌리지를 못 함
  2. Boot 에서 Boot Option #1 을 USB를 1순위로 설정
     - UEFI : BIOS의 정식 이름.
  3. Security에서 Secure Boot를 끔 : 인증받은 OS만 켜지게 막는 보안기능을 끔. 윈도우 기준이라 우선 설정 끄고 시작
- 설치
  - Install Proxmox VE (Graphical) —> 마우스로 누르는 화면 방식
    - Filesystem : ext4 → 디스크에 파일 정리하는 규칙. 리눅스는 ext4
    - IP : `<내부 IP>`/24 —> 집 안 컴퓨터 주소
    - Gateway : `<내부 IP>` —> 공유기 주소 : 인터넷 나가는 문
  - 설치 후 재부팅 시 USB 제거 : 제거 안 하면 설치화면 다시
- 웹 UI 접속
  - `https://<내부 IP>:8006`
    - `<내부 IP>` : 미니피씨 주소
    - 8006 : 컴퓨터 포트 → proxmox 관리화면은 8006 사용. 웹사이트는 보통 80/443 사용
  - root/LinuxPAM으로 로그인
    - root : 리눅스 최고 관리자 계정
    - LinuxPAM : 리눅스 기본 로그인 방식
- 저장소 설정 및 업데이트
  - Repositories : 저장소 (프로그램, 업데이트 파일 받아오는 창고 서버)
    - 유료 회원으로 돼있는 설정들 변경
      - enterprise , ceph (저장장치 여러 대를 묶는 기능) 끔
      - no-Subscription : 킴
  - Refresh시 apt를 IPv6 연결 실패해서 IPv4 로 고정
    - Refresh : 창고에게 업데이트 여부 확인
    - apt : 창고에서 프로그램 받아오는 도구

### B. Tailscale 원격 접속

- 문제점 : `<내부 IP>` 는 집 안 (사설망)에만 통해서 밖에선 접속 불가
  - 사설망 : 집, 회사 안에서 쓰는 네트워크
  - 사설 IP  : 집 안에서만 통하는 주소
- Tailscale : 내 기기끼리만 쓰는 전용 통로 (VPN) 만들어 줌
  - VPN : 인터넷 위에 나만의 통로를 깔기
  - Tailscale : 그 VPN을 쉽게 만들어주는 서비스. 같은 계정끼리 묶어줌
  - 주소 : Tailscale을 깔면 기기마다 100.x.x.x 주소가 더 생김
    - 접속할 때 Tailscale 주소로 접속.
    - 같은 네트워크 내에선 기존 사설 IP로 접속 가능
    - 포트포워딩 : 밖에서 들어오는 원래 방법. (전 세계에 문을 여는 것) ↔ 메시 VPN : TailScale → 내 기기에게만 열림
- 설치
  - pve shell 에서 명령어 입력
    - curl -fsSL [https://tailscale.com/install.sh](https://tailscale.com/install.sh) | sh   —> 인터넷에서 설치 스크립트 받아서 바로 실행
      - curl : 인터넷에서 파일 받기
      - fsSL : 에러나면 멈추고 조용히 주소 바뀌면 따라가는 옵션 묶음
      - install.sh : 설치 스크립트
      - |: 앞 결과를 뒤로 넘기기
      - sh : 스크립트 실행
  - tailscale up 명령어
    - tailscale 실행 후 계정에 기기 등록 → 로그인 링크 나옴
  - tailscale ip -4
    - tailscale 주소 받기

### C. Ubuntu Server VM 생성

- ISO 업로드
  - local(pve) → ISO Images
    - local(pve) : proxmox 안의 파일 보관 창고
    - ISO Images : 창고 안의 설치 파일 칸
- VM 생성
  - VM ID : 100 (VM ID, proxmox는 100부터 시작)
  - NAME : portfolio
  - Qemu Agent : proxmox랑 VM이 대화하는 통로
  - Disk : VM에게 줄 저장공간
  - local-lvm : proxmox 안의 VM 디스크 전용 창고
  - SCSI : 디스크 연결 방식
  - Type : host —>  미니 피씨 CPU 기능을 그대로 VM에게 넘김
  - vmbr0 : proxmox 가상 스위치
  - virtIO : VM 전용 랜카드 방식
- Ubuntu 설치
  - Type of install : Ubuntu server : 기본판
  - Network : DHCP → `<내부 IP>`
    - DHCP : 공유기가 자동으로 주소 할당
    - proxmox(pve) : 설치 때 주소 직접 고정, VM : 자동으로 받음
  - OpenSSH server : 다른 컴퓨터에서 ssh로 원격 접속할 수 있게 받아주는 프로그램
- 로그인 확인
  - 콘솔에서 로그인 확인
  - Ubuntu 26.04.1 LTS
    - LTS : Long Term Support : 5년 이상 보안 업데이트 해주는 안정판
