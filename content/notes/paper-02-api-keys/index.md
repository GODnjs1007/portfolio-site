---
title: "논문 실측 2단계 · API 키 준비와 보관"
date: 2026-10-12
projects: ["llm-api-policy"]
step: 2
summary: "측정에 쓸 Gemini·OpenAI API 키를 비용 사고 없이 준비하고, 코드와 분리해 VM에 안전하게 보관한다."
tags: ["보안", "비용", "리눅스", "트러블슈팅"]
troubleshooting:
  - "OpenAI API 401 invalid_api_key"
draft: false
---

## 목표

측정에 쓸 Gemini·OpenAI API 키를 비용 사고 없이 준비하고, 코드와 분리해 VM에 안전하게 보관한다.

## A. OpenAI 결제와 키 발급

1. OpenAI 플랫폼에서 API 크레딧 $5 선불 충전 (ChatGPT 구독과 API 결제는 별개)
   - 자동 충전(auto-reload)은 끔 — 켜두면 잔액이 떨어질 때마다 자동 결제됨
2. API 키 발급: 이름 `paper`, 만료 30일 (측정이 끝나면 키가 알아서 무효화되도록)

## B. VM에 키 보관

```bash
mkdir -p ~/probe/logs && cd ~/probe
nano ~/probe/.env
chmod 600 ~/probe/.env
```

```bash
export GEMINI_API_KEY=...
export OPENAI_API_KEY=...
export GEMINI_MODEL=gemini-3.5-flash
export OPENAI_MODEL=gpt-6-luna
```

- 왜 `.env`로 분리하나: 키를 코드에 직접 쓰면 코드를 GitHub 등에 올릴 때 키도 같이 새어 나감. 코드와 비밀값을 분리하는 것이 기본
- `chmod 600`: 파일 주인만 읽고 쓸 수 있게 권한 제한

## C. 모델 이름 확인

쓸 수 있는 모델 이름 확인 (키가 맞는지도 같이 확인됨)

```bash
source ~/probe/.env
curl -s https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY" \
  | grep -o '"id": "[^"]*"' | grep -iE "luna|mini|nano" | sort
```

## 트러블슈팅

### 1. OpenAI API 401 invalid_api_key

- 증상: 모델 목록 조회 시 `Incorrect API key provided: AQ.…`
- 확인한 것: 에러에 찍힌 키 앞부분이 `AQ.` → OpenAI 키(`sk-`)가 아니라 Gemini 키 형식
- 원인: `.env`에서 두 키의 자리를 반대로 넣음
- 해결: `.env` 삭제 후 다시 작성
- 재발 방지: 키 앞부분으로 출처 구분 (OpenAI `sk-`, Gemini `AQ.`/`AIza`)
