---
title: "돌봄 논문 2단계 · 코드 규칙 검사(R0~R4) 구현"
date: 2026-10-08
projects: ["pet-handover-ai"]
step: 2
summary: "AI가 채운 JSON 칸을 if문 규칙으로 다시 검사해, AI가 놓친 질문을 AI 호출 없이 잡는다."
tags: ["구축"]
troubleshooting: []
draft: false
---

## 목표

B 방식(JSON 양식)의 결과를 파이썬 규칙으로 한 번 더 검사하는 C 방식을 만든다.

## A. 규칙을 만든 방법

- 개발용 사례 10개로 B를 돌려보고, B가 틀린 유형을 모음
- 틀린 유형마다 "JSON 어느 칸을 보면 잡을 수 있나"를 규칙으로 만듦
- 평가용 사례로는 규칙을 만들지 않음 (1단계 D)

## B. 다섯 규칙

| 규칙 | 검사 내용 | 걸리면 |
| --- | --- | --- |
| R0 형식 | JSON이 깨졌거나 필수 칸이 없음 | "자동 점검 미완료" 표시 |
| R1 필수 값 | 동물·날짜·시각이 비었거나, 급여량이 숫자가 아님 | 질의 추가 |
| R2 값 충돌 | 같은 동물·날짜·시각·작업에 값이 2개 이상 | 질의 추가 |
| R3 질의-업무 불일치 | 질문의 근거 메시지가 어떤 할 일에도 연결 안 됨 | 질의 추가 |
| R4 타인 정정 | A가 한 말을 B가 바꿨는데 A가 그 뒤로 말이 없음 | 질의 추가 |

## C. 코드 구성

| 파일 | 하는 일 |
| --- | --- |
| `run_ab.py` | 개발용 사례로 A·B를 돌려보며 프롬프트 점검 |
| `run_eval.py` | 평가용 20개 × 10회를 A·B로 실행하고 응답을 `eval_results_*.jsonl`에 저장 |
| `check_c.py` | B의 JSON 결과에 R0~R4를 적용해 C 결과를 만들고 집계 |

- C는 AI를 다시 부르지 않고 B 결과만 읽음 → 추가 비용 0, 추가 시간은 밀리초 단위
- 코드 원본: 맥 `~/pet-handoff/`

## D. 코드 `check_c.py`

```python
import json
import re
import sys
import time

REQUIRED_KEYS = ["tasks", "prohibitions", "message_log", "changes", "questions"]
FEED_WORDS = ["급여", "사료", "밥", "식사", "먹이", "간식 주"]
WHEN_ANCHORS = ["방문", "식사", "내내", "때"]
AMOUNT_RE = re.compile(r"\d|반|한|하나|두|세")
TIME_RE = re.compile(r"\d")


def is_feeding(t):
    text = f"{t.get('task') or ''} {t.get('food') or ''}"
    return any(w in text for w in FEED_WORDS)


def empty(v):
    return v is None or str(v).strip() == ""


def check(raw):
    start = time.perf_counter()
    warns = []
    try:
        d = json.loads(raw)
    except Exception:
        return [("R0", True, "JSON 해석 실패 — 자동 점검 미완료, 원문 확인 필요")], 0.0
    missing = [k for k in REQUIRED_KEYS if k not in d]
    if missing:
        warns.append(("R0", True, f"필수 키 없음 {missing} — 자동 점검 미완료"))
    tasks = d.get("tasks") or []
    questions = d.get("questions") or []
    log = d.get("message_log") or []
    for t in tasks:
        label = f"{t.get('animal')} {t.get('date')} {t.get('task')}"
        for k in ("animal", "date", "when", "task"):
            if empty(t.get(k)):
                warns.append(("R1", True, f"[{label}] {k} 없음"))
        when = str(t.get("when") or "")
        if when and not TIME_RE.search(when) and not any(a in when for a in WHEN_ANCHORS):
            warns.append(("R1", True, f"[{label}] 실행 시점이 구체적이지 않음: '{when}'"))
        if is_feeding(t):
            amt = t.get("amount")
            if empty(amt) or not AMOUNT_RE.search(str(amt)):
                warns.append(("R1", True, f"[{label}] 급여량 없음/불명확: '{amt}'"))
    groups = {}
    for t in tasks:
        key = (t.get("animal"), t.get("date"), str(t.get("when")), t.get("task"))
        groups.setdefault(key, set()).add((str(t.get("amount")), str(t.get("food"))))
    for key, vals in groups.items():
        if len(vals) > 1:
            warns.append(("R2", True, f"같은 업무에 값이 여러 개 {key}: {sorted(vals)}"))
    task_ids = set()
    for t in tasks:
        task_ids.update(t.get("source_ids") or [])
    for q in questions:
        qids = set(q.get("source_ids") or [])
        if qids and not (qids & task_ids):
            warns.append(("R3", True, f"확인 질문의 대상 업무가 할 일 목록에 없음 (근거 {sorted(qids)})"))
    order = [m.get("id") for m in log]
    sender = {m.get("id"): m.get("sender") for m in log}
    for m in log:
        tgt = m.get("corrects")
        if not tgt or tgt not in sender:
            continue
        if sender[tgt] and m.get("sender") and sender[tgt] != m.get("sender"):
            later = order[order.index(m.get("id")) + 1:] if m.get("id") in order else []
            if not any(sender.get(x) == sender[tgt] for x in later):
                warns.append(("R4", True, f"{m.get('id')}({m.get('sender')})가 {tgt}({sender[tgt]})를 정정 — 원래 발신자 승인 확인 필요"))
    for c in d.get("changes") or []:
        b, a = str(c.get("before") or ""), str(c.get("after") or "")
        if b and (b == a or "변동 없" in a):
            warns.append(("N1", False, f"값이 같은데 변경으로 기록됨: {c.get('what')}"))
    return warns, round((time.perf_counter() - start) * 1000, 3)


def main(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    out_path = "c_" + path.split("/")[-1]
    print(f"{'사례':<8}{'B질문':>6}{'C경고':>6}{'최종확인':>8}  경고 내용")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            if r["method"] != "B":
                continue
            warns, ms = check(r["output"]) if r["ok"] else ([("R0", True, "호출 실패 — 자동 점검 미완료")], 0.0)
            try:
                b_q = len(json.loads(r["output"]).get("questions") or [])
            except Exception:
                b_q = 0
            c_confirm = [w for w in warns if w[1]]
            final = b_q > 0 or len(c_confirm) > 0
            rec = {"case_id": r["case_id"], "rep": r.get("rep", 1), "b_questions": b_q,
                   "c_warnings": [{"rule": w[0], "confirm": w[1], "msg": w[2]} for w in warns],
                   "b_needs_confirm": b_q > 0, "c_needs_confirm": final, "check_ms": ms}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            tag = r["case_id"] + (f"#{r['rep']}" if "rep" in r else "")
            print(f"{tag:<8}{b_q:>6}{len(c_confirm):>6}{('예' if final else '-'):>8}  " +
                  " | ".join(f"{w[0]}:{w[2]}" for w in warns))
    print(f"\n저장: {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
```

## E. 코드 부분별 설명

| 부분 | 하는 일 | 규칙 |
| --- | --- | --- |
| `json.loads(raw)` 실패 / `missing` | JSON이 깨졌거나 5개 필수 키가 없으면 점검 미완료 | R0 |
| `for k in ("animal", "date", "when", "task")` | 할 일마다 동물·날짜·시점·작업이 비었는지 | R1 |
| `TIME_RE`, `WHEN_ANCHORS` | 시점에 숫자도 없고 "방문·식사·내내·때" 같은 기준 말도 없으면 불명확 | R1 |
| `is_feeding` + `AMOUNT_RE` | 급여 작업인데 양이 비었거나 숫자·"반" 같은 양 표현이 없으면 | R1 |
| `groups` | (동물, 날짜, 시점, 작업)이 같은 할 일을 묶고, 양·음식 값이 2개 이상이면 | R2 |
| `task_ids` vs `qids` | 질문의 근거 메시지 ID가 어떤 할 일의 근거와도 안 겹치면 | R3 |
| `corrects` + `sender` + `later` | 다른 사람이 정정했는데, 원래 발신자가 그 뒤로 말이 없으면 | R4 |
| `N1` | 바뀐 게 없는데 "변경"으로 적힌 경우. 기록만 하고 확인 요청은 안 함 (`False`) | 참고용 |

- 경고는 `(규칙, 확인 필요 여부, 메시지)` 세 칸짜리 묶음. 두 번째 칸이 `True`인 경고가 하나라도 있으면 C는 "확인 필요"로 판정
- 최종 판정 `final = B가 질문을 냈거나 C 경고가 있거나` → C는 B의 질문을 지우지 않고 **더하기만** 함. 그래서 탐지율은 B보다 낮아질 수 없고, 과잉 질의는 늘 수 있음
- `time.perf_counter()`로 검사에 걸린 시간을 밀리초로 기록 → 결과 표의 "+0.02ms"
- 실행: `python check_c.py eval_results_날짜.jsonl` → `c_eval_results_날짜.jsonl`로 저장
- R1의 시점 검사가 "작업 끝난 후"처럼 숫자도 기준 말도 없는 표현을 불명확으로 잡은 것이 과잉 질의가 늘어난 원인 중 하나 (3단계 F)

## F. 왜 코드로 검사하나

- AI는 같은 입력에도 답이 달라질 수 있음
- if문 규칙은 같은 입력이면 항상 같은 결과 → AI 뒤에 두는 안전망
- AI 판단이 틀려도 판단 재료(누가 언제 무슨 말을 했는지)가 JSON 칸에 남아 있으면 코드가 다시 볼 수 있음
  - 예: B가 충돌을 놓친 1회에도 "첫 메시지 발신자 = 보호자, 두 번째 = 공동보호자"가 칸에 남아 있어서 R4가 잡음
