---
title: "LLM API 지연·오류 대응 정책 실측"
summary: "LLM API가 느리거나 오류를 낼 때 기다리기·같은 API 재시도·다른 AI 전환 중 어떤 정책이 나은지 비교한 논문입니다. 홈랩 실측 VM에서 10분마다 자동으로 쌓은 기록 1,528건으로 세 정책을 시뮬레이션했습니다."
role: "단독 저자 · 실측 환경 구성과 분석"
status: "학술대회 투고 완료 · 11월 심사 결과 발표"
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
    - "크레딧 소진(402)으로 7일치 기록이 무효가 된 것을 찾아 원인 확인 후 재충전·재수집"
    - "기록 하나로 세 정책 × 타임아웃 3가지를 다시 계산하는 시뮬레이션 코드 작성"
    - "2쪽 논문 작성, 한국인공지능융합기술학회 추계학술대회 투고 (포스터 발표)"
  verified:
    - "10.8 11:10 첫 자동 기록 확인, 이후 날짜별 기록 수로 빠짐없이 쌓이는지 점검"
    - "타임아웃을 p95(2.80초)보다 짧게 두면 추가 호출 35.6%, p95가 5.19초(재시도)·7.44초(전환)로 오히려 늘어남"
    - "p99보다 조금 긴 3.5초에서는 추가 호출 0.65%, 지연은 기다리기와 같음"
    - "실제 장애 1회(Gemini SSL 오류)는 다른 AI로 전환한 경우에만 복구됨"
steps:
  - { name: "paper VM 생성과 원격 접속", status: "완료", note: "paper-01-vm" }
  - { name: "API 키 준비와 보관", status: "완료", note: "paper-02-api-keys" }
  - { name: "측정 스크립트 작성", status: "완료", note: "paper-03-probe-script" }
  - { name: "cron 자동 실행과 수집 확인", status: "완료", note: "paper-04-cron" }
  - { name: "정책 시뮬레이션과 결과", status: "완료", note: "paper-05-sim" }
  - { name: "수집 중지 → 데이터 백업 → 학술대회 투고", status: "완료" }
  - { name: "API 키 폐기 → 심사 결과 → 포스터 발표", status: "예정" }
next: "API 키를 폐기하고, 11.3 심사 결과를 확인한 뒤 11.20~21 학술대회에서 포스터로 발표합니다."
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
