---
title: "산학 실시간 심전도 처리 서버"
summary: "환자 여러 명의 심전도가 실시간으로 들어오는 서버를 팀으로 만들고, 그중 가상 환자 스트림 생성기와 부하테스트를 맡았습니다. 홈랩 VM 101에 팀 테스트 서버를 구축해 운영했고, 공개 데이터로 기준 AI 모델을 학습해 정확도와 판정 속도를 비교했습니다."
role: "팀장 · 서버 (스트림 생성기·부하테스트) · 기준 AI 모델"
status: "진행 중"
category: "인프라"
stack: ["Python", "TCP", "MQTT", "Redis Streams", "Docker", "Prometheus", "Grafana", "PyTorch", "PhysioNet"]
period: "2026.09 ~"
weight: 20
mapLabel: "산학"
alsoOn:
  host: "homelab"
  label: "vm 101"
  title: "산학 테스트 서버"
  off: true
relations: ["테스트 서버 → 홈랩", "산학 논문"]
brief:
  why: "서버 1대가 환자 몇 명까지 지연 없이 버티는지 숫자로 재고, 병목을 찾아 개선하려고 생성기와 부하테스트를 맡았습니다."
  did:
    - "Proxmox ecg VM에 팀 테스트 서버 구성, 팀원 원격 접속"
    - "공개 데이터셋(PhysioNet)으로 가상 환자 스트림 생성기 작성"
    - "TCP 연결 방식과 메시지 형식 설계, 3리드 데이터 전송"
    - "수신부·Redis Streams·워커 연결과 전체 시연"
    - "Prometheus·Grafana를 붙여 환자 수별(6 → 20 → 50 → 100명) 부하테스트"
    - "생성기에 MQTT 송신 추가, 환자별 토픽으로 TCP와 비교 준비"
    - "공개 데이터(PTB-XL)로 기준 CNN 학습, 모델 6종 × 시드 3번으로 정확도와 판정 속도 비교"
  verified:
    - "6·20·50명에서 유실 0, 워커 처리 지연 p95 약 13ms · 27ms · 54ms"
    - "100명에서 유실 0이지만 워커 하나(w0)의 p95가 120ms → 1,010ms로 계속 증가"
    - "원인: 분석을 메시지마다 3ms로 가정해서 34명을 맡은 w0가 1초에 1.02초 분량 일을 해야 했음"
    - "후속 확인: 실제 판정은 5초 구간마다 1번이라 가정보다 약 12배 가벼움. 실제 모델을 붙여 다시 잰 100명 결과는 유실 0, 판정 p95 약 102ms (팀원 측정, 맥북 기준)"
    - "MQTT 송신: 10명 × 10초 유실 0, 지연 p95 1.3ms"
    - "기준 CNN 시험셋(학습에 안 쓴 환자): 민감도 0.929 · 특이도 0.883 · AUC 0.969, 5초 구간 판정 CPU 0.40ms"
    - "모델 6종 AUC 0.962~0.976으로 비슷, CPU 판정은 0.40~6.55ms로 16배 차이 → 경량 CNN 기준선, CNN+LSTM 최종 후보"
steps:
  - { name: "가상 환자 스트림 생성기", status: "완료", note: "sanhak-01-stream-generator" }
  - { name: "서버 연결 방식 설계", status: "완료", note: "sanhak-02-protocol-design" }
  - { name: "TCP 전송과 3리드 데이터", status: "완료", note: "sanhak-03-tcp-3lead" }
  - { name: "수신부 연결과 전체 시연", status: "완료", note: "sanhak-04-receiver-demo" }
  - { name: "환자 수별 부하테스트와 모니터링", status: "완료", note: "sanhak-05-loadtest" }
  - { name: "MQTT 송신 추가", status: "완료" }
  - { name: "기준 AI 모델 학습과 모델 비교", status: "완료" }
  - { name: "실제 기기 조건(1리드)으로 재학습과 외부 평가", status: "진행 중" }
  - { name: "AI 모델을 넣은 100명 부하테스트와 병목 개선", status: "예정" }
  - { name: "산학 논문 작성", status: "예정", note: "/projects/sanhak-paper" }
next: "실제 기기와 같은 1리드로 모델을 다시 학습하고 외부 데이터로 평가한 뒤, 모델을 넣은 상태로 100명 부하테스트를 다시 재고 결과를 논문으로 정리할 계획입니다."
draft: false
---

## 개요

팀 5명(서버 2, AI 3) 중 팀장이자 서버 담당입니다. 공개 데이터셋(PhysioNet)만 사용했고, 기업 데이터와 기업 정보는 이 페이지에 쓰지 않습니다.

```plain text
생성기(나) → TCP·MQTT → 수신부 → Redis Streams → 워커 → R파 검출 → AI 판정 → 화면
```

관련 논문: [산학 실시간 심전도 서버 논문](/projects/sanhak-paper/)

<!-- 작성 틀: 선택한 이유 / 배운 점 은 직접 작성 -->
