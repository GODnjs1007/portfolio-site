---
title: "산학 실시간 심전도 처리 서버"
summary: "환자 여러 명의 심전도가 실시간으로 들어오는 서버를 팀으로 만들고, 그중 가상 환자 스트림 생성기와 부하테스트를 맡았습니다. 홈랩 VM 101에 팀 테스트 서버를 구축해 운영합니다."
role: "팀장 · 서버 (스트림 생성기·부하테스트)"
status: "진행 중"
category: "인프라"
stack: ["Python", "TCP", "Redis Streams", "Docker", "Prometheus", "Grafana", "PhysioNet"]
period: "2026.09 ~"
weight: 20
runsOn: "homelab"
mapLabel: "vm 101"
brief:
  why: "서버 1대가 환자 몇 명까지 지연 없이 버티는지 숫자로 재고, 병목을 찾아 개선하려고 생성기와 부하테스트를 맡았습니다."
  did:
    - "Proxmox ecg VM에 팀 테스트 서버 구성, 팀원 원격 접속"
    - "공개 데이터셋(PhysioNet)으로 가상 환자 스트림 생성기 작성"
    - "TCP 연결 방식과 메시지 형식 설계, 3리드 데이터 전송"
    - "수신부·Redis Streams·워커 연결과 전체 시연"
    - "Prometheus·Grafana를 붙여 환자 수별(6 → 20 → 50 → 100명) 부하테스트"
  verified:
    - "6·20·50명에서 유실 0, 워커 처리 지연 p95 약 13ms · 27ms · 54ms"
    - "100명에서 유실 0이지만 워커 하나(w0)의 p95가 120ms → 1,010ms로 계속 증가"
    - "원인: 환자를 3개 워커에 나누면 w0가 34명을 맡아 1초에 1.02초 분량 일을 해야 함. 워커 하나당 한계 약 33명"
steps:
  - { name: "가상 환자 스트림 생성기", status: "완료", note: "sanhak-01-stream-generator" }
  - { name: "서버 연결 방식 설계", status: "완료", note: "sanhak-02-protocol-design" }
  - { name: "TCP 전송과 3리드 데이터", status: "완료", note: "sanhak-03-tcp-3lead" }
  - { name: "수신부 연결과 전체 시연", status: "완료", note: "sanhak-04-receiver-demo" }
  - { name: "지연·유실 측정 스크립트", status: "완료" }
  - { name: "환자 수별 부하테스트와 모니터링", status: "완료", note: "sanhak-06-loadtest" }
  - { name: "병목 찾기와 최적화", status: "예정" }
next: "병목을 찾아 워커 수, 묶어서 처리(배치), 건당 처리 시간 줄이기로 개선할 계획입니다."
draft: false
---

## 개요

팀 5명(서버 2, AI 3) 중 팀장이자 서버 담당입니다. 공개 데이터셋(PhysioNet)만 사용했고, 기업 데이터와 기업 정보는 이 페이지에 쓰지 않습니다.

```plain text
생성기(나) → TCP 8000 → 수신부 → Redis Streams → 워커 → R파 검출 → AI 판정 → 화면
```

<!-- 작성 틀: 선택한 이유 / 배운 점 은 직접 작성 -->
