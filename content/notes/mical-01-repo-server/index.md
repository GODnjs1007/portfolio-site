---
title: "MiCAL 1단계 · 저장소와 서버 구축"
date: 2026-10-31
projects: ["web-project"]
step: 1
summary: "팀 저장소를 만들고 역할별 폴더를 나눈 뒤, 홈랩에 이 프로젝트 전용 VM을 만들어 프론트 시안을 calendar.ihaewon.com으로 외부 공개한다."
tags: ["Proxmox", "Docker", "Cloudflare", "트러블슈팅"]
troubleshooting:
  - "SSH 키를 등록했는데 계속 비번을 물어봄"
  - "32GB로 만든 VM 디스크가 14GB로 잡힘"
  - "calendar.ihaewon.com이 안 열림 (ERR_NAME_NOT_RESOLVED)"
draft: false
---

## 목표

팀 저장소를 만들고 역할별 폴더를 나눈 뒤, 홈랩에 이 프로젝트 전용 VM을 만들어 프론트 시안을 `calendar.ihaewon.com`으로 외부 공개한다.

## A. GitHub 저장소와 프로젝트 뼈대

- `campus-calendar` 저장소를 Private으로 만들고 팀원 4명 Collaborator로 초대
- 폴더를 담당별로 나눔 → 각자 자기 폴더에서만 작업해 충돌을 줄임
  - `backend/` Django API (이해원), `crawler/` 크롤러 (팀원), `frontend/` 디자인 시안 (팀원 2명), `docs/` 문서
- README에 회의 내용(문제, 타겟, 기능, 데이터 소스, MVP 범위), 역할, 기술 스택, 브랜치 규칙 정리
  - MVP: 최소 기능 제품. 2차 과제 안에 확실히 끝낼 범위(학사일정, 교내 장학금, 런어스)만 먼저 만듦
- `docs/data-format.md`에 크롤러가 넘길 일정 JSON 형식을 정함
  - 필드: `source`, `external_id`, `title`, `start_at`, `end_at`, `all_day`, `category`, `department`, `url`, `raw`
  - `source` + `external_id`가 같으면 새로 만들지 않고 덮어씀 → 크롤러가 여러 번 돌아도 일정이 중복으로 쌓이지 않음
  - upsert: 없으면 넣고(insert) 있으면 고침(update)
  - `raw`: 크롤링 원본을 통째로 보관. 파싱을 잘못했을 때 다시 긁지 않고 고칠 수 있음
- DB는 PostgreSQL로 정함. upsert(`ON CONFLICT`)와 시간대 처리(`timestamptz`)가 깔끔하고, 크롤러와 웹이 동시에 써도 잠기지 않음
  - SQLite는 동시에 쓰면 파일 전체가 잠겨서 서버용으로 제외
- `docker-compose.yml`에 PostgreSQL과 시안용 nginx를 넣음. 두 포트 모두 외부에 열지 않음 (nginx는 `127.0.0.1:8080`에만 묶음)
- `.env`는 `.gitignore`로 제외하고 키 이름만 적은 `.env.example`을 올림
- 런어스는 아이디·비번을 받아 크롤링하지 않고, Moodle 캘린더 내보내기(iCal URL)를 받아 주기적으로 수집하기로 함
  - iCal: 캘린더 일정을 주고받는 표준 형식. URL은 고정이고 요청할 때마다 그 시점 최신 일정을 돌려줌
  - 실시간 push가 아니라 서버가 주기적으로 다시 받는 방식(polling)이라 새 과제는 다음 주기에 반영됨

## B. 서버 VM 구축

- Proxmox에 VM 105 `calendar` 생성 (2코어, 4GB, 32GB, Ubuntu 26.04 Server, 계정 haewonlee)
  - 탭별 설정 : General 이름 `calendar` / OS Ubuntu Server ISO, Linux / System 기본값 + Qemu Agent 켬, TPM 끔 / Disks SCSI(VirtIO SCSI single), local-lvm, 32GB, IO thread, Discard 켬 / CPU 1소켓 2코어 / Memory 4096MB / Network vmbr0, VirtIO / Start after created
  - Ubuntu 설치 : 계정 haewonlee, OpenSSH server 설치, 추가 snap 패키지 없음
  - 2코어/4GB로 잡은 이유 : Django + PostgreSQL + 크롤러가 한 VM에 들어가도 충분하고, 모자라면 Proxmox에서 나중에 늘리면 됨
  - Qemu Agent: 켜면 Proxmox가 VM 안쪽 IP·상태를 알 수 있고 정상 종료도 가능
  - Discard: VM 안에서 지운 파일 공간을 미니PC 디스크로 돌려줌
  - TPM: 윈도우 11용 보안 칩. 우분투에는 필요 없어서 끔
- Tailscale 설치 후 `ssh haewonlee@calendar`로 접속
- 기초 세팅: apt 업데이트(40개 패키지), qemu-guest-agent·git·curl 설치, 타임존 Asia/Seoul (`date`로 KST 확인)
  - 타임존: 캘린더 서비스라 서버 시간이 한국 시간이어야 로그·크론 시각이 헷갈리지 않음
- 데스크톱 SSH 키 등록 → 비번 없이 접속 (트러블슈팅 1번 참고)
- Docker 29.9.2 설치 (`get.docker.com` 스크립트, Compose 플러그인 포함), haewonlee를 docker 그룹에 추가 → 재접속 후 `docker run --rm hello-world`로 확인
  - docker 그룹: 여기 들어가야 sudo 없이 docker 명령을 쓸 수 있음. 그룹 변경은 다시 로그인해야 적용됨
- 디스크를 14GB → 28GB로 확장 (트러블슈팅 2번 참고)
- 기초 세팅이 끝난 상태를 스냅샷 `base-setup`으로 저장
  - 스냅샷: VM의 그 순간 상태를 통째로 저장해두는 것. 설정을 망쳐도 이 시점으로 되돌릴 수 있음
- 저장소 전용 배포 키(`~/.ssh/campus_calendar`)를 만들어 Deploy keys에 등록하고 `~/.ssh/config`에 `Host github-calendar`로 지정
  - 여러 저장소 배포 키가 같은 VM에 있어도 Host 별칭으로 구분해서 쓸 수 있음
- 저장소를 `github-calendar` 별칭으로 `git clone`

## C. 시안 배포와 도메인 연결

- 프론트 시안(색상 4종, 정적 HTML·CSS)을 `frontend/`에 올림
  - 시안과 같이 온 `generate.cjs`는 옛날 레이아웃을 만드는 스크립트라 실행하면 지금 시안을 덮어써서 제외
- VM에서 `docker compose up -d frontend` → `curl -I localhost:8080`으로 `200 OK` 확인
  - nginx 컨테이너가 `frontend/` 폴더를 읽기 전용으로 보고 있어서, 시안을 고치면 `git pull`만 하면 바로 반영됨
  - 띄운 직후 첫 curl은 `Connection reset`. nginx가 아직 준비 전이라 다시 치니 정상
- Cloudflare Tunnel `calendar` 생성 → VM에 cloudflared를 서비스로 설치 → Healthy 확인
  - 서비스로 설치해서 재부팅해도 자동으로 다시 연결됨
- Route 추가: `calendar.ihaewon.com` → `http://localhost:8080`
  - Route: 이 주소로 들어오면 터널 안의 어느 서비스로 보낼지 정하는 규칙. 추가하면 DNS에 CNAME이 자동으로 생김
  - CNAME: 이 주소는 저 주소의 별칭이라고 알려주는 DNS 레코드
- 공유기 포트는 열지 않음. 밖에서는 Cloudflare를 거쳐서만 들어옴
- [https://calendar.ihaewon.com](https://calendar.ihaewon.com) 에서 시안 비교 화면 확인
- 처음에 이름을 `calender`로 잘못 만들어 주소가 안 열림 (트러블슈팅 3번 참고)

## 트러블슈팅

### 1. SSH 키를 등록했는데 계속 비번을 물어봄

- 증상 : 키 등록 명령어를 두 번 쳐도 `ssh haewonlee@calendar` 할 때마다 비번을 물어봄
- 확인한 것 : 명령어를 친 프롬프트가 `haewonlee@calender:~$`였고, `type: :USERPROFILE.sshid_ed25519.pub: not found` 에러가 떴음
- 원인 : 데스크톱 PowerShell에서 쳐야 하는 명령어를 VM 안에서 침. 리눅스는 `$env:USERPROFILE`을 모르니 올릴 키를 못 찾음
- 해결 : `PS C:\Users\이해원>` 프롬프트에서 다시 침 → 비번 없이 접속됨
- 재발 방지 : 명령어 치기 전에 프롬프트로 어디인지 확인한다
  - `PS C:\...>` = 데스크톱 (키 등록, ssh 접속)
  - `haewonlee@calendar:~$` = VM 안 (apt, docker, git)

### 2. 32GB로 만든 VM 디스크가 14GB로 잡힘

- 증상 : 로그인 화면에 `Usage of /: 44.2% of 13.67GB`
- 확인한 것 : Proxmox에서는 32GB로 만듦
- 원인 : Ubuntu 설치 기본값이 LVM을 쓸 때 디스크 절반만 루트(`/`)에 잡고 나머지는 비워둠
  - LVM: 디스크를 유연하게 나눠 쓰는 방식. 나중에 크기를 늘릴 수 있음
- 해결 : `sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv` → `df -h /`로 28GB 확인
  - `-r`: 볼륨을 늘린 뒤 파일 시스템(ext4)도 같이 늘림
- 재발 방지 : VM 기초 세팅 순서에 디스크 확장을 넣음

### 3. calendar.ihaewon.com이 안 열림 (ERR_NAME_NOT_RESOLVED)

- 증상 : 터널은 Healthy인데 브라우저에서 "서버 IP 주소를 찾을 수 없습니다". `ssh haewonlee@calendar`도 `Could not resolve hostname`
- 확인한 것 : Route 화면에 `calender.ihaewon.com`(e)으로 등록돼 있었음. VM hostname, Tailscale 이름, 터널 이름, Proxmox VM 이름도 전부 `calender`
- 원인 : Ubuntu 설치 때 서버 이름을 `calender`로 입력하고 그 뒤로 같은 이름을 그대로 씀. 주소는 `calendar`(a)로 쳐서 없는 주소가 됨
- 해결 : Route Subdomain을 `calendar`로 수정 (DNS의 CNAME도 자동으로 바뀜). 나머지 이름도 맞춤
  - `sudo hostnamectl set-hostname calendar` + `/etc/hosts` 수정
  - `sudo tailscale set --hostname=calendar`
  - Proxmox VM 이름, Cloudflare 터널 이름도 `calendar`로 변경
  - 데스크톱에서 `ipconfig /flushdns`
- 재발 방지 : VM 만들 때 정한 이름을 한 번 복사해두고 Ubuntu 설치, Tailscale, 터널, Route에 그대로 붙여넣는다
  - 밖에서 보이는 건 Route 주소뿐이라 나머지 이름이 틀려도 서비스는 돌아감. 그래도 관리할 때 헷갈리니 맞추는 게 좋음
