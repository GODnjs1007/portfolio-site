---
title: "커리어 내비 3단계 · 웹 서비스 MVP"
date: 2026-10-31
projects: ["career-navi"]
step: 3
summary: "(진행 중) 팀원 엔진을 서버에 연결하고, 계획서 그림 3 수준의 진단 리포트 화면(적합도·역량 카드·What-If·학기별 로드맵)을 만든다. Claude API 비용이 새지 않게 서버를 잠근다."
tags: ["FastAPI", "React", "보안", "진행 중"]
draft: false
---

## 목표

팀원 엔진을 서버에 연결하고, 계획서 그림 3 수준의 진단 리포트 화면(적합도·역량 카드·What-If·학기별 로드맵)을 만든다. Claude API 비용이 새지 않게 서버를 잠근다.

## A. 엔진 연결과 서버 잠금

- 팀원 PR #2(엔진 뼈대) 리뷰 : 코드를 받아 실행하고, 결과를 `main.py`의 `DiagnosisResult` 형식 검사에 넣어 통과 확인 → merge
  - 리뷰: 팀원 코드를 merge하기 전에 확인하는 것
- `/api/diagnose`가 가짜 54% 대신 팀원의 `diagnose()`를 호출 (`from engine import diagnose as run_engine`). 엔드포인트 함수 이름도 `diagnose`라 이름을 바꿔서 import
  - as: import할 때 이름을 바꿔 부르는 파이썬 문법
- Claude API 크레딧 보호를 위해 `/docs`, `/openapi.json` 기본 비활성. 로컬은 `.env`에 `ENABLE_DOCS=1`
- 요청 횟수 제한 : IP당 1분에 5번, 서버 전체 하루 300번 → 넘으면 429. 터널·Nginx를 거치면 서버가 보는 IP가 다 내부 주소라 Cloudflare 헤더로 방문자를 구분
  - 429: "요청이 너무 많음"을 뜻하는 HTTP 상태 코드
  - `cf-connecting-ip`: Cloudflare가 붙여주는 실제 방문자 IP 헤더
- 입력 길이 각 3000자 제한 → 토큰(비용) 상한
- 화면에 에러 메시지 표시 (429·입력 오류·연결 실패)
- 확인 : 도메인에서 43%와 역량 4개(팀원의 가짜 데이터) 표시, `/docs`는 Swagger 대신 첫 화면, 연타 시 "요청이 너무 많아요"
- 서버 `.env` 정리 : 키 뒤에 `chmod ...` 글자가 같이 저장돼 있어서 `sed`로 공백 뒤를 지움(내 파일·팀원 복사본) → `awk '{print NF}'`로 1덩어리 확인 후 `docker restart api`
- 서버는 시작할 때만 `.env`를 읽어서, 바꾸면 재시작해야 반영됨
- 엔진 실패 처리 (PR #6, 10/30) : 팀원 PR #3이 merge되면 진단마다 실제로 Claude API를 부르므로, API 오류·응답 형식 오류를 잡아 `502` + "AI 분석 중 문제가 생겼어요" 안내만 화면에 보내고 자세한 내용은 서버 로그에 남김
  - 502: 서버가 뒤쪽(여기선 Claude API)에서 제대로 된 답을 못 받았다는 HTTP 상태 코드
  - `docker logs api`: 실패 원인(Traceback)을 확인하는 명령

### Claude API 준비

- Claude Console에서 이 프로젝트 전용 워크스페이스 `career-navi` 생성 → 다른 용도와 사용량·비용이 안 섞이고, 이 워크스페이스에만 한도를 걸 수 있음
- 키 `careernavi-server` 발급 : 만료 30일 (발표까지만 쓰면 되고, 혹시 새도 기한이 지나면 자동으로 막힘)
- 워크스페이스 월 지출 한도 $30 → 한도를 넘으면 API 호출이 거부돼서 비용이 그 이상 나가지 않음
- 키는 VM `backend/.env`에만 둠. GitHub·노션·인수인계 문서에는 쓰지 않음. 팀원 작업용 복사본도 팀원 홈 폴더에 같은 권한으로
  - 워크스페이스(Console): API 키·사용량·한도를 묶어서 관리하는 단위
  - 지출 한도(spend limit): 한 달 동안 쓸 수 있는 최대 금액

```bash
cd ~/career-navi/backend
nano .env              # ANTHROPIC_API_KEY=... 한 줄 추가
chmod 600 .env         # 나만 읽고 쓰기
docker restart api     # .env는 시작할 때만 읽음
```

- 키 줄 뒤에 다른 글자가 붙어 저장된 걸 발견해서 정리함

```bash
sed -i 's/^\(ANTHROPIC_API_KEY=[^]*\) .*/\1/' .env
grep '^ANTHROPIC_API_KEY' .env | awk '{print NF}'    # 1이면 정상
```

- chmod 600: 파일 주인만 읽기·쓰기 가능. 같은 VM의 다른 계정은 못 읽음
- sed -i: 파일 내용을 바로 고침. 여기선 키 값 뒤 첫 공백부터 끝까지 지움
- awk '{print NF}': 한 줄이 공백 기준 몇 덩어리인지 출력

### pgvector DB 컨테이너 (db)

- 교내 자원(교과목·비교과·현장실습)을 의미로 검색하려고 벡터 검색이 되는 PostgreSQL을 미리 띄워둠 (데이터는 4단계에서 넣음)

```bash
docker run -d --name db --restart unless-stopped \
  -p 127.0.0.1:5432:5432 \
  -e POSTGRES_PASSWORD=<.env에 둔 값> \
  -v pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg16

docker exec -it db psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec -it db psql -U postgres -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
```

- 결과 : vector 확장 0.8.7
- 포트를 `127.0.0.1`에만 열어서 VM 안(FastAPI)에서만 접속되고 밖에서는 안 보임
- DB 비밀번호도 `.env`에만 둠
  - pgvector: PostgreSQL에 벡터(임베딩) 저장·유사도 검색 기능을 붙이는 확장
  - 임베딩: 문장을 숫자 목록으로 바꾼 것. 뜻이 비슷하면 숫자도 가까움
  - 볼륨(pgdata): 컨테이너를 지워도 DB 데이터가 남는 저장 공간
  - psql: PostgreSQL 명령줄 도구

### 코드 (backend/main.py 핵심)

#### 엔진 연결 + 실패 처리

```py
from engine import diagnose as run_engine
from engine.judge import fit_score

@app.post("/api/diagnose", response_model=DiagnosisResult)
def diagnose(req: DiagnoseRequest, request: Request):
    check_rate_limit(request)
    try:
        return run_engine(req.experience_text, req.posting_text)
    except Exception:
        log.exception("engine 실패")
        raise HTTPException(502, "AI 분석 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.")
```

- `response_model=DiagnosisResult` : 엔진이 돌려준 결과가 `docs/api.md` 형식과 다르면 FastAPI가 바로 에러를 냄 → 형식 어긋남을 화면까지 가기 전에 잡음

#### /docs 차단

```py
_docs = os.getenv("ENABLE_DOCS") == "1"
app = FastAPI(
    title="Career Navi API",
    docs_url="/docs" if _docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _docs else None,
)
```

#### 입력 길이 제한

```py
class DiagnoseRequest(BaseModel):
    experience_text: str = Field(min_length=1, max_length=3000)
    posting_text: str = Field(min_length=1, max_length=3000)
```

- 넘으면 FastAPI가 자동으로 `422` 반환
  - 422: 요청 형식은 맞지만 값이 규칙에 안 맞는다는 HTTP 상태 코드

#### 요청 횟수 제한

```py
PER_IP_LIMIT = int(os.getenv("RATE_PER_IP_PER_MIN", "5"))
DAILY_LIMIT = int(os.getenv("RATE_DAILY_TOTAL", "300"))

def _client_ip(request: Request) -> str:
    return (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )

def check_rate_limit(request: Request) -> None:
    now = time.time()
    hits = _ip_hits[_client_ip(request)]
    while hits and now - hits[0] > 60:      # 1분 지난 기록은 버림
        hits.popleft()
    if len(hits) >= PER_IP_LIMIT:
        raise HTTPException(429, "요청이 너무 많아요. 1분 뒤에 다시 시도해 주세요.")
    ...
```

- 기록은 서버 메모리에만 둠 → 서버를 재시작하면 초기화. 발표용 규모에선 DB·Redis 없이 이걸로 충분하다고 판단
- 한도는 `.env`로 바꿀 수 있게 해둠 (발표 당일 같은 와이파이로 몰리면 IP당 한도를 올릴 수 있음)
  - deque: 앞뒤로 넣고 빼기 빠른 목록. 오래된 기록을 앞에서 버림
  - x-forwarded-for: 프록시(Nginx)가 원래 요청자 IP를 적어주는 헤더

#### 확인 명령

```bash
# 입력 3001자 → 422
python3 -c "import json;print(json.dumps({'experience_text':'a'*3001,'posting_text':'b'}))" \
  | curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost/api/diagnose -H "Content-Type: application/json" -d @-

# 6번 연속 → 마지막 429
for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost/api/diagnose \
    -H "Content-Type: application/json" -d '{"experience_text":"a","posting_text":"b"}'
done
```

## B. 진단 리포트 화면

- `POST /api/whatif` 추가 : 체크한 역량을 '충족'으로 보고 점수 재계산
- 계산은 팀원 엔진의 `fit_score()`를 그대로 불러 씀 → 점수 규칙이 한 곳에만 있어서, 팀원이 규칙을 바꿔도 화면 점수가 어긋나지 않음
- LLM을 안 부르니까 `/api/whatif`엔 요청 횟수 제한 없음
- 적합도 원형 게이지 : SVG 원 두 개(회색 배경 + 파란 진행)로 그림. 체크하면 `+43`처럼 오른 만큼 표시
  - SVG: 코드로 그리는 벡터 그림 형식
- 역량 카드 : 충족 초록 / 부분충족 주황 / 미충족 빨강. 공고 문장과 내 경험 문장을 근거로 표시
  - 컴포넌트: 화면을 작은 부품(게이지, 역량 카드)으로 나눠 만드는 React 단위
- What-If : 추천 항목 체크박스 → 체크할 때마다 `/api/whatif` 호출
  - useEffect: 값이 바뀔 때마다(여기선 체크 목록) 자동으로 실행되는 코드
- 학기별 로드맵 : 체크한 항목을 `3-2 → 겨울 → 4-1 → 시기 무관` 순서로
- 로드맵 순서 버그 : 처음엔 겨울이 3-2보다 앞에 나옴 → 여름·겨울을 "체크한 항목 중 가장 이른 학년의 방학"으로 보고 정렬하도록 수정
- 확인 : 도메인에서 게이지·카드 표시, 체크하면 점수가 오르고 내려가고 로드맵이 채워짐 (팀원의 가짜 데이터 기준 43% → 데이터베이스+동계 현장실습 체크 시 86%)

### 체험 모드 /demo (PR #7, 10/30)

- 포스터 QR을 찍으면 입력 없이 바로 결과 화면이 나오게 `careernavi.ihaewon.com/demo` 추가
- 나중에 로그인을 붙여도 `/demo`는 로그인 없이 열리게 따로 뺌
- `GET /api/demo` : 고정 예시 입력(pandas 경험 + 제조 데이터 분석 공고)으로 엔진을 처음 한 번만 돌리고, 결과를 서버 메모리에 저장해서 재사용 → 몇 명이 찍어도 Claude API는 한 번만 호출
- 발표장에선 다들 같은 와이파이(같은 IP)라서 `/api/demo`엔 요청 횟수 제한을 안 걸음 (API를 안 부르니 비용 문제 없음)
- 화면 : 입력창은 읽기 전용, 진단하기 버튼 숨김, 위에 "체험 모드" 배너 + "내 경험으로 진단하기 →" 링크
- 체험 QR은 `/demo` 주소로 새로 만듦 (포스터에 사용)
  - 캐시: 한 번 계산한 결과를 저장해두고 다시 쓰는 것

```py
_demo_result: Optional[dict] = None

@app.get("/api/demo", response_model=DemoResponse)
def demo():
    global _demo_result
    if _demo_result is None:
        try:
            _demo_result = run_engine(DEMO_EXPERIENCE, DEMO_POSTING)
        except Exception:
            log.exception("demo engine 실패")
            raise HTTPException(502, "체험 데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.")
    return {"experience_text": DEMO_EXPERIENCE, "posting_text": DEMO_POSTING, "result": _demo_result}
```

```javascript
const IS_DEMO = window.location.pathname.startsWith('/demo')
```

- Nginx는 없는 경로를 `index.html`로 보내서(`try_files`) `/demo`도 같은 React 화면이 열리고, 화면이 주소를 보고 체험 모드로 바뀜

### 코드

#### What-If 점수 재계산 (backend/main.py)

```py
@app.post("/api/whatif", response_model=WhatIfResult)
def whatif(req: WhatIfRequest):
    done = set(req.done_ids)
    comps = [
        {"id": c.id, "type": c.type, "status": "충족" if c.id in done else c.status}
        for c in req.competencies
    ]
    return {"fit_score": fit_score(comps)}
```

- 점수 규칙(팀원의 judge.py) : 가중치 필수 2 · 우대 1 · 직무 1 / 상태 충족 1 · 부분충족 0.5 · 미충족·판단보류 0 → 적합도 = Σ(가중치×상태) ÷ Σ가중치 × 100

#### 적합도 게이지 (frontend/src/App.jsx)

```javascript
function Gauge({ score, base }) {
  const r = 52
  const len = 2 * Math.PI * r            // 원 둘레
  return (
    <svg viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={r} className="gauge-bg" />
      <circle cx="60" cy="60" r={r} className="gauge-fg"
        strokeDasharray={len} strokeDashoffset={len * (1 - score / 100)} />
    </svg>
  )
}
```

- 파란 원의 선을 둘레만큼 점선 하나로 만들고, 점수만큼만 보이게 나머지를 밀어냄
  - strokeDasharray: 선을 점선으로 그릴 때 한 칸 길이
  - strokeDashoffset: 점선 시작 위치를 미는 값

#### 체크 → 서버 재계산

```javascript
useEffect(() => {
  if (!result) return
  postJson('/api/whatif', { competencies: result.competencies, done_ids: doneIds })
    .then((d) => setWhatIf(d.fit_score))
}, [result, doneIds.join(',')])
```

#### 학기 정렬

```javascript
// 3-1 < 여름 < 3-2 < 겨울 < 4-1 ... (시기 무관은 맨 뒤)
function semesterKey(s, baseYear) {
  if (!s) return 999
  const m = s.match(/^(\d)-(\d)$/)
  if (m) return Number(m[1]) * 10 + Number(m[2]) * 2
  if (s.includes('여름')) return baseYear * 10 + 3
  if (s.includes('겨울')) return baseYear * 10 + 5
  return 900
}
```

- 3-2 → 34, 겨울(3학년 기준) → 35, 4-1 → 42 처럼 숫자로 바꿔 정렬
- 여름·겨울엔 학년이 없어서, 체크한 항목 중 가장 이른 학년(`baseYear`)의 방학으로 봄 → 처음 버그(겨울이 3-2보다 앞) 수정

#### 반영

```bash
cd ~/career-navi && git pull
docker restart api
docker run --rm -v ~/career-navi/frontend:/app -w /app node:22 sh -c "npm install && npm run build"
docker restart web
```

## 남은 작업

- [x] 엔진 실패 처리 (PR #6)
- [x] 체험 모드 `/demo` + 체험용 QR (PR #7)
- [ ] 팀원과 `docs/api.md` JSON 형식 확정 (`ncs_code`·`score_gain` 계산 가능 여부, 11/3까지) — 2단계에서 넘어옴
- [ ] `/demo` 서버 반영 → 핸드폰으로 체험 QR 찍어서 확인
- [ ] 팀원 PR #3(공고 역량 추출 Claude API) 리뷰·merge → 서버 반영(`git pull` + `docker restart api`) → Nginx `proxy_read_timeout 120s` → 동작 확인
  - 팀원에게 확인할 것: 모델이 Opus(고가). 역량 추출은 Sonnet으로 충분한지
  - merge 후 매칭·추천은 아직 가짜라 판단보류·빈 추천이 나오는 게 정상
- [ ] 팀원 인수인계 문서(`docs/handoff/`) 요청
- [ ] 진단 결과 DB 저장 (팀원의 교내 자원 표 초안 받은 뒤)
- [ ] 시연 시나리오 점수 맞추기 (팀원의 샘플 데이터)
