---
title: "배운 점"
---

### A. 엔진 연결 및 서버 잠금
- 목적
    - 가짜 54% 대신 팀원 엔진 diagnose()를 연결 및 클로드 API 비용이 새지 않게 서버 잠금
- 설명
    - Claud API 준비

        ```bash
        chmod 600 .env          # 나만 읽기
        docker restart api      # .env는 시작할 때만 읽음
        ```

        - 워크스페이스 : 키,사용량,한도를 묶어 관리하는 단위
        - 키는 VM backend/.env에만 저장
    - 엔진 연결

        ```py
        from engine import diagnose as run_engine   # 팀원 엔진 함수를 가져옴. 내 함수도 diagnose라 이름 바꿈
        from engine.judge import fit_score           # 팀원 점수 계산 함수 (What-If에서 씀)

        @app.post("/api/diagnose", response_model=DiagnosisResult)
        def diagnose(req: DiagnoseRequest, request: Request):   # req: 보낸 텍스트 / request: 요청 자체(IP 확인용)
            check_rate_limit(request)                           # 횟수 제한 먼저 검사. 넘으면 여기서 429
            try:
                return run_engine(req.experience_text, req.posting_text)   # 팀원 엔진 실행 → 결과 돌려줌
            except Exception:                                   # 엔진이 뭐든 실패하면
                log.exception("engine 실패")                    # 자세한 에러는 서버 로그에만
                raise HTTPException(502, "AI 분석 중 문제가 생겼어요.")   # 화면엔 짧은 안내만
        ```

        - return MOCK 이었던 자리에서 return run engine(…)으로 변경
        - try / except : 안에서 에러나면 프로그램이 죽지 않고 except로 넘어감
            - Claude API 실패, 팀원 코드 버그, 응답 형식 오류 → 전부 502 하나로 처리
    - 서버 잠금

        ```py
        _docs = os.getenv("ENABLE_DOCS") == "1"              # .env에 ENABLE_DOCS=1 있을 때만 True
        app = FastAPI(
            docs_url="/docs" if _docs else None,             # True면 /docs 열고, 아니면 아예 없음
            openapi_url="/openapi.json" if _docs else None,  # Swagger가 읽는 원본 파일도 같이 끔
        )
        ```

        - 서버 (VM)에는 ENABLE\_DOCS가 없어서 /docs 치면 404

        ```py
        class DiagnoseRequest(BaseModel):
            experience_text: str = Field(min_length=1, max_length=3000)   # 1~3000자만
            posting_text: str = Field(min_length=1, max_length=3000)
        ```

        - 길이 밖이면 FastAPI가 자동으로 422 → 내 코드까지 안옴
            - 토큰 3000자로 제한
            - 길이 밖이면 FastAPI 가 자동으로 422 → 내 코드까지 오지 않음

        ```py
        PER_IP_LIMIT = int(os.getenv("RATE_PER_IP_PER_MIN", "5"))    # IP당 1분 5번
        DAILY_LIMIT = int(os.getenv("RATE_DAILY_TOTAL", "300"))      # 전체 하루 300번

        def _client_ip(request):
            return request.headers.get("cf-connecting-ip") or request.client.host
            # Cloudflare가 붙여준 진짜 방문자 IP. 없으면 직접 연결한 IP

        def check_rate_limit(request):
            hits = _ip_hits[_client_ip(request)]      # 이 IP의 요청 시각 목록
            while hits and now - hits[0] > 60:        # 1분 지난 기록은 버림
                hits.popleft()
            if len(hits) >= PER_IP_LIMIT:             # 1분 안에 5번 넘으면
                raise HTTPException(429, "요청이 너무 많아요.")
            hits.append(now)                          # 통과하면 기록
        ```

        - .env 에서 숫자를 바꿀 수 있게 os.getenv로 읽음
        - 기록은 서버 메모리에만 → 재시작하면 0부터
        - 터널 → Nginx → FastAPI 거치면 request.client.host 가 다 내부 주소라 cloudflare가 붙여주는 cf-connecting-ip 헤더를 봐야 진짜 방문자가 구분
    - pgvector DB

        ```py
        docker run -d --name db --restart unless-stopped \
          -p 127.0.0.1:5432:5432 \                    # VM 안에서만 접속 (밖에서 안 보임)
          -e POSTGRES_PASSWORD=... \                  # 비밀번호는 .env 값
          -v pgdata:/var/lib/postgresql/data \        # 데이터는 볼륨에 → 컨테이너 지워도 남음
          pgvector/pgvector:pg16

        docker exec -it db psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"   # 벡터 기능 켜기
        ```

        - -p 127.0.0.1:5432:5432 → 앞의 127.0.0.1이 핵심
            - 이거 없으면 0.0.0.0이라 VM밖에서도 열림

### B. 진단 리포트 화면
- 목적
    - 계획서 그림 3처럼 적합도 게이지, 역량 카드, What-if, 학기별 로드맵 만들기
- 설명
    - What-if API

        ```py
        class WhatIfRequest(BaseModel):
            competencies: list[Competency]      # 진단 결과의 역량 목록 그대로
            done_ids: list[str]                 # 체크한 역량 id들 (예: ["c2", "c5"])

        @app.post("/api/whatif", response_model=WhatIfResult)
        def whatif(req: WhatIfRequest):
            done = set(req.done_ids)            # 빠르게 찾으려고 set으로
            comps = [
                {"id": c.id, "type": c.type,
                 "status": "충족" if c.id in done else c.status}   # 체크한 건 충족으로 바꿈
                for c in req.competencies
            ]
            return {"fit_score": fit_score(comps)}   # 팀원 judge.py 함수로 점수 계산
        ```

        - 화면이 이 역량들 중 c2, c5를 충족으로 치면 몇 점? 이라고 물어보는 것
        - 점수 공식을 따로 만들지 않고 팀원의 fir\_score을 불러서 팀원이 규칙을 바꿔도 화면이 어긋나지 않음
        - LLM 쓰지않으니 비용, 요청제한이 없음
            - set : 중복 없는 목록
                - in으로 찾는게 list보다 빠름
