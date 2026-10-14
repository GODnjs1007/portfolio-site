---
title: "돌봄 논문 3단계 · 실행과 결과 집계"
date: 2026-10-08
projects: ["pet-handover-ai"]
step: 3
summary: "Gemini API로 400회 실행해 세 방식을 비교하고, 코드 검사가 놓친 질문을 모두 잡는 대신 쓸데없는 질문이 늘어나는 것을 확인했다."
tags: ["트러블슈팅"]
troubleshooting:
  - "Gemini 무료 티어 429 한도 초과"
draft: false
---

## 목표

고정한 평가 사례로 A·B를 실행하고, C를 적용해 세 방식을 같은 기준으로 비교한다.

## A. 실행

- 모델: gemini-3.5-flash (thinking level low)
- 평가 사례 20개 × 10회 × A·B = 400회 호출, 400회 모두 응답 받음
  - 10회는 두 번에 나눠 실행: 1차 3회(120건) + 2차 7회(280건)
- C는 B 결과 200건에 규칙 검사만 적용 (호출 없음)

## B. 프롬프트 구조 — `run_ab.py`

A와 B는 **같은 공통 규칙**을 쓰고, 마지막 출력 형식만 다르다. 그래야 차이가 "양식" 때문인지 확인할 수 있다.

```plain text
프롬프트 = COMMON(공통 규칙) + A_SUFFIX 또는 B_SUFFIX(출력 형식) + 사례 메시지
```

공통 규칙 중 실험의 핵심 줄:

```plain text
- 서로 다른 보호자가 같은 동물·일시·작업에 다른 값을 제시하고 승인·수정 관계가 드러나지 않으면
  임의로 고르지 말고 확인 질문으로 남겨라. 최신 메시지라는 이유만으로 채택하지 않는다.
- 필수 정보가 빠졌으면 임의로 채우지 말고 무엇을 확인할지 써라.
```

| | A 자유 | B 양식 |
| --- | --- | --- |
| 출력 지시 | 할 일·변경·확인 질문을 포함해 자유롭게 | 아래 JSON 형식으로만 |
| API 설정 | 기본 | `response_mime_type = "application/json"` |

B가 채우는 JSON 칸 (C가 검사하는 재료):

```json
{
  "tasks": [{"animal": "", "date": "YYYY-MM-DD", "when": "", "task": "",
             "food": null, "amount": null, "place": null, "note": null, "source_ids": []}],
  "prohibitions": [{"animal": "", "period": "", "action": "", "source_ids": []}],
  "message_log": [{"id": "M1", "sender": "", "corrects": null, "summary": ""}],
  "changes": [{"what": "", "before": "", "after": "", "source_ids": []}],
  "questions": [{"question": "", "source_ids": []}]
}
```

- `message_log`의 `sender`·`corrects`가 R4의 재료, `source_ids`가 R3의 재료

## C. API 호출 — `call()`

```python
def call(prompt, json_mode):
    global USE_THINKING_LEVEL
    last_err = ""
    attempt = 0
    for attempt in range(5):
        try:
            start = time.perf_counter()
            r = client.models.generate_content(model=MODEL, contents=prompt, config=make_config(json_mode))
            sec = time.perf_counter() - start
            u = r.usage_metadata
            return {
                "ok": True, "text": r.text or "", "sec": round(sec, 2),
                "in_tok": u.prompt_token_count, "out_tok": u.candidates_token_count,
                "think_tok": u.thoughts_token_count, "total_tok": u.total_token_count,
                "error": "", "attempts": attempt + 1,
            }
        except Exception as e:
            last_err = str(e)
            low = last_err.lower()
            if USE_THINKING_LEVEL and "thinking" in low:
                USE_THINKING_LEVEL = False
                print("  ! 생각 단계 고정이 거부돼서 끄고 다시 시도")
                continue
            if "429" in last_err or "resource_exhausted" in low or "503" in last_err:
                wait = 30 * (attempt + 1)
                print(f"  ! 호출 제한/서버 바쁨 -> {wait}초 대기 후 재시도")
                time.sleep(wait)
                continue
            break
    return {"ok": False, "text": "", "sec": None, "in_tok": None, "out_tok": None,
            "think_tok": None, "total_tok": None, "error": last_err[:500], "attempts": attempt + 1}
```

- 최대 5번 시도. 429(호출 제한)·503(서버 바쁨)이면 30초, 60초, 90초… 점점 길게 기다렸다가 다시 시도
- 응답시간(`sec`)과 토큰 수를 같이 남겨서 결과 표의 시간·비용을 계산
- API 키는 코드에 없음. `genai.Client()`가 환경변수에서 읽음

## D. 반복 실행 — `run_eval.py`

```python
for rep in range(1, REPEATS + 1):
    for c in CASES:
        for method in ("A", "B"):
            prompt = COMMON + (A_SUFFIX if method == "A" else B_SUFFIX) + "\n" + case_text(c)
            res = call(prompt, json_mode=(method == "B"))
            # 결과를 jsonl(프롬프트·응답 원문 포함)과 csv(시간·토큰 요약)에 한 줄씩 저장
            time.sleep(SLEEP)
```

- 회차 → 사례 → 방식 순서로 돌려서, 같은 사례의 A와 B가 바로 붙어서 실행됨 (시간대 차이 최소화)
- 호출 사이 2초씩 쉼
- 결과 파일: `eval_results_날짜.jsonl`(원문), `eval_summary_날짜.csv`(요약) → `check_c.py`가 jsonl을 읽어 C 결과를 만듦

## E. 결과

| 지표 | A 자유 | B 양식 | C 양식+코드 |
| --- | --- | --- | --- |
| 탐지율 (n=60) | 91.7% | 95.0% | **100%** |
| 보호자 간 충돌에서 혼자 결정 (10회 중) | 5 | 1 | **0** |
| 과잉 질의율 (n=140) | 28.6% | **7.9%** | 12.1% |
| 평균 응답시간 | 2.72초 | 4.16초 | +0.02ms |
| 호출당 비용 | 약 $0.0048 | 약 $0.0095 | +$0 |

## F. 결과 읽기

- **양식만 줘도 좋아짐 (A → B)**: 탐지율이 오르고 과잉 질의가 28.6%에서 7.9%로 크게 줄어듦
  - 자유 요약은 "확인 질문" 항목을 채우려고 불필요한 질문을 만드는 경향. 양식은 칸을 먼저 채우게 해서 실제로 빈 값만 질문으로 남는 것으로 보임 (추정, 따로 검증 안 함)
- **코드를 더하면 놓친 걸 다 잡음 (B → C)**: 탐지율 100%, 혼자 결정 0회
- **대가 (B → C)**: 과잉 질의가 6건 늘어 7.9% → 12.1%
  - R1이 "작업 끝난 후" 같은 표현을 시각이 불명확하다고 봄
  - R4가 본인이 승인한 변경을 알아보지 못함
  - 둘 다 "한 번 더 물어본 것"이지 틀린 값을 확정한 건 아님 → 돌봄에서는 놓치는 것보다 덜 위험
- A는 충돌 사례에서 절반을 "시간이 바뀐 것"으로 해석해 혼자 19시로 정했고, "사료 제품명은 묻지 마라"고 했는데도 물어봄

## G. 한계

- 가상 사례 20개, 모델 1개, 10회 반복. 통계 검정 없음
- 사례·정답·규칙을 같은 과정에서 만듦. 독립 검토 없음
- 코드는 AI가 뽑은 칸만 보므로, AI가 지시를 통째로 빼먹으면 못 잡음
- 평가 사례 하나(E18)는 말투를 고치다가 음식 종류가 빠진 결함이 있었음 → 평가 후 발견, 정답은 고치지 않고 포함·제외 결과를 둘 다 제시

## 트러블슈팅

### 1. Gemini 무료 티어 429 한도 초과

- 증상: 반복 실행 중 `429` 응답으로 호출이 막힘
- 원인: 무료 티어의 호출 한도를 넘음 (사례 20개 × 10회 × 2방식)
- 해결: 선불 결제로 전환 후 다시 실행 → 400회 모두 성공
