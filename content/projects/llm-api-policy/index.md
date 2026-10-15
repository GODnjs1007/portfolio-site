---
title: "LLM API 지연·오류 대응 정책 실측"
summary: "LLM API가 느리거나 오류를 낼 때 기다리기·같은 API 재시도·다른 AI 전환 중 어떤 정책이 나은지 비교하는 논문입니다. 홈랩에 실측 VM을 따로 만들어 10분마다 자동으로 응답시간을 기록합니다."
role: "논문 작성 · 실측 환경 구성"
status: "실측 중 · 10월 학술대회 제출 예정"
category: "연구"
stack: ["Proxmox VM", "Ubuntu", "Tailscale", "Python", "cron", "Gemini API", "OpenAI API"]
period: "2026.10"
weight: 41
mapLabel: "논문"
alsoOn:
  host: "homelab"
  label: "vm 102"
  title: "LLM API 논문 실측 서버"
relations: ["실측 → 홈랩 VM", "추계학술대회"]
brief:
  why: "논문 데이터를 모으는 일을 사람이 손대지 않아도 계속 도는 운영 자동화로 구성해보려고 했습니다."
  did:
    - "논문 실측 전용 VM(paper) 생성, Tailscale로만 접속"
    - "Gemini·OpenAI API 키를 선불 결제·자동 충전 끔으로 준비하고 코드와 분리해 보관"
    - "한 번 실행에 1차 호출·재시도·전환 기록을 한 줄로 남기는 측정 스크립트 작성"
    - "cron으로 10분마다 자동 실행 등록"
  verified:
    - "10.8 11:10 첫 자동 기록 확인, 이후 날짜별 기록 수로 빠짐없이 쌓이는지 점검"
steps:
  - { name: "paper VM 생성과 원격 접속", status: "완료", note: "paper-01-vm" }
  - { name: "API 키 준비와 보관", status: "완료", note: "paper-02-api-keys" }
  - { name: "측정 스크립트 작성", status: "완료", note: "paper-03-probe-script" }
  - { name: "cron 자동 실행과 수집 확인", status: "완료", note: "paper-04-cron" }
  - { name: "수집 중지 → 데이터 백업 → API 키 폐기", status: "예정" }
next: "10.18까지 수집한 뒤 중지하고, 데이터를 백업한 다음 API 키를 폐기합니다."
draft: false
---

## 개요

```plain text
cron(10분마다) → probe.py → 1차 호출·재시도 대용 → Gemini API
                          → 동시 호출(전환 대용) → OpenAI API
                          → logs/probe_날짜.jsonl
```

<!-- 투고 → "투고", 심사 통과 → "게재 승인", 발표 후 → "발표"로 status만 바꿈 -->
<!-- 작성 틀: 선택한 이유 / 배운 점 은 직접 작성 -->
