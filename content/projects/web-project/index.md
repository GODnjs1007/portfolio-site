---
title: "MiCAL · 학사·학과·장학금 일정 통합 캘린더"
summary: "학교·학과 학사일정, 장학금, 비교과, 공모전, 런어스 과제처럼 여러 홈페이지에 흩어진 일정을 한 캘린더로 모아 보여주는 웹 서비스입니다. 웹프로그래밍 5인 조별 과제로 만들고 있고, 백엔드·DB·서버를 맡았습니다. 홈랩 VM 105에서 calendar.ihaewon.com으로 공개해 두었습니다."
role: "조원 · 백엔드·DB·서버"
status: "1차 기획 제출 · 2차 구현 중"
category: "서비스"
stack: ["Django 5.2", "Django REST Framework", "PostgreSQL 16", "Docker Compose", "Nginx", "Cloudflare Tunnel", "자체 서버(Proxmox)"]
period: "2026 2학기"
alsoOn:
  host: "homelab"
  via: "서버"
  label: "vm 105"
  title: "MiCAL 서버"
tone: "#C49A32"
weight: 29
mapLabel: "웹프"
brief:
  why: "학사일정, 학과 공지, 장학금, 비교과, 공모전, 런어스 과제가 서로 다른 홈페이지에 흩어져 있어서 하나씩 찾아봐야 했습니다. 이 일정들을 한 캘린더로 모아 보여주는 서비스를 웹프로그래밍 조별 과제로 만들기로 했습니다."
  did:
    - "크롤러와 DB 사이 일정 JSON 형식(docs/data-format.md)을 정함. source + external_id가 같으면 덮어쓰는(upsert) 규칙으로 여러 번 수집해도 중복이 쌓이지 않게 설계"
    - "런어스는 아이디·비번을 받지 않고 사용자가 등록한 iCal URL을 주기적으로 받아오는 방식으로 결정"
    - "홈랩에 프로젝트 전용 VM 105를 만들고 Docker Compose로 frontend(nginx)·web(Django + gunicorn)·db(PostgreSQL 16) 컨테이너 구성. DB는 외부 포트 없음, nginx는 127.0.0.1:8080에만 열고 Cloudflare Tunnel로 공개 (공유기 포트 개방 없음)"
    - "Django · DRF로 회원가입·로그인(토큰 인증, 비밀번호 해시 저장)과 일정 조회·필터·개인 일정 API 작성. 공식 일정과 개인 일정을 owner로 나누고 부분 유니크 제약으로 중복 방지"
    - "nginx가 /api/·/admin/은 Django로, 나머지는 화면 파일로 나눠 한 주소에서 화면과 API를 같이 서비스 (CORS 설정 불필요)"
    - "서버 계정은 서버에서 직접 작업할 팀원(크롤링 담당)에게만 SSH 키 전용으로 발급하고, Tailscale도 이 VM 하나만 공유"
    - "DB 비번·Django 비밀키는 서버 .env에만 두고, 작업 로그에 노출된 비밀키는 새로 발급해 교체"
    - "프론트 팀 프로토타입에 연결 코드 파일 하나(prototype-api.js)만 따로 붙여 실제 일정이 뜨게 연결. 프론트 팀 파일은 2줄만 수정"
  verified:
    - "백엔드 테스트 8개 통과 (해시 저장, 약한 비번 거절, 남의 개인 일정 안 보임, 공식 일정 삭제 막힘, import 중복 없음 등)"
    - "컨테이너 3개 기동(db healthy) 후 /api/health/ 200 OK, calendar.ihaewon.com/admin/ 관리자 로그인 확인"
    - "크롤링 데이터 742건 적재 (학사 168, 소프트웨어학부 2, 경영 6, 장학금 28, 공모전 24, 비교과 514). 재실행 시 새로 2 / 갱신 740 / 건너뜀 0으로 upsert가 설계대로 동작"
    - "리눅스 서버에서만 실패하던 학과 사이트 SSL 오류를 빠진 중간 인증서 등록으로 해결 (인증서 확인은 끄지 않음)"
    - "실제 데이터를 붙이자 주간 보기에서 같은 시간 일정 10개 이상이 찌그러지는 문제를 찾아 최대 2개 + '+N개 더'로 수정"
steps:
  - { name: "저장소와 서버 구축 (시안 배포까지)", status: "완료", note: "mical-01-repo-server" }
  - { name: "백엔드 배포와 데이터 적재 (DB 설계, 로그인·일정 API, 크롤링 데이터)", status: "진행 중", note: "mical-02-backend-data" }
  - { name: "화면과 API 연결", status: "진행 중", note: "mical-03-frontend-api" }
  - { name: "런어스 iCal 연동·크롤러 주기 실행", status: "예정" }
  - { name: "2차 과제 제출", status: "예정" }
next: "회원가입·로그인 화면을 연결하고(회원가입 때 런어스 URL 받기), 개인 일정을 브라우저 localStorage 대신 서버 API에 저장합니다. 장학금·공모전·비교과 분류를 화면에서 어떻게 묶을지 정하고, 크롤러 주기 실행(cron) 방식을 팀원과 결정한 뒤 런어스 iCal 연동으로 넘어갑니다."
draft: false
---

## 개요

여러 홈페이지에 흩어진 학교 일정을 한 캘린더로 모아 보여주는 웹 서비스 MiCAL(Merge in CAL)입니다. 1차는 기획 문서, 2차는 Frontend + Backend 구현 과제입니다. 저는 크롤링 결과를 받아 DB에 저장하고 화면에 API로 넘기는 서버 전체(DB 설계, Django API, 런어스 연동, 배포·운영)를 맡고, 팀원들이 PM·크롤링·화면 디자인과 프론트를 맡습니다.

```plain text
학교·학과 홈페이지 크롤링 ─┐
런어스 iCal URL 주기 수집 ──┼→ PostgreSQL → Django API → 캘린더 화면 (월·주·일)
개인 일정 입력 ─────────────┘
```

<!-- 작성 틀: 선택한 이유 / 배운 점 은 직접 작성 -->
