---
title: "산학 1단계 · 가상 환자 스트림 생성기"
date: 2026-10-08
projects: ["sanhak-ecg"]
step: 1
summary: "실제 환자 없이 서버를 시험하기 위해, 공개 심전도 데이터를 잘라서 가상 환자 N명이 실시간으로 보내는 것처럼 흉내 내는 생성기를 만든다."
tags: ["구축"]
troubleshooting: []
draft: false
---

## 목표

실제 환자 없이 서버를 시험하기 위해, 공개 심전도 데이터를 잘라서 가상 환자 N명이 실시간으로 보내는 것처럼 흉내 내는 생성기를 만든다.

## 기준

- 데이터: PhysioNet LTSTDB (Long-Term ST Database), 250Hz
  - PhysioNet: 의료 데이터 공개 도서관
  - LTSTDB: 그 안의 심전도 모음. 사람마다 21\~24시간짜리 기록
  - 250Hz: 1초에 250번 측정 = 4ms마다 점 하나
- 0.1초마다 25샘플씩 보냄 (250Hz × 0.1초)
  - 샘플: 측정한 점 하나(숫자 하나)
  - 0.1초 분량을 상자 하나에 담는 것. 점 하나씩 보내면 1초에 250번, 25개씩 묶으면 1초에 10번
- 환자마다 시작 위치를 다르게 해서 같은 파형이 동시에 나오지 않게 함
  - 파일 하나로 여러 명을 흉내 내니까, 다 처음부터 틀면 100명이 똑같은 박동을 보냄. 환자 0은 3초부터, 1은 17초부터처럼 섞음

## A. 데이터 읽기 — `read_sample.py`

```python
import wfdb

# LTSTDB의 s20011 기록에서 처음 2500개(10초)만 읽기
record = wfdb.rdrecord("s20011", pn_dir="ltstdb", sampto=2500)

print("샘플링 레이트:", record.fs)
print("채널 수:", record.n_sig)
print("채널 이름:", record.sig_name)
print("데이터 모양:", record.p_signal.shape)
print("처음 5개 값:")
print(record.p_signal[:5])
```

- `wfdb` : PhysioNet 파일을 읽는 파이썬 도구
- `"s20011"` : 읽을 사람(기록) 이름
- `pn_dir` : PhysioNet에서 바로 읽어옴 (파일 다운로드 불필요)
- `sampto` : 몇 번째 샘플까지 읽을지. 기록 하나가 21\~24시간이라 전부 읽으면 무거움
  - 여기선 2,500개 = 10초만 읽어서 파일 모양만 확인
  - B·C에서 실제로 재생할 때는 `sampto=FS * 60` = 15,000개 = 1분
- `record.fs` : 샘플링 레이트 (250)
- `record.n_sig`, `record.sig_name` : 리드 수와 리드 이름 (s20011은 2리드)
- `record.p_signal` : 측정값 표. 모양 (2500, 2) = 2,500줄 × 2리드
- `[:5]` : 앞 5줄만

## B. 환자 1명 — `stream_one.py`

- 0.1초마다 25샘플씩 잘라서 내보내는 구조만 확인
  - 보내는 곳 없이 화면에 찍기만 함. 0.1초 박자대로 잘 나오는지 보는 단계

```python
FS = 250               # 초당 샘플 수
CHUNK = 25             # 한 번에 보내는 개수 (0.1초 분량)
INTERVAL = CHUNK / FS  # 0.1초

# 1분 분량 읽어두고 반복 재생
record = wfdb.rdrecord("s20011", pn_dir="ltstdb", sampto=FS * 60)
signal = record.p_signal

def send(patient_id, chunk):
    pass  # 나중에 서버(큐)로 보내는 코드가 들어갈 자리

pos = 0
start = time.perf_counter()
next_tick = start

while time.perf_counter() - start < 10:
    chunk = signal[pos:pos + CHUNK]
    send(0, chunk)
    pos = (pos + CHUNK) % len(signal)

    next_tick += INTERVAL
    time.sleep(max(0, next_tick - time.perf_counter()))
```

- `CHUNK = 25` : 상자 하나에 담는 샘플 수. 250 × 0.1초
- `INTERVAL` : 25 / 250 = 0.1초. 상자 보내는 간격
- `send()` : 아직 비어 있음(`pass`). 3단계에서 TCP 전송으로 채움
- `time.perf_counter()` : 시간 재는 용도의 정밀한 시계
- `while ... < 10` : 10초 동안 반복
- `signal[pos:pos + CHUNK]` : pos번째부터 25개 잘라내기
- `% len(signal)` : 1분 끝까지 가면 0으로 돌아가 처음부터 다시 재생
- 마지막 두 줄이 next_tick 방식 (F-3)
- 실제 파일에는 1초마다 누적 개수를 화면에 찍는 줄이 더 있음 (여기선 생략)

## C. 환자 N명 — `stream_multi.py`

- 환자 수를 실행 인자로 받음
  - 실행 인자: 프로그램 이름 뒤에 붙이는 값. `python stream_multi.py 20` 이면 환자 20명
- `next_tick` 방식: 매번 0.1초씩 자는 게 아니라 다음 보낼 시각을 정해두고 그때까지만 대기 → 처리 시간만큼 늦어지는 걸 막음
  - next_tick: 다음에 보낼 시각. 메트로놈처럼 박자를 미리 정해둠 (F-3 참고)
  - sleep: 정해진 시간만큼 멈춰 기다리는 것
- 목표 개수, 실제 개수, 최대 지각을 출력해서 생성기 자체가 늦지 않은지 확인
  - 최대 지각: 정해둔 시각보다 가장 늦게 보낸 정도. 이게 커지면 생성기가 박자를 못 따라가는 것

```python
N = int(sys.argv[1]) if len(sys.argv) > 1 else 6   # 환자 수
DURATION = 10                                     # 측정 시간(초)

# 환자마다 시작 위치를 다르게
positions = [random.randrange(0, len(signal), CHUNK) for _ in range(N)]

sent = 0
max_late = 0.0
start = time.perf_counter()
next_tick = start

while time.perf_counter() - start < DURATION:
    for pid in range(N):
        p = positions[pid]
        chunk = signal[p:p + CHUNK]
        send(pid, chunk)
        sent += len(chunk)
        positions[pid] = (p + CHUNK) % len(signal)

    next_tick += INTERVAL
    wait = next_tick - time.perf_counter()
    if wait < 0:
        max_late = max(max_late, -wait)
    time.sleep(max(0, wait))

elapsed = time.perf_counter() - start
print(f"환자 {N}명 | 목표 초당 {N * FS}개 | 실제 초당 {round(sent / elapsed)}개 | 최대 지각 {max_late * 1000:.1f}ms")
```

- `sys.argv[1]` : 실행 인자. `python stream_multi.py 20`의 `20`. 안 주면 6명
- `positions` : 환자마다 시작 위치를 난수로 뽑음 (F-4). `CHUNK` 간격으로 뽑아서 상자 경계에 맞춤
- `for pid in range(N)` : 0.1초마다 환자 N명 상자를 차례로 만듦
- `sent` : 지금까지 만든 샘플 수. 마지막에 초당 개수 계산용
- `wait` : 다음 박자까지 남은 시간
- `wait < 0` : 정해둔 시각이 이미 지남 = 지각. 그중 가장 큰 값이 최대 지각
- `max(0, wait)` : 지각했으면 안 자고 바로 다음 박자로
- 마지막 줄이 D 결과 출력 (목표 / 실제 / 최대 지각)

## D. 결과

- 환자 100명 기준 초당 목표 25,000샘플 중 24,999샘플 생성
- 만드는 속도만 잔 것. 서버로 보내는 부분(`send`)은 비워둠
  - send: 서버로 보내는 함수. 3단계에서 TCP 전송으로 채움
  - 25,000 / 24,999: 환자 100명 × 점 250개 = 목표. 거의 다 만들었으니 박자를 안 놓침

## E. 코드 검토 (팀원)

- 검토 의견 8건 받음. 메시지 형식이 정해져야 고칠 수 있는 것들이 있어 일부 보류
  - 메시지 형식: 상자에 붙이는 송장 양식 (2단계에서 정함)
- 생성기를 서버와 같은 컴퓨터에서 돌리면 서버 성능이 낮게 나올 수 있다는 지적 → 개발 단계는 같이, 최종 측정만 분리하기로 함
  - 같은 컴퓨터면 생성기와 서버가 CPU를 나눠 써서 서버가 느려 보일 수 있음. 대신 시계가 같아서 지연 계산은 정확함

## F. 자세히 보기 (공부용)

### 1. 생성기가 왜 필요한가

- 서버가 환자 100명을 버티는지 재려면 환자 100명이 필요함. 진짜 환자는 없으니까 공개 심전도 파일을 재생해서 흉내 냄
- 비유: 택배 물류센터 개장 전에 가짜 상자를 쏟아봐서 막히는 곳을 찾는 것

### 2. 숫자 감 잡기

| 숫자 | 뜻 |
| --- | --- |
| 250Hz | 1초에 250번 측정 = 4ms마다 점 하나 |
| 0.1초 × 250 = 25 | 상자 하나에 리드당 숫자 25개 |
| 환자 1명 | 1초에 상자 10개, 숫자 250개 (리드당) |
| 환자 100명 | 1초에 상자 1,000개, 숫자 25,000개 (리드당) |

- 한 점씩 보내면 1초에 250번 보내야 해서 부담이 큼. 실제 장비도 묶어서 보내니까 0.1초 묶음으로 보냄

### 3. 박자 맞추기 (next_tick)

```python
next_tick = start
for _ in range(ticks):
    보내기()
    next_tick += 0.1                    # 다음에 보낼 시각을 정해두고
    time.sleep(next_tick - time.time())  # 그때까지만 기다림
```

- 나쁜 방법: 매번 `sleep(0.1)`. 보내는 데 2ms 걸리면 한 바퀴가 0.102초 → 100번 돌면 0.2초 밀림. 오차가 계속 쌓임
- 좋은 방법: “다음 시각”을 미리 정해두고 남은 시간만 기다림. 한 번 늦어도 다음에 따라잡음
- 비유: 메트로놈. 내가 늦게 쳐도 다음 박자는 제자리에 옴
- 최대 지각 = 정해둔 시각보다 가장 늦게 보낸 정도. 이게 커지면 생성기 자체가 못 따라가는 것

### 4. 환자마다 시작 위치 다르게

- 파일 하나로 여러 명을 흉내 내니까 같은 위치에서 시작하면 100명이 똑같은 파형을 보냄
- 그래서 환자마다 시작 위치를 다르게 함. 단 난수라 실행마다 달라져서 회차 비교가 어렵다는 검토 의견 있음 (고정값으로 바꿀 예정)

### 5. D 결과가 뜻하는 것

- 24,999 / 25,000 = 생성기가 박자를 놓치지 않고 만들 수 있다는 뜻
- 아직 아무 데도 안 보냈으니 “서버가 버틴다”는 뜻은 아님. 보내는 건 3단계, 받아서 처리하는 건 4단계
