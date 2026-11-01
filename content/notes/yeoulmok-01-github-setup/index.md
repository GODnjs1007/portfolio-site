---
title: "여울목 1단계 · 깃허브 세팅"
date: 2026-10-29
projects: ["yeoulmok"]
step: 1
summary: "서버 코드를 올릴 GitHub 저장소를 팀 조직 아래 만들고, 홈랩 서버 VM에서 바로 받고 올릴 수 있게 연결한다."
tags: ["GitHub", "Proxmox", "SSH", "배포 키"]
troubleshooting:
  - "조직 저장소에 배포 키를 추가할 수 없음"
  - "\"Key is already in use\"로 배포 키 등록 실패"
  - "API 키를 불러왔는데 값이 비어 있음"
draft: false
---

## 목표

서버 코드를 올릴 GitHub 저장소를 팀 조직 아래 만들고, 홈랩 서버 VM에서 바로 받고 올릴 수 있게 연결한다.

## A. GitHub 조직과 서버 저장소

- 조직 `yeoulmok` 생성 (Free, 개인 계정 소속), 팀원 초대 후 Owner로 변경
  - 조직(Organization): 여러 사람이 저장소를 같이 관리하는 GitHub 팀 계정
  - Owner: 조직의 모든 저장소와 설정을 관리할 수 있는 권한
- 조직 안에 서버 저장소 `yeoulmok/server` 생성 (Public, README, .gitignore Python)
  - Public: 공고 의무가 GitHub 공개라서. API 키는 저장소 밖에 두므로 공개해도 안전
- 앱·웹 저장소는 팀원이 조직 안에 따로 만듦. 이슈·PR 규칙은 저장소마다 각자 정함
- 처음 개인 계정에 만든 저장소는 삭제하고, 인수인계 문서와 `.env.example`만 새 저장소로 옮김

## B. 서버 VM과 저장소 연결

- 홈랩 미니PC(Proxmox)에 여울목 전용 VM 생성

| 항목 | 값 |
| --- | --- |
| 이름 / 번호 | `yeoulmok` / VM 104 |
| 사양 | 2코어 / 4GB / 디스크 28GB (LVM 확장) |
| OS | Ubuntu 26.04 |
| 접속 | Tailscale, 기기 이름으로 SSH 접속 (IP 말고 이름으로) |
| SSH 키 | 맥·윈도우 데스크톱 등록 완료 |
| 설치 | Docker |

- LVM 확장: 디스크를 늘린 뒤 리눅스 쪽 파티션도 같이 늘려야 실제로 쓸 수 있음
- Tailscale: 집 밖에서도 내 기기끼리 사설망처럼 접속하게 해주는 VPN. 기기 이름으로 접속 가능
- 도메인 계획 (아직 연결 안 함): `yeoulmok.ihaewon.com`, Cloudflare 터널 (커리어 내비와 같은 방식)
  - 웹과 API는 같은 주소에 두고 API는 `/api/...`로 나눔. `api.yeoulmok.ihaewon.com` 같은 두 단계 서브도메인은 Cloudflare 무료 인증서가 안 돼서
- 작업 시작할 때: VM에 SSH 접속 → `cd ~/yeoulmok && git pull`
- VM `yeoulmok`에서 배포 키 생성 → `yeoulmok/server` Settings → Deploy keys에 등록 (Allow write access 체크)
  - 배포 키(Deploy key): 저장소 하나에만 접근하는 SSH 키. 서버가 털려도 다른 저장소는 안전
  - Allow write access: 체크해야 VM에서 push 가능. 안 하면 clone·pull만 됨
- `~/.ssh/config`에 `IdentityFile ~/.ssh/yeoulmok_server` 지정 → GitHub 접속 때 이 키를 씀
- VM에서 `git clone git@github.com:yeoulmok/server.git ~/yeoulmok` → `ssh -T git@github.com`으로 `Hi yeoulmok/server!` 확인
- API 키는 VM `~/secrets/yeoulmok.env`에만 보관 (`chmod 600`). 저장소에는 키 이름만 적은 `.env.example`
  - .env.example: 필요한 키 이름만 적어둔 빈 양식 파일
  - 변수: `HRFCO_KEY`(한강홍수통제소), `KMA_KEY`(기상청). 키 값만 넣음 (트러블슈팅 3번 참고)
  - 불러오기: `set -a; source ~/secrets/yeoulmok.env; set +a`
- Claude GitHub 앱을 조직 `yeoulmok`에 설치 → Claude가 서버 저장소에 직접 push 가능
- 배포 키 등록 중 두 번 막힘 (트러블슈팅 1, 2번 참고)

## 트러블슈팅

### 1. 조직 저장소에 배포 키를 추가할 수 없음

- 증상 : `yeoulmok/server` Settings → Deploy keys에 "Disabled by yeoulmok"이라고 뜨고 추가 버튼이 없음
- 확인한 것 : 저장소 설정이 아니라 조직 정책으로 막혀 있다는 표시
- 원인 : 새로 만든 조직은 배포 키가 기본으로 꺼져 있음
- 해결 : 조직 설정에서 배포 키를 허용으로 바꿈
- 재발 방지 : 조직을 새로 만들면 배포 키 허용 여부부터 확인한다

### 2. "Key is already in use"로 배포 키 등록 실패

- 증상 : VM에 있던 기존 배포 키를 새 저장소에 등록하자 "Key is already in use"
- 확인한 것 : 같은 키가 개인 저장소에 등록돼 있었고, 지운 줄 알았던 그 저장소가 실제로는 남아 있었음 (`git ls-remote`로 확인)
- 원인 : 배포 키는 저장소 하나에만 붙을 수 있음. 기존 저장소가 살아 있어서 키가 거기 묶여 있었음
- 해결 : VM에서 새 키(`yeoulmok_server`)를 만들어 등록하고 `~/.ssh/config`의 IdentityFile을 바꿈
- 재발 방지 : 저장소를 옮기거나 새로 만들면 배포 키도 새로 만든다 (저장소 1개당 키 1개)
  - 배포 키는 저장소마다 다른 키여야 함. 같은 키를 두 저장소에 동시에 등록할 수 없음

### 3. API 키를 불러왔는데 값이 비어 있음

- 증상 : `~/secrets/yeoulmok.env`를 불러온 뒤 API를 호출했는데 키 값이 비어서 요청 실패
- 확인한 것 : env 파일에 키 값이 아니라 발급 페이지의 요청 URL을 통째로 붙여넣었음
- 원인 : URL 안의 `&`를 셸이 '뒤에서 실행' 기호로 읽어서 변수 값이 끊김
- 해결 : env 파일에 키 값만 넣음 (`HRFCO_KEY=값`)
- 재발 방지 : env 파일에는 값만 넣고, 특수문자가 있으면 따옴표로 감싼다
