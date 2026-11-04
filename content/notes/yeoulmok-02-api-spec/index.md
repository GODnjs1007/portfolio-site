---
title: "여울목 2단계 · 기능 정의와 API 명세"
date: 2026-10-31
projects: ["yeoulmok"]
step: 2
summary: "10/29 회의에서 정한 기능을 화면으로 옮기고, 서버와 앱·웹이 주고받을 API 명세를 정한다."
tags: ["API 명세", "Figma", "와이어프레임", "FastAPI", "Cloudflare"]
troubleshooting:
  - "Figma가 무료 플랜으로 연결됨"
  - "교육 플랜인데 좌석이 View로 나옴"
draft: false
---

## 목표

10/29 회의에서 정한 기능을 화면으로 옮기고, 서버와 앱·웹이 주고받을 API 명세를 정한다.

## A. 기능 정의 (10/29 회의)

- 주기능: 계곡에 있을 때 실시간 위험 탐지
- 앱 (로그인 없음)
  1. 계곡 구독(위치 설정). 검색은 이름 있는 큰 계곡만
  2. GPS로 근처 계곡 보기
  3. API로 홍수 기준 정하기 (해원)
  4. 알림: 보내는 시점 3단계
  5. AI API: 발령 근거 설명 / 시즌 보고서 초안 / 계곡 현재 상태 문구
- 웹 (로그인)
  - 관할 상태 점검
  - 공무원이 계곡 실시간 사용자 수 모니터링
  - 공무원이 앱 사용자에게 직접 경고 알림
- 팀 작업 순서: 기능 정의 → 피그마 화면 → 서버·화면 API 연결 → API 명세서
  - 내 제안: API 명세를 화면·서버 작업 전에 먼저. 화면과 서버가 같은 약속을 보고 동시에 만들 수 있어서
  - API 명세: 서버와 앱·웹이 어떤 주소로 어떤 값을 주고받을지 정한 약속
- 이슈·PR 규칙: 저장소가 달라서 각자 정함. 서버 저장소 규칙은 내가 공부해서 정할 예정
- 미정
  - 알림 3단계가 무엇인지. 원래 설계는 2단계 (상류 1시간 강수 → 사전 경보 / 하류 30분 수위 상승폭 → 즉시 경보)
  - 웹의 실시간 사용자 수·공무원 직접 알림은 사용자 위치를 서버로 받아야 해서 위치정보 법적 절차 필요 → 웹은 읽기 전용 관할 상태부터 (3단계 D 참고)
  - 판정 기준값 X(상류 1시간 강수)·Y(하류 30분 상승폭): 사고일 과거 데이터로 1차, 컨설팅 1회차에서 검토. 기준값은 코드가 아니라 DB에 관측소별로 저장
- 이후 정리된 것 (10/31)
  - 대상 계곡: 금대리, 서곡리 (3단계 C 참고)
  - 서곡리는 쓸 만한 하류 수위 관측소가 없어서 강수 사전 경보만 제안
  - 보드 카드 '홍수 판별 방법 및 관련 기준 조사'(팀원)와 기준값 작업이 겹침 → 판별 방법 조사 = 팀원, 데이터로 계산 = 해원으로 나누자고 11/1 회의에서 제안

## B. Figma 학생 계정과 팀 파일

- Figma 화면을 Claude가 읽고 코드로 옮기려면(디자인→코드) Figma 유료 기능이 필요함 → 학생 계정의 Education 플랜으로 해결
  - Education 플랜: 학생 인증을 받으면 Professional급 기능을 무료로 쓰는 요금제
- 처음 연결된 계정 확인 (Claude에서 Figma `whoami`)

| 항목 | 처음 | 바꾼 뒤 |
| --- | --- | --- |
| 계정 | 개인 계정 | 학교 계정 |
| 플랜 | starter (무료) | student (교육) |
| 좌석 | View | View (교육 플랜은 좌석 구분이 없어서 표시만 이렇게 나옴) |

- 좌석(seat): 팀 안에서 그 사람이 쓸 수 있는 권한 등급. View는 보기 전용
- 바꾼 순서 (트러블슈팅 1번 참고)
  1. claude.ai 설정 → 커넥터 → Figma 연결 해제 → 학교 계정으로 다시 연결
  2. `figma.com/education`에서 학생 인증 신청: 학생 / 고등 교육 / 학교 이메일 있음 / 학교 이메일로 로그인됨 / 컴퓨터 과학 / 졸업 예정 2027년 2월
  3. 요금제 선택에서 '교육' 선택 (팀원 초대, 작업 선택 화면은 건너뜀)
  4. 관리자 콘솔 → 멤버에서 교육 상태 '인증됨' 확인
- 졸업 후: Education이 끝나면 Starter로 내려가고 파일은 삭제되지 않음. 편집 가능한 파일이 3개로 줄어서 넘는 파일은 보기 전용이 됨. 학교 메일은 졸업 후에도 유지된다고 확인
- Figma의 GitHub 연결은 안 함. 디자인은 Figma 커넥터로 읽고, 코드는 조직에 설치된 Claude GitHub 앱으로 올리면 충분
- 팀 파일 생성: Claude가 내 학생 팀에 `여울목 화면설계` 파일을 만듦
  - 파일을 내 팀에 둔 이유: 학생 팀이라 파일 개수 제한이 없고, 연결된 계정이라 Claude가 바로 읽고 쓸 수 있음
- 팀원 초대: 공유하기 → 팀원 메일 → 편집 가능
  - 교육 플랜은 '인증받은 교육 사용자와의 협업'으로 제한돼서, 졸업생인 팀원이 편집 가능한지는 직접 확인 필요. 안 되면 파일을 팀원 계정 쪽으로 옮김
  - 공유 설정이 '누구나 볼 수 있음'으로 돼 있음 → 링크를 아는 사람은 볼 수 있음. 필요하면 나중에 제한
- 깡통 화면 5장 (C 참고)

## C. 깡통 화면 5장

- 10/29 회의 기능 정의를 기준으로 와이어프레임 5장을 그림 (Claude가 Figma에 직접 생성)
  - 와이어프레임: 색·디자인 없이 배치와 들어갈 정보만 잡은 회색 화면
  - 앱은 아이폰 크기(393×852), 웹은 1440×900. 글꼴은 Noto Sans KR
  - 계곡 이름·수치는 가짜 값(○○, 14:05 등)

| 화면 | 들어간 것 |
| --- | --- |
| 앱 01 홈(구독 계곡) | 구독한 계곡 카드(이름, 지역, 상태 배지, 상류 1시간 강수, 하류 수위 30분 변화, 관측 시각), 계곡 추가 버튼, 하단 탭(홈·근처·검색) |
| 앱 02 계곡 검색·구독 | 검색창, '이름 있는 큰 계곡만 검색' 안내, 계곡 목록과 구독/구독중 버튼 |
| 앱 03 근처 계곡(GPS) | 지도 자리, 내 위치 기준 거리순 계곡 목록과 상태 배지 |
| 앱 04 경보 상세 | 경보 배지, 한 줄 요약, AI 근거 설명, 관측소·관측 시각·실측값·기준값 표, 행동 요령, 면책 문구 |
| 웹 01 관할 계곡 상태 | 왼쪽 메뉴, 요약 숫자(전체 계곡·사전 경보·즉시 경보·판정 불가), 계곡 표, 지도 자리, '읽기 전용' 표시 |

- 모든 화면에 출처 "자료: 한강홍수통제소, 기상청" (두 기관 이용약관 조건)
- 경보 상세에 "판단 보조 정보이며 공식 재난경보를 대체하지 않습니다" (신청서 내용과 맞춤)
- 경보 배지는 "안전 / 사전 경보"만. 알림 3단계가 아직 미정
- 웹은 읽기 전용 관할 상태만. 실시간 사용자 수·공무원 직접 알림은 위치정보 법적 절차 때문에 후순위 (3단계 D 참고)
- 팀원이 이 위에 다듬는 방식으로 진행

## D. 헬스체크 API와 도메인 연결

- 구조 : 폰·브라우저 → `https://yeoulmok.ihaewon.com` → Cloudflare(HTTPS·DNS) ⇄ 터널 ⇄ cloudflared(yeoulmok VM) → `localhost:8000` → FastAPI 컨테이너 `api`
- 앱도 바깥 인터넷에서 서버를 불러야 해서 공개 주소가 필요함. 아이폰 앱은 https만 허용 → Cloudflare가 인증서 처리
  - 서브도메인: 이미 가진 `ihaewon.com` 앞에 이름을 붙인 주소. DNS 레코드만 추가하면 돼서 추가 비용 없음
- 서버 코드는 서버가 살아 있는지만 알려주는 `/api/health` 하나로 시작 (FastAPI)
  - 헬스체크: 서버가 정상인지 확인하려고 만드는 가장 단순한 API
- 처음엔 VM에서 가상환경(.venv)으로 직접 실행해서 Tailscale 주소로 확인 → 터미널을 끄면 서버도 꺼져서 커리어 내비와 같은 방식으로 Docker 컨테이너로 바꿈
- 컨테이너에 API 키 파일을 `--env-file`로 넣어둠 → 나중에 수집 코드가 키를 환경변수로 꺼내 씀. 키는 여전히 저장소 밖
- 터널은 커리어 내비·포트폴리오와 따로 `yeoulmok` 터널을 새로 만듦 → VM 하나가 죽어도 다른 서비스 영향 없음
- VM에 git 사용자 이름이 없어서 커밋 전에 설정
- 결과 : 폰 5G(와이파이 끔)로 `https://yeoulmok.ihaewon.com/api/health` 접속 → `{"status":"ok","service":"yeoulmok"}`

### 명령어·설정

#### 1. 서버 코드 (VM `~/yeoulmok`)

```py
from fastapi import FastAPI

app = FastAPI(title="여울목 API")

@app.get("/api/health")          # 이 주소로 GET 요청이 오면
def health():
    return {"status": "ok", "service": "yeoulmok"}   # 이 JSON을 돌려줌
```

```bash
mkdir -p app && cat > app/main.py   # 위 코드를 app/main.py로 저장
printf "fastapi\nuvicorn\n" > requirements.txt
git config user.name "<GitHub 아이디>" && git config user.email "<메일>"
git add app requirements.txt && git commit -m "헬스체크 API 추가" && git push
```

- requirements.txt: 이 코드에 필요한 파이썬 패키지 목록. 컨테이너가 이걸 보고 설치함
- `.venv`는 `.gitignore`에 막혀서 저장소에 안 올라감 (`git status`로 확인)

#### 2. 직접 실행으로 먼저 확인

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- 브라우저 `http://yeoulmok:8000/api/health` → ok. 로그의 `favicon.ico 404`는 브라우저가 탭 아이콘을 찾는 요청이라 무시
  - 가상환경(venv): 프로젝트마다 파이썬 패키지를 따로 담는 공간
  - uvicorn: FastAPI 코드를 실제로 요청 받는 서버로 띄워주는 프로그램

#### 3. FastAPI 컨테이너 (api)

```bash
docker run -d --name api --restart unless-stopped \
  -p 8000:8000 \
  -v ~/yeoulmok:/app -w /app \
  --env-file ~/secrets/yeoulmok.env \
  python:3.12-slim \
  sh -c "pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000"

docker logs -f api      # Uvicorn running 뜰 때까지 확인
```

- --env-file: 파일 안의 `KEY=값`을 컨테이너 환경변수로 넣음
- --restart unless-stopped: VM이 재부팅돼도 컨테이너 자동 재시작

#### 4. Cloudflare Tunnel

```bash
cloudflared tunnel login
cloudflared tunnel create yeoulmok
cloudflared tunnel route dns yeoulmok yeoulmok.ihaewon.com
sudo mkdir -p /etc/cloudflared && sudo cp ~/.cloudflared/<터널 ID>.json /etc/cloudflared/
```

`/etc/cloudflared/config.yml`

```yaml
tunnel: <터널 ID>
credentials-file: /etc/cloudflared/<터널 ID>.json

ingress:
  - hostname: yeoulmok.ihaewon.com
    service: http://localhost:8000
  - service: http_status:404
```

```bash
sudo cloudflared service install
sudo systemctl status cloudflared     # active (running)
```

- 인증 파일(.json)은 VM에만 두고 Git에 안 올림
- `route dns`가 Cloudflare에 CNAME을 자동으로 만들어줌

#### 5. 코드 반영 방법

```bash
cd ~/yeoulmok && git pull
docker restart api
```

## E. API 명세서 초안

- 화면 5장 기준으로 초안 작성 → 팀 노션에 올리고 팀원이 보면서 추가·삭제
  - API 명세서: 앱·웹과 서버가 어떤 주소로 뭘 보내고 뭘 받을지 정한 약속. 이게 있으면 둘이 동시에 만들 수 있음
- 바꿀 땐 둘 다 바꿔도 되지만 바꿨으면 서로 알리기
- 주소 `https://yeoulmok.ihaewon.com/api/...`, JSON, 시각은 한국시간
- 경보 단계 `level`: `safe` / `pre_alert` / `immediate` / `unknown`(판정 불가) → 알림 3단계 정해지면 수정

| # | 화면 | 메서드 | 주소 | 하는 일 |
| --- | --- | --- | --- | --- |
| 0 | 공통 | GET | `/api/health` | 서버 확인 (완료) |
| 1 | 검색·근처 | GET | `/api/valleys` | 계곡 전체 목록 (이름, 지역, 위경도) |
| 2 | 검색 | GET | `/api/valleys?q=` | 이름 검색 (큰 계곡만) |
| 3 | 홈 | GET | `/api/status?ids=1,2` | 구독 계곡 현재 상태 |
| 4 | 경보 상세 | GET | `/api/valleys/{id}/alert` | 경보 근거, AI 설명, 행동 요령 |
| 5 | 알림 | POST | `/api/devices` | 푸시 토큰 + 구독 계곡 등록 |
| 6 | 알림 | PUT | `/api/devices/{token}` | 구독 계곡 변경 |
| 7 | 웹 | POST | `/api/admin/login` | 관리자 로그인 |
| 8 | 웹 | GET | `/api/admin/overview` | 요약 숫자 + 관할 계곡 표 |

- 근처 계곡은 API가 없음 → 1번으로 위치를 받아 폰에서 거리 계산. 사용자 위치가 서버로 안 가서 위치정보 신고 대상 아님 (3단계 D 참고)
- 관측값이 없으면 `null`, `level`은 `unknown`. 0으로 보내지 않음
- 서곡리는 수위 관측소가 없어서 수위 값이 항상 `null`
- 3번 응답 예시

```json
{
  "updated_at": "2026-11-01T09:00",
  "source": "자료: 한강홍수통제소, 기상청",
  "valleys": [
    {
      "id": 1,
      "name": "금대리 계곡",
      "region": "원주시 판부면",
      "level": "pre_alert",
      "rain_1h_mm": 18.0,
      "water_rise_30m_m": 0.06,
      "observed_at": "2026-11-01T08:50"
    }
  ]
}
```

- 회의에서 정할 것: 알림 3단계(level 값), 푸시 방식(iOS APNs), 웹 관리자 계정 발급

## 트러블슈팅

### 1. Figma가 무료 플랜으로 연결됨

- 증상 : Claude에 연결된 Figma 계정의 플랜이 Starter(무료), 좌석 View로 나옴. 이대로면 디자인→코드 호출이 거의 막힘
- 확인한 것 : 연결된 계정이 개인 gmail. 학교 계정으로 다시 연결해도 플랜이 Starter → 학교 메일로 가입만 돼 있고 학생 인증은 안 된 상태
- 원인 : 학생 인증을 받지 않은 계정으로 연결함
- 해결 : 커넥터를 학교 계정으로 다시 연결 → `figma.com/education`에서 학생 인증 → 요금제 '교육' 선택 → whoami에서 student 확인
- 재발 방지 : 커넥터를 연결하면 whoami로 계정·플랜부터 확인하고 작업 시작

### 2. 교육 플랜인데 좌석이 View로 나옴

- 증상 : 인증 후에도 whoami 좌석이 View. 관리자 콘솔 멤버 화면에 좌석 바꾸는 칸이 없음
- 확인한 것 : 멤버 화면에 '교육 상태: 인증됨'만 있고 좌석 열이 없음
- 원인 : 교육 플랜은 좌석 구분이 없어서 표시만 View로 나옴
- 해결 : 좌석 변경 없이 진행. Claude가 파일 생성·화면 그리기까지 정상으로 됨
- 재발 방지 : 플랜(tier)이 student면 좌석 표시는 무시해도 됨

## 남은 작업

- [x] Figma 화면설계 파일 세팅과 깡통 화면
- [ ] 팀원 편집 권한 확인
- [x] 헬스체크 API, 컨테이너, 도메인 연결 (`yeoulmok.ihaewon.com`)
- [x] API 명세서 초안
- [ ] API 명세서 팀원 검토
- [ ] 알림 3단계 정의 (팀원과 회의)
- [ ] 역할 나누기: 홍수 판별 방법 조사 = 팀원, 데이터로 기준값 계산 = 해원 (회의에서 제안)
