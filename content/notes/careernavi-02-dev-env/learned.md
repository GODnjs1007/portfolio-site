---
title: "배운 점"
---

### A. GitHub 레포와 뼈대 파일
- 폴더 구조
    - frontend/ : react
    - backend/ : FastAPI
    - docs/ : API명세
- API 명세 : 서버가 어떤 주소로 어떤 형식의 데이터를 주고 받는지 적는 문서 —> 진단 결과 한 건

    ```json
    {
      "fit_score": 54,
      "competencies": [
        { "id": "c1", "name": "SQL 활용", "type": "필수", "status": "미충족",
          "evidence": { "posting": "SQL을 활용한 데이터 추출 경험", "experience": null } }
      ],
      "recommendations": [
        { "id": "r1", "competency_id": "c1", "kind": "교과목", "title": "데이터베이스",
          "semester": "3-2", "score_gain": 12 }
      ]
    }
    ```

    - competencies : 역량 목록
        - type : 필수 / 우대 / 직무
        - status : 충족 / 부분충족 / 미충족 / 판단보류
        - posting : 공고에서 찾은 문장
            - experience : 내 경험에서 찾은 문장
    - recommendations : 추천 목록
        - competency_id : 이 추천이 어느 역량을 위한 건지 (r1 → c1). 체크하면 그 역량이 충족으로 바뀜
        - kind : 교과목 / 비교과 / 현장실습 / 자격증
        - score_gain : 이걸 시행하면 몇 점 오르는지
    - null 규칙 : 값이 없을 때 문자열이나 “”이나 “없음”으로 쓰지 않고 null 쓰기로 함
    - 엔드포인트 : 서버에서 요청을 받는 주소 (ex : POST /api/diagnose)
- 서버 뼈대 (backend/main.py)

    ```py
    class Competency(BaseModel):          # api.md 형식을 파이썬 클래스로 옮김
        id: str
        type: Literal["필수", "우대", "직무"]  # 이 셋 중 하나만 허용
        status: Literal["충족", "부분충족", "미충족", "판단보류"]

    @app.post("/api/diagnose", response_model=DiagnosisResult)
    def diagnose(req: DiagnoseRequest):
        return MOCK                       # 고정된 가짜 결과 (54%)
        
    @app.get("/api/health")               # GET: 살아있는지 확인용
    def health():
        return {"status": "ok"}
    ```

    - 팀원 엔진 나오기 전 화면 개발 할 수 있게 고정된 가짜 결과 돌려주게 만듦
        - Literal : 정해진 값 중 하나만 허용
    - response_model 걸어두면 형식에 안 맞는 결과 나올 때 FastAPI가 에러나게 해줌
        - MOCK : 가짜 기능 대신 형식만 맞춘 고정 데이터 : 가짜 응답
    - Pydantic : 데이터 형식을 클래스로 정의하고 들어오고 나가는 값이 형식에 맞는지 검사해주는 라이브러리
    - HTTP 메서드 : 요청의 종류
        - GET : 조회 (데이터 안 실음)
            - /api/health
        - POST : 데이터 실어서 보냄
            - /api/diagnose
- CORS 설정

    ```py
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"])
    ```

    - 개발중인 화면 (5173)과 서버 (8000)가 주소가 달라서 서버가 5173에서 오는 요청 받겠다는 허용문
    - CORS : 브라우저가 다른 주소로 가는 요청을 막는 규칙
        - 서버가 허용 목록을 주면 통과
    - 미들웨어 : 모든 요청이 거쳐 가는 중간 처리 단계
- .gitignore / 첫 push

    ```py
    git init
    git add .
    git commit -m "init: 프로젝트 뼈대"
    git push -u origin main
    ```

    - .gitignore
        - .env , node\_modules , .venv , \*.pdf
            - API 키 , 개인정보, 설치 파일이 레포에 올라가지 않게 설정
        - 이후에 main에 바로 올리지 않고 브랜치 → PR → merge로 진행
            - PR (Pull Request) : 브랜치 작업을 main에 합쳐달라는 요청. 팀원 리뷰 가능
            - squash merge : 브랜치 커밋 여러 개를 하나로 합쳐서 main으로 넣는 방식

### B. 로컬에서 FastAPI 서버 실행
- 목적
    - 맥북에서 서버를 직접 띄워 뼈대가 돌아가고 가짜 결과 나오는지 확인
- 설명
    - 로컬에서 실행
        - FastAPI 서버의 서버는 요청 받아주는 프로그램이란 뜻이지 VM이 아님.
            - 주소가 localhost:8000
    - 같은 코드가 맥북과 VM에 각각 있음
        - 맥북 → git push → GitHub → git pull → VM 순서
    - 가상환경 , 패키지 설치

        ```py
        cd ~/career-navi/backend
        python3 -m venv .venv            # 이 프로젝트 전용 파이썬 환경
        source .venv/bin/activate        # 켜기 (터미널 앞에 (.venv) 뜸)
        pip install -r requirements.txt  # 목록대로 한 번에 설치
        ```

        - career-navi 폴더 다운 (클로드 이용)
            - .venv는 python3 -m venv 명령이 폴더까지 만들어줌
        - 프로젝트마다 환경 따로 두면 프로젝트랑 패키지 버전이랑 섞이지 않음
            - venv : 프로젝트 전용 파이썬 환경
                - 설치한 패키지가 이 폴더 안에만 들어감
            - requirements.txt : 필요한 패키지 이름 목록.
                - 팀원도 같은 걸로 설치하면 환경이 같아짐
    - 환경변수 파일

        ```py
        cp .env.example .env
        ```

        - API 키 같은 비밀값은 .env에만
            - .env.example은 이런 키가 필요하다는 빈 양식
        - 환경변수 : 코드 밖에서 넣어주는 설정값
            - 코드를 바꾸지 않고 값만 바꿀 수 있음
    - 서버 실행

        ```bash
        uvicorn main:app --reload        # main.py의 app을 띄움
        ```

        - Application startup complete —> 뜨면 켜짐
        - uvicorn : FastAPI 앱을 실제로 실행해주는 서버 프로그램
            - Django의 runserver과 같은 역할
        - —reload : 코드를 저장하면 서버가 자동으로 켜짐.
    - Swagger로 확인
        - localhost:8000/docs를 열면 API 목록 화면에 뜸
        - POST /api/diagnose —> Try it out → execute → 응답 200
            - fit\_score : 54 확인
            - 응답 200 : 요청이 정상 처리됐다는 HTTP 상태코드
            - POST : 데이터 실어서 보냄
        - GET /api/health → \{”status”: “ok”\}내
            - 서버가 살아있는지만 보는 용도
            - 배포 후에도 점검에 사용
            - GET : 데이터 조회 , 실어 보내진 않음
        - Swagger
            - 코드에서 자동으로 만들어지는 API 문서 겸 테스트 화면
            - 버튼으로 요청 보내볼 수 있음

### C. 홈랩에 서비스용 VM 준비
- 목적
    - 팀원이 들어와서 같이 쓸 서버를 홈랩 미니 PC에 VM으로 새로 만들고 SSH 세팅
- 설명
    - 사양
        - 사양: 103 / careernavi / 2코어 / 4GB / 30GB / Ubuntu Server 26.04
            - RAM은 FAST API , Nginx , DB + 임베딩 모델 (약 2GB) 예상
    - 디스크 확장

        ```bash
        sudo lvextend -l +100%FREE -r /dev/ubuntu-vg/ubuntu-lv   # 남은 공간 전부 루트에
        df -h /                                                   # 확인
        ```

        - 30GB를 줬는데 설치 후 루트가 13.67GB만 잡혀 있어서 28GB로 늘림. Ubuntu 설치 기본값이 LVM 절반만 쓰는 게 원인
            - LVM : 디스크를 나중에 늘리거나 나눌 수 있게 논리적으로 관리하는 방식
                - lvextend : LVM 영역 늘리는 명령어
                - +100%FREE : 남은 공간 전부
                - -r : 파일 시스템까지 다 같이
    - Tailscale 연결

        ```bash
        curl -fsSL https://tailscale.com/install.sh | sh
        sudo tailscale up                 # 로그인 링크 뜸 → 내 계정에 등록
        ```

        - MagicDNS : IP 대신 기기 이름 (careernavi)으로 접속하게 해주는 기능
    - SSH 키 등록

        ```bash
        ssh-copy-id <사용자>@careernavi    # 내 공개키를 VM에 자동 등록
        ```

        - 비밀번호 없이 접속하게 해줌.
        - ssh-copy-id : 공개키를 서버의 authorized\_keys에 자동 추가
            - authorized\_keys : VM에 들어올 수 있는 공개키 목록 파일
    - Docker 설치

        ```bash
        curl -fsSL https://get.docker.com | sudo sh
        sudo usermod -aG docker $USER     # 나를 docker 그룹에 추가
        exit                              # 재접속해야 그룹 적용
        docker run hello-world            # 확인
        ```

        - usermod -aG : 사용자를 그룹에 추가
            - a : 기존 그룹 유지
            - G : 그룹 지정
        - hello-world : Docker가 이미지 받고 → 컨테이너 만들고 → 실행까지 되는지 보는 테스트

### D. 뼈대 배포와 도메인 연결
- 목적
    - 맥북에서 돌던 FastAPI를 VM에 올리고 내 도메인으로 밖에서 접속되게 만듦
- 설명
    - 구조
        - <mark>방문자 → careernavi.ihaewon.com → Cloudflare → tunnel → VM의 Cloudflare → localhost:8000 (FastAPI 컨테이너)</mark>
        - 서브도메인 : 도메인 앞에 이름을 붙인 하위 주소
    - 배포 키로 코드 받기

        ```bash
        ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""   # VM 전용 키
        cat ~/.ssh/github_deploy.pub                            # → GitHub 레포 Deploy keys에 등록
        git clone git@github.com:<내 계정>/career-navi.git ~/career-navi
        ```

        - 내 개인 GitHub 키를 VM에 두지 않고, 이 레포 하나만 읽을 수 있는 키를 따로 만듦
        - Allow write access 체크하지 않음
            - <mark>VM에서 push하지 못 함 —> VM에 직접 코드 고쳐서 push하면 맥북이랑 어긋나기 때문에 받기만 하는 곳으로 고정</mark>
                - 코드 수정은 맥북에서 push
                - VM은 git pull 로 받기만 하고 실행
        - \~/.ssh/config 에 IdentityFile \~/.ssh/github\_deploy를 적어 깃허브 접속할 때 이 키를 쓰게 함
    - FastAPI 컨테이너

        ```bash
        docker run -d --name api --restart unless-stopped \
          -p 8000:8000 \
          -v ~/career-navi/backend:/app -w /app \
          python:3.12-slim \
          sh -c "pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000"
        ```

        - 이미지를 따로 만들지 않고 공식 파이썬 이미지에 코드 폴더 연결해서 시작할 때 설치
            - 코드 바꾸면 git pull + docker restart api 로 변경
            - 대신 킬 때마다 설치해서 첫 응답까지 좀 걸림
        - -v : 볼륨, VM 폴더를 컨테이너 안 폴더에 연결
        - — restart unless-stopped : VM 재부팅돼도 자동 재시작
        - --host 0.0.0.0 : 컨테이너 밖에서 오는 요청도 받음.
            - 기본값이면 컨테이너 안에서만 됨
    - Cloudflare Tunnel

        ```bash
        cloudflared tunnel create careernavi
        cloudflared tunnel route dns careernavi careernavi.ihaewon.com   # DNS 자동 등록
        sudo cloudflared service install                                 # 부팅 시 자동 실행
        ```

        /etc/cloudflared.config.yml

        ```bash
        ingress:
          - hostname: careernavi.ihaewon.com
            service: http://localhost:8000
          - service: http_status:404
        ```

        - VM이 Cloudflare 쪽으로 먼저 연결 맺는 방식
        - 터널 인증 파일 (.json)은 VM에서만 실행
        - CNAME : 이 주소는 저 주소를 따라가라는 DNS 레코드
            - route dns가 자동으로 만듦
            - cloudflare 대시보드 → ihaewon.com → DNS에 존재
                - \<터널ID>.cfargotunnel.com으로 가라고 적어두고 cloudflare가 터널 통해 VM으로 연결

### E. React 화면과 Nginx 배포
- 목표
    - 입력창 , 진단 버튼, 결과가 있는 화면을 만들고 Nginx로 화면과 API를 한 주소에서 서비스
- 설명
    - 구조
        - <mark>방문자 → 터널 → localhost:80 (nginx) → /는 react 빌드 파일, /api/는 FastAPI(8000)</mark>
        - Nginx 는 정문 역할 , 화면 파일은 직접 줌
        - /api/는 뒤의 FastAPI로 넘김
        - 리버스 프록시 : 받은 요청은 뒤쪽 다른 서버로 대신 전달
    - React 프로젝트

        ```bash
        npm create vite@latest frontend -- --template react
        cd frontend && npm install
        npm run dev                          # localhost:5173
        ```

        vite.config.js

        ```bash
        server: { proxy: { '/api': 'http://localhost:8000' } }
        ```

        - 화면 코드는 fetch(’/api/diagnose’) 처럼 상대 주소만 사용
            - 개발땐 Vite, 배포 때는 Nginx가 넘겨줘서 코드 수정없이 둘 다 동작
                - Vite : 리엑트 프로젝트 생성, 개발 서버, 빌드 도구
                - proxy : 개발중 /api 요청을 백엔드로 넘기는 설정
        - 화면이 서버 주소를 몰라도 실행되게 해둠
            - 화면은 /api/… 만 부르고 어디로 보낼지는 Vite(개발), Nginx(배포)가 결정 → 화면 코드 수정 없이 둘 다 동작
    - 빌드 (VM)

        ```bash
        docker run --rm -v ~/career-navi/frontend:/app -w /app node:22 \
          sh -c "npm install && npm run build"      # → frontend/dist
        ```

        - VM에 Node 깔지 않고 빌드할 때만 컨테이너를 잠깐 띄움 → 서버에 도구가 쌓이지 않음
            - 빌드 : 리엑트 코드를 브라우저가 바로 읽는 html, js, css로 묶기
            - —rm : 끝나면 컨테이너 자동 삭제
    - Nginx 설정 (\~/nginx/careernavi.conf)

        ```bash
        server {
            listen 80;
            root /usr/share/nginx/html;
            location / { try_files $uri /index.html; }
            location /api/ { proxy_pass http://host.docker.internal:8000; }
        }
        ```

        ```bash
        docker run -d --name web --restart unless-stopped -p 80:80 \
          --add-host host.docker.internal:host-gateway \
          -v ~/career-navi/frontend/dist:/usr/share/nginx/html \
          -v ~/nginx/careernavi.conf:/etc/nginx/conf.d/default.conf nginx
        ```

        - try\_files : 없는 경로는 리엑트 첫 화면 —> /demo 같은 주소도 리엑트가 받음
        - host.docker.internal : 컨테이너 안에서 자기를 가르킴
        - 설정 파일은 서버마다 달라서 레포가 아닌 VM에서만
    - 터널 대상 변경

        ```bash
        sudo sed -i 's#localhost:8000#localhost:80#' /etc/cloudflared/config.yml
        sudo systemctl restart cloudflared
        ```

        - 8000(FastAPI) → 80(Nginx)으로 바꿈.
            - **바꾸기 전에** VM 안에서 curl localhost로 html 나오는지 먼저 확인
            - <mark>D 과정에서는 화면이 없었고 FastAPI만 있어서 터널을 8000에 꽂았는데 E 과정에서 리엑트 화면이 생기면서 80이 정문이 됨</mark>
                - /api만 FastAPI로 넘기므로 터널 목적지를 바꿈
    - 반영

        ```bash
        cd ~/career-navi && git pull
        docker restart api                                  # 백엔드
        docker run --rm ... node:22 sh -c "npm run build"   # 화면
        docker restart web
        ```
