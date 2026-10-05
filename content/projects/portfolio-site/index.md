---
title: "이 포트폴리오 사이트"
summary: "Hugo로 만든 정적 사이트를 홈랩 VM의 Docker Nginx 컨테이너에서 직접 운영합니다. 지금 보고 계신 페이지입니다."
role: "개인 프로젝트"
status: "진행 중"
category: "인프라"
stack: ["Hugo", "PaperMod", "Docker", "Nginx", "GitHub"]
period: "2026.10 ~"
featured: true
weight: 3
mapLabel: "vm 100"
runsOn: "homelab"
here: true
brief:
  why: "만든 것과 겪은 문제를 한곳에 쌓아두고, 그 사이트 자체도 직접 운영하는 서버 위에 올리려고 만들었습니다."
  did:
    - "Hugo로 사이트 구성, GitHub 저장소로 관리"
    - "VM 100에서 빌드 결과를 Nginx 컨테이너가 읽기 전용으로 서빙"
    - "프로젝트·기록을 Markdown 파일만 추가하면 목록과 지도에 반영되는 구조로 설계"
steps:
  - { name: "Hugo 사이트 구성과 GitHub 업로드", status: "완료", note: "homelab-03-site-deploy" }
  - { name: "VM 100 Docker Nginx 배포", status: "완료", note: "homelab-03-site-deploy" }
  - { name: "사이트 구조·디자인 개편", status: "진행 중" }
  - { name: "도메인·HTTPS 외부 공개", status: "예정" }
next: "도메인과 HTTPS를 붙이고, push하면 자동으로 다시 배포되게 만듭니다."
draft: false
---

## 개요

배포 과정은 홈랩 3단계 기록과 같은 작업이라, 자세한 내용은 그 기록에 모아두었습니다.
