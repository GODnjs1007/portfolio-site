---
title: "논문 실측 3단계 · 측정 스크립트 작성"
date: 2026-10-08
projects: ["llm-api-policy"]
step: 3
summary: "한 번 실행하면 세 정책(기다리기·재시도·전환) 비교에 필요한 응답 기록을 한 줄로 남기는 스크립트를 만든다."
tags: ["구축"]
troubleshooting: []
draft: false
---

## 목표

한 번 실행하면 세 정책(기다리기·재시도·전환) 비교에 필요한 응답 기록을 한 줄로 남기는 스크립트를 만든다.

## A. 무엇을 기록하나

한 번 실행하면 아래 3번의 호출을 하고 결과를 한 줄(JSON)로 저장한다.

| 기록 | 호출 | 논문에서의 의미 |
| --- | --- | --- |
| gemini_1 | Gemini 1차 호출 | 그냥 기다렸을 때 |
| gemini_2 | 1차 직후 Gemini 재호출 | 같은 API로 재시도했을 때 |
| openai | 1차와 동시에 OpenAI 호출 | 다른 AI로 전환했을 때 |

- 각 호출마다 시작 시각, 걸린 시간(초), HTTP 코드, 성공 여부, 토큰 수, 오류 메시지를 남김
- 타임아웃은 60초로 넉넉히 두고, 정책별 타임아웃은 나중에 기록을 보고 적용함 → 정책마다 따로 호출할 필요가 없어 비용이 줄어듦
- Gemini와 OpenAI는 스레드 2개로 **동시에** 호출 → 같은 시점의 네트워크 상태에서 비교

## B. 코드 `probe.py`

```python
# probe.py — LLM API 지연·장애 실측 수집기 (cron으로 10분마다 실행)
import json, os, time, uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import requests

KST = timezone(timedelta(hours=9))
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "")
HARD_TIMEOUT = 60
PROMPT = ("다음 문장을 20자 이내로 요약하라: "
          "보호자는 내일 저녁 7시에 고양이에게 사료 40g을 주고 물을 갈아 달라고 요청했다.")
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

def call_gemini():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {"contents": [{"parts": [{"text": PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 256, "thinkingConfig": {"thinkingLevel": "low"}}}
    headers = {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"}
    return timed_post(url, body, headers, ("usageMetadata", "promptTokenCount", "candidatesTokenCount"))

def call_openai():
    url = "https://api.openai.com/v1/chat/completions"
    body = {"model": OPENAI_MODEL, "messages": [{"role": "user", "content": PROMPT}],
            "max_completion_tokens": 256}
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"}
    return timed_post(url, body, headers, ("usage", "prompt_tokens", "completion_tokens"))

def timed_post(url, body, headers, usage_path):
    t0 = time.perf_counter()
    rec = {"start": datetime.now(KST).isoformat(timespec="milliseconds")}
    try:
        r = requests.post(url, json=body, headers=headers, timeout=HARD_TIMEOUT)
        rec["sec"] = round(time.perf_counter() - t0, 3)
        rec["http"] = r.status_code
        rec["ok"] = r.status_code == 200
        if r.ok:
            u = r.json().get(usage_path[0], {}) or {}
            rec["in_tok"], rec["out_tok"] = u.get(usage_path[1]), u.get(usage_path[2])
        else:
            rec["error"] = r.text[:300]
    except requests.Timeout:
        rec.update(sec=round(time.perf_counter() - t0, 3), http=None, ok=False, error="timeout")
    except Exception as e:
        rec.update(sec=round(time.perf_counter() - t0, 3), http=None, ok=False, error=f"{type(e).__name__}: {e}"[:300])
    return rec

def gemini_twice():
    return call_gemini(), call_gemini()

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        fg = ex.submit(gemini_twice)
        fo = ex.submit(call_openai)
        g1, g2 = fg.result()
        o1 = fo.result()
    row = {"round_id": uuid.uuid4().hex[:12], "ts": datetime.now(KST).isoformat(timespec="seconds"),
           "gemini_model": GEMINI_MODEL, "openai_model": OPENAI_MODEL,
           "gemini_1": g1, "gemini_2": g2, "openai": o1}
    path = os.path.join(LOG_DIR, f"probe_{datetime.now(KST):%Y%m%d}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(row["ts"], "G1", g1.get("http"), g1.get("sec"), "| G2", g2.get("http"), g2.get("sec"),
          "| O", o1.get("http"), o1.get("sec"))
    for name, r in (("G1", g1), ("G2", g2), ("O", o1)):
        if not r.get("ok"):
            print(name, "ERROR:", r.get("error"))

if __name__ == "__main__":
    main()
```

<details><summary>코드 부분별 설명</summary>

- `timed_post`: 요청 하나를 보내고 걸린 시간을 잰다. `time.perf_counter()`는 시계 바늘이 아니라 경과 시간 측정용 타이머라 정확함
- `try / except`: 실패해도 프로그램이 죽지 않고 "실패했다"는 기록을 남기게 함. 장애를 재는 실험이라 실패 기록이 오히려 핵심 데이터
- `requests.Timeout`: 60초 안에 응답이 없으면 timeout으로 기록
- `ThreadPoolExecutor(max_workers=2)`: 일꾼 2명을 둬서 Gemini 쪽과 OpenAI 쪽을 동시에 실행
- `.jsonl`: 한 줄에 JSON 하나. 계속 줄만 추가하면 되고, 나중에 한 줄씩 읽어 분석하기 쉬움
- 파일명에 날짜를 넣어 하루에 파일 하나씩 생김

</details>

## C. 테스트 실행

```bash
cd ~/probe && source .env && python3 probe.py
# 2026-10-08T11:03:24+09:00 G1 200 2.111 | G2 200 2.047 | O 200 4.63
```

- `G1 200 2.111` = Gemini 1차 호출 성공(HTTP 200), 2.111초 걸림
