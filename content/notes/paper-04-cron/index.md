---
title: "논문 실측 4단계 · cron 자동 실행과 수집 확인"
date: 2026-10-08
projects: ["llm-api-policy"]
step: 4
summary: "사람이 손대지 않아도 10분마다 측정이 돌게 하고, 기록이 빠짐없이 쌓이는지 확인한다."
tags: ["리눅스", "모니터링", "트러블슈팅"]
troubleshooting:
  - "OpenAI 400 (max_tokens)"
draft: false
---

## 목표

사람이 손대지 않아도 10분마다 측정이 돌게 하고, 기록이 빠짐없이 쌓이는지 확인한다.

## A. cron 등록

```bash
(crontab -l 2>/dev/null; echo "*/10 * * * * cd /home/<사용자>/probe && . ./.env && /usr/bin/python3 probe.py >> logs/cron.log 2>&1") | crontab -
crontab -l
```

| 부분 | 의미 |
| --- | --- |
| `*/10 * * * *` | 분·시·일·월·요일 순서. 분 자리가 `*/10` → 매 10분마다 (0, 10, 20 … 분) |
| `cd /home/<사용자>/probe` | cron은 홈 폴더 기준으로 실행되지 않을 수 있어 경로를 먼저 이동 |
| `. ./.env` | 키 파일을 읽어 환경변수로 등록. cron은 로그인 셸 설정을 안 읽어서 직접 불러와야 함 |
| `/usr/bin/python3` | cron의 PATH가 짧아서 실행 파일을 전체 경로로 지정 |
| `>> logs/cron.log 2>&1` | 화면 출력(1)과 에러 출력(2)을 모두 cron.log에 이어 붙임 → 안 돌았을 때 원인 확인용 |

## B. 동작 확인 (10.8)

```bash
tail ~/probe/logs/cron.log
# 2026-10-08T11:10:06+09:00 G1 200 1.917 | G2 200 2.0 | O 200 5.035
```

- 11:10에 사람이 실행하지 않았는데 기록이 생김 → 자동 측정 시작

## C. 수집 현황 확인 (10.12)

```bash
wc -l ~/probe/logs/probe_*.jsonl
grep -c "G1 200 .*G2 200 .*O 200" ~/probe/logs/cron.log
grep -v "G1 200 .*G2 200 .*O 200" ~/probe/logs/cron.log | grep "^2026"
```

| 날짜 | 기록 수 | 비고 |
| --- | --- | --- |
| 10.8 | 77 | 수동 테스트 1회 포함, 12:50 1회 결측 (VM 재시작) |
| 10.9 ~ 10.11 | 144 × 3 | 하루 144회 전부 기록 |
| 10.12 | 69 | 11:20까지 |

- 합계 578회 (cron 577 + 수동 1)

## 트러블슈팅

### 1. OpenAI 400 (max_tokens)

- 증상: 5회 OpenAI 호출만 `400`, `Could not finish the message because max_tokens or model output limit was reached`
- 확인한 것: `grep -c "max_tokens"` 결과 5 → 실패 5회 전부 같은 원인
- 원인: `probe.py`의 `max_completion_tokens: 256`이 OpenAI 답 길이보다 작을 때가 있음 (OpenAI 답은 약 250토큰, Gemini는 약 10토큰)
- 서비스 장애가 아니라 측정 설정 문제
