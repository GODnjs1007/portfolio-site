---
title: "캡스톤 3단계 · 플레이 기록 서버 개선 1차"
date: 2026-11-07
projects: ["capstone-game"]
step: 3
summary: "기획자 요청대로 테스터들이 집에서 보낸 기록을 브라우저 주소창만으로 내려받고 요약해볼 수 있게 서버를 고치고, 홈랩 VM에 올려 외부에서 접속되게 한다."
tags: ["구축", "보안", "트러블슈팅"]
troubleshooting:
  - "토큰 자리에 예시 글자가 그대로 들어감"
  - "터널 커넥터가 두 개 뜸"
draft: false
---

## 목표

기획자 요청(개선 1차, 납기 11/10)대로 테스터들이 집에서 보낸 기록을 브라우저 주소창만으로 내려받고 요약해볼 수 있게 서버를 고치고, 홈랩 VM에 올려 외부에서 접속되게 한다.

## 진행 과정

### A. 주소창 내보내기

- 기획자가 요청한 내보내기를 브라우저 주소창만으로 열 수 있게 만듦
- 토큰을 헤더 `X-Token` 말고 주소 뒤 `?token=`으로도 받음. 주소창은 헤더를 못 넣어서 이전엔 401이 났음
  - 쿼리 문자열: 주소 뒤 `?` 다음에 붙는 `이름=값` 정보
- 접속 로그에는 토큰이 `token=***`로 가려져 찍히게 함
- 추가한 주소 (모두 뒤에 `?token=토큰`)
  - `/`: 목록 페이지. 런마다 요약·CSV·JSON Lines·산점도 링크, 전체 zip 링크
  - `/runs/<run_id>/csv`: 한 줄 = 사건. pos는 `pos_x·pos_y·pos_z` 세 열, data는 키마다 `data.<키>` 열
  - `/runs/<run_id>/summary`: 사건 종류별 수, 런 길이, 피어 수, 얼음·기절·구출 수, run_end 표, 피어별 부하 표
  - `/runs/<run_id>/shelters.svg`: shelter_place의 x·z 좌표 산점도
  - `/export.zip`: 전체 런의 JSON Lines + CSV
- CSV는 맨 앞에 BOM을 붙여서 엑셀로 열어도 한글이 안 깨짐
  - BOM: 파일 맨 앞에 붙는 표시. 엑셀이 UTF-8로 읽게 해줌
- 산점도는 그림 라이브러리 대신 SVG를 직접 만듦. 패키지가 안 늘어서 윈도우 설치가 간단함
  - SVG: 점·선을 좌표로 적는 그림 형식. 브라우저가 바로 그려줌
- 기획자가 준 실제 샘플 2개로 확인하고 세 군데 고침
  - 2인 판인데 피어가 3으로 잡힘 → peer 0은 게임(호스트)이 보낸 사건으로 보고 피어 수에서 뺌 (기획자 확인 대기)
  - 표의 참/거짓을 CSV처럼 `true/false`로 맞춤
  - 쉘터가 1개뿐이면 산점도가 너무 확대돼서 최소 10m 범위를 보여주게 함

### B. 안전 (토큰 필수, run_id 제한)

- `PLAYLOG_TOKEN`이 없으면 서버가 시작하지 않고 종료함. 이전엔 기본값 `change-me-token`으로 그냥 떴음
- run_id 허용 문자를 영문·숫자·`-`·`_`, 1~128자로 제한. 아니면 400
  - 정규식: 글자 패턴 규칙. 여기서는 `^[A-Za-z0-9_-]{1,128}$`
  - 이전엔 `/`와 `..`만 막아서, 윈도우에서 `C:\...`나 콜론이 든 값이 data/ 밖에 쓰거나 500을 낼 수 있었음
- 배열 안에 틀린 run_id가 하나라도 있으면 아무것도 저장하지 않음 (반만 저장되는 걸 막음)
- 토큰 비교는 `hmac.compare_digest`로 바꿈
  - compare_digest: 두 값을 항상 같은 시간에 비교하는 함수. 응답 시간 차이로 토큰을 추측하지 못하게 함
- 확인 결과
  - 토큰 없이 실행 → 서버가 안 뜨고 exit 1
  - run_id `a:b`, `C:\evil` → 400
  - 토큰 없이 요청 → 401, 헤더나 `?token=`이 맞으면 200

### C. README 윈도우 기준 정리

- 12월 이후 기획자 윈도우 PC에서 README만 보고 돌릴 수 있게 순서를 다시 짬
  - 설치(Python, clone, venv, pip) → 실행(PowerShell) → 주소·토큰 → 받기 형식 → 내보내기 주소표 → CSV 열·요약 계산 방법 → 확인 → 인수인계
  - venv: 프로젝트 전용 파이썬 패키지 공간
- 요약 항목마다 어떻게 세는지 적어둠 (구출 = player_state가 downed→normal, 피어 수는 peer 0 제외 등)
- 테스트 도구 추가: 샘플 파일을 서버로 보내는 `tests/send_samples.py`, 형식대로 가짜 샘플을 만드는 `tests/make_samples.py`
- 인수인계: data/는 git에 안 올라가서 회차마다 폴더째 전달, 서버 주소가 바뀌면 게임 쪽 주소만 변경

### D. 홈랩 VM 배포

- 서비스마다 VM 하나 원칙대로 VM 106 `playlog`를 새로 만듦 (1코어 / 2GB / 20GB, Ubuntu Server)
  - 설치 화면에서 `/`가 10GB만 잡혀 있어서 ubuntu-lv를 18.2GB로 늘림
- Tailscale 연결, 기초 세팅, Proxmox 스냅샷 `base-setup`
- GitHub Deploy key(읽기 전용)로 Private 저장소를 clone
  - Deploy key: 저장소 하나에만 쓰는 SSH 키. 이 VM이 다른 저장소에는 접근 못 함
- 토큰은 `/etc/playlog.env`에 두고 권한 600, systemd 서비스 `playlog`로 상시 실행
  - systemd: 리눅스에서 프로그램을 서비스로 등록해 부팅 때 켜고, 죽으면 다시 켜는 관리자
  - 서버는 `127.0.0.1:8000`에만 열어서 VM 밖에서 직접 못 들어오고 터널로만 들어옴
- 토큰 자리에 예시 글자가 들어가서 다시 넣음 (트러블슈팅 1번)
- Cloudflare 터널 `playlog` → `playlog.ihaewon.com` → `http://localhost:8000` (공유기 포트 개방 없음)
  - 커넥터가 두 개 떠서 하나를 끔 (트러블슈팅 2번)
- 확인 결과
  - `systemctl status playlog` → `active (running)`
  - 브라우저로 `https://playlog.ihaewon.com/?token=…` → 목록 페이지 열림
  - 데스크톱 PowerShell에서 https로 POST → `saved 1` (테스트 파일은 지움)

## 트러블슈팅

### 1. 토큰 자리에 예시 글자가 그대로 들어감

- 증상 : `curl "http://127.0.0.1:8000/runs?token=..."` → `Invalid HTTP request received.`
- 확인한 것 : `/etc/playlog.env`에 실제 토큰 대신 예시 문구(한글)가 저장돼 있었음
- 원인 : 명령 예시의 자리표시를 실제 토큰으로 안 바꾸고 붙여넣음. 주소에도 한글이 그대로 들어가서 서버가 요청 자체를 못 읽음
- 해결 : 실제 토큰으로 다시 저장 → `sudo systemctl restart playlog` → `{"runs":[]}` 확인
- 재발 방지 : 붙여넣기 전에 자리표시(한글 설명, `<…>`)를 바꿨는지 확인. 홈랩 7단계 Grafana 비번 때와 같은 실수

### 2. 터널 커넥터가 두 개 뜸

- 증상 : Cloudflare 터널 화면에 Active replicas 2
- 확인한 것 : VM 터미널 하나에서 cloudflared 로그가 계속 찍히고 있었고, `systemctl status cloudflared`도 running
- 원인 : 설치 화면의 "Install as service"와 "run tunnel (manual)" 명령을 둘 다 실행함
- 해결 : manual로 띄운 쪽을 Ctrl+C로 종료. 서비스로 등록된 커넥터만 남김
- 재발 방지 : 상시 실행할 때는 "Install as service"만 실행. manual은 창을 닫으면 꺼지는 임시 실행

## 남은 작업

- 기획자 확인 답변 받기 (peer 0 제외, build "dev", 구출 기준)
- 플레이테스트 회차마다 data/ 폴더 전달
- 12월 인수: 기획자 윈도우 PC로 이전
