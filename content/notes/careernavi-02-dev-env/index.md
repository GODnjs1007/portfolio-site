---
title: "커리어 내비 2단계 · 개발 환경과 프로젝트 뼈대"
date: 2026-10-31
projects: ["career-navi"]
step: 2
summary: "GitHub 레포를 만들고, 팀원과 맞출 진단 결과 JSON 형식을 문서로 정한 뒤, 그 형식대로 가짜 결과를 돌려주는 FastAPI 서버와 React 화면을 만든다. 서비스를 올릴 홈랩 VM을 준비하고 도메인으로 외부에 공개한다."
tags: ["FastAPI", "React", "홈랩", "배포", "트러블슈팅"]
troubleshooting:
  - "팀원 SSH 접속 시 비밀번호를 물어봄"
  - "터널을 Nginx로 바꾼 뒤 사이트가 500 에러"
draft: false
---

## 목표

GitHub 레포를 만들고, 팀원과 맞출 진단 결과 JSON 형식을 문서로 정한 뒤, 그 형식대로 가짜 결과를 돌려주는 FastAPI 서버와 React 화면을 만든다. 서비스를 올릴 홈랩 VM을 준비하고 도메인으로 외부에 공개한다.

## A. GitHub 레포와 뼈대 파일

- 레포 `career-navi` 생성 (Private, README·.gitignore·license 자동 생성 끔)
- 개발 중 API 키가 실수로 올라가도 노출되지 않게 Private으로 만듦. 발표 끝나면 Public으로 전환
- Owner는 내 계정, 팀원은 Collaborator로 초대. 팀 Organization은 필요하면 Transfer로 옮김
  - Collaborator: 레포에 초대된 팀원
  - Transfer: 레포 소유자를 다른 계정·조직으로 옮기는 기능
- 폴더는 `frontend/`(React) · `backend/`(FastAPI) · `docs/`(API 명세) 세 개로 나눔
- `docs/api.md` : 팀원(AI)과 나(웹) 사이의 약속 문서. 진단 결과 JSON 형식과 API 목록, 회의에서 정할 것
  - 엔드포인트: 서버에서 요청을 받는 주소 (예: `POST /api/diagnose`)
- `backend/main.py` : JSON 형식을 Pydantic 클래스로 옮기고, `/api/diagnose`가 고정된 가짜 결과(적합도 54%)를 돌려주게 함 → AI 엔진 없이도 화면 개발을 바로 시작
  - 가짜 응답(mock): 진짜 기능 대신 형식만 맞춘 고정 데이터
  - Pydantic: 들어오고 나가는 데이터 형식을 클래스로 정의하고 검사하는 라이브러리
  - CORS: 다른 주소(React 5173 → FastAPI 8000)에서 오는 요청을 브라우저가 막는 규칙
- React 주소(5173)는 CORS 허용을 미리 설정해둠
- `.gitignore`에 `.env`, `node_modules`, `.venv`, `*.pdf` 추가 → API 키·개인정보 커밋 방지
- 맥북에서 `git init` → `commit` → `push`로 파일 7개 첫 커밋 (`init: 프로젝트 뼈대`)

### 코드

#### docs/api.md : 진단 결과 형식

```json
{
  "diagnosis_id": "d_001",
  "posting_title": "제조 데이터 분석 (신입)",
  "fit_score": 54,
  "competencies": [
    {
      "id": "c1",
      "name": "SQL 활용",
      "type": "필수",
      "ncs_code": "2001010101",
      "status": "미충족",
      "evidence": {
        "posting": "SQL을 활용한 데이터 추출 경험",
        "experience": null
      }
    }
  ],
  "recommendations": [
    {
      "id": "r1",
      "competency_id": "c1",
      "kind": "교과목",
      "title": "데이터베이스",
      "semester": "3-2",
      "url": "https://example.com",
      "score_gain": 12
    }
  ]
}
```

- `type`: 필수 / 우대 / 직무
- `status`: 충족 / 부분충족 / 미충족 / 판단보류
- `kind`: 교과목 / 비교과 / 현장실습 / 자격증
- 근거가 없으면 `null`

#### backend/main.py

```py
"""커리어 내비 백엔드 — 1단계: 가짜 데이터로 형식만 맞춰 둔 뼈대."""
import os
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Career Navi API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- docs/api.md 형식을 그대로 옮긴 것 ----
class Evidence(BaseModel):
    posting: Optional[str] = None
    experience: Optional[str] = None


class Competency(BaseModel):
    id: str
    name: str
    type: Literal["필수", "우대", "직무"]
    ncs_code: Optional[str] = None
    status: Literal["충족", "부분충족", "미충족", "판단보류"]
    evidence: Evidence


class Recommendation(BaseModel):
    id: str
    competency_id: str
    kind: Literal["교과목", "비교과", "현장실습", "자격증"]
    title: str
    semester: Optional[str] = None
    url: Optional[str] = None
    score_gain: int = 0


class DiagnosisResult(BaseModel):
    diagnosis_id: str
    posting_title: str
    fit_score: int
    competencies: list[Competency]
    recommendations: list[Recommendation]


class DiagnoseRequest(BaseModel):
    experience_text: str
    posting_text: str


# ---- 가짜 응답 (AI 엔진 붙기 전까지) ----
MOCK = DiagnosisResult(
    diagnosis_id="d_001",
    posting_title="제조 데이터 분석 (신입)",
    fit_score=54,
    competencies=[
        Competency(id="c1", name="SQL 활용", type="필수", status="미충족",
                   evidence=Evidence(posting="SQL을 활용한 데이터 추출 경험")),
        Competency(id="c2", name="Python 데이터 분석", type="필수", status="충족",
                   evidence=Evidence(posting="Python 기반 데이터 분석 역량",
                                     experience="수업 프로젝트에서 pandas로 매출 데이터 분석")),
        Competency(id="c3", name="현장 데이터 프로젝트", type="우대", status="미충족",
                   evidence=Evidence(posting="제조 현장 데이터 분석 프로젝트 경험자 우대")),
    ],
    recommendations=[
        Recommendation(id="r1", competency_id="c1", kind="교과목", title="데이터베이스",
                       semester="3-2", score_gain=12),
        Recommendation(id="r2", competency_id="c3", kind="현장실습", title="동계 현장실습",
                       semester="겨울", score_gain=12),
    ],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/diagnose", response_model=DiagnosisResult)
def diagnose(req: DiagnoseRequest):
    # TODO: 팀원 엔진 연결
    return MOCK
```

#### .gitignore

```bash
.env
*.env
!.env.example
__pycache__/
*.pyc
.venv/
venv/
node_modules/
dist/
.DS_Store
.vscode/
.idea/
data/private/
*.pdf
```

#### 첫 push (맥북)

```bash
cd ~/career-navi
git init
git add .
git commit -m "init: 프로젝트 뼈대"
git branch -M main
git remote add origin git@github.com:<내 계정>/career-navi.git
git push -u origin main
```

- 이후 작업은 main에 바로 올리지 않고 브랜치 → PR → squash merge로 진행 (PR #1 인수인계 문서부터)
  - 브랜치: main을 건드리지 않고 따로 작업하는 갈래
  - PR(Pull Request): 브랜치 작업을 main에 합쳐달라는 요청. 팀원이 리뷰할 수 있음
  - squash merge: 브랜치의 커밋 여러 개를 하나로 합쳐서 main에 올리는 방식 → main 기록이 PR 단위로 깔끔하게 남음
- 인수인계는 `docs/handoff/날짜_이름.md`로 레포에 남기기로 팀원과 합의 (첫 문서 `2026-10-28_haewon.md`)

## B. 로컬에서 FastAPI 서버 실행

- `backend/`에서 가상환경 만들고 패키지 설치
  - venv: 프로젝트마다 따로 쓰는 파이썬 환경. 다른 프로젝트와 패키지 버전이 안 섞임
  - requirements.txt: 필요한 패키지 목록. `pip install -r`로 한 번에 설치
- `.env.example`을 `.env`로 복사 (API 키 같은 비밀값은 여기에만)
- `uvicorn main:app --reload`로 서버 실행 → `Application startup complete.`
  - uvicorn: FastAPI 앱을 실제로 띄워주는 서버 프로그램 (Django의 `runserver` 역할)
  - `--reload`: 코드를 저장하면 서버가 자동으로 다시 켜짐
- 서버는 끝나는 명령이 아니라 계속 켜져 있음. 끄려면 `Ctrl + C`
- `localhost:8000/docs`에서 Swagger 화면 확인 (`GET /api/health`, `POST /api/diagnose`, Schemas)
  - Swagger: 코드에서 자동으로 만들어지는 API 문서 겸 테스트 화면

### 명령어 (맥북)

```bash
cd ~/career-navi/backend
python3 -m venv .venv
source .venv/bin/activate        # 윈도우: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload        # http://localhost:8000/docs
```

- 터미널 앞에 `(.venv)`가 붙으면 가상환경이 켜진 상태
- Swagger에서 `POST /api/diagnose` → Try it out → Execute → 응답 `200`, `fit_score: 54` 확인
- `GET /api/health` → `{"status": "ok"}` : 서버가 살아 있는지 확인하는 용도. 배포 후 점검에도 계속 씀
  - source: 현재 터미널에 가상환경 설정을 적용하는 명령
  - 200: 요청이 정상 처리됐다는 HTTP 상태 코드

### requirements.txt

```txt
fastapi
uvicorn[standard]
pydantic
python-dotenv
```

- python-dotenv : `.env` 파일 값을 환경변수로 읽어옴 (`load_dotenv()`)

## C. 홈랩에 서비스용 VM 준비

### 1. 왜 VM을 새로 만들었나

- 팀원이 SSH로 들어와서 작업할 서버라, 기존 VM(portfolio·ecg)과 분리해 프로젝트 전용 VM을 따로 만듦
- 팀원에게 docker 권한을 주면 그 VM에선 사실상 관리자라서, 내 다른 서비스가 있는 VM에 같이 두면 안 됨
- 사양은 들어갈 것 기준으로 잡음 : FastAPI·Nginx·PostgreSQL(1GB 안쪽) + 한국어 임베딩 모델(약 2GB) + 여유 → RAM 4GB
- 미니PC RAM 16GB를 다른 VM과 나눠 쓰는 중이라 필요한 만큼만 배정. 임베딩 모델이 정해지면 6GB로 늘릴지 다시 판단

### 2. VM 생성

- Proxmox 웹 UI → 오른쪽 위 Create VM
- ISO는 홈랩 1단계에서 올려둔 ubuntu-26.04.1-live-server-amd64.iso 재사용

| 항목 | 값 |
| --- | --- |
| VM ID / Name | 103 / careernavi |
| OS | Ubuntu Server 26.04 |
| Disk | 30GB |
| CPU | 2 cores |
| Memory | 4GB |

- 메모리를 정할 때 Proxmox Summary에서 다른 VM들이 쓰는 메모리를 먼저 확인하고, 남는 범위 안에서 4GB로 정함 (ecg는 곧 끌 예정이라 여유 계산에 넣음)

### 3. Ubuntu 설치

- Type of install : Ubuntu Server
- Network : DHCP로 집 공유기에서 IP 자동 할당
- Server name : careernavi
- Install OpenSSH server 체크 → 맥북 터미널에서 SSH로 접속하기 위함
- 설치 끝나고 Proxmox → 103 (careernavi) → Console에서 로그인 확인

### 4. 루트 디스크 확장

- 30GiB를 줬는데 `df -h /`로 보니 루트가 13.67GB만 잡혀 있음
- Ubuntu 설치 기본값이 LVM 영역의 절반 정도만 루트에 할당해서 생긴 일 (홈랩 portfolio VM 때와 같은 현상)
- 남은 공간을 전부 루트에 붙여서 28GB로 늘림

```bash
sudo lvextend -l +100%FREE -r /dev/ubuntu-vg/ubuntu-lv
df -h /
```

- 결과 : 13.67GB → 28GB
  - LVM: 디스크를 나중에 늘리거나 나눌 수 있게 논리적으로 관리하는 방식
  - lvextend: LVM 영역 크기를 늘리는 명령
  - +100%FREE: 남은 공간 전부
  - -r: 파일시스템(ext4) 크기까지 같이 늘림

### 5. Tailscale 연결

- Proxmox 콘솔(noVNC)은 복붙이 안 돼서, Tailscale부터 깔고 이후 작업은 맥북 터미널에서 SSH로 함

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4
```

- `tailscale up`에서 나온 로그인 링크로 내 Tailscale 계정에 기기 등록
- 맥북에서 `ssh <사용자>@careernavi`로 접속 성공 → 집 밖에서도 접속 가능
  - Tailscale: 내 기기들끼리만 묶는 사설 네트워크(VPN). 공유기 포트를 열지 않아도 밖에서 접속 가능
  - MagicDNS: IP 대신 기기 이름(careernavi)으로 접속하게 해주는 Tailscale 기능

### 6. SSH 키 등록 (맥북·데스크톱)

- 맥북에 이미 있던 키(`~/.ssh/id_ed25519`)를 VM에 등록 → 비밀번호 없이 접속

```bash
ssh-copy-id <사용자>@careernavi
```

- 중간에 맥북 → 데스크톱으로 자리를 옮겨서, 데스크톱에서도 키를 새로 만들어 같은 방식으로 등록

```bash
ssh-keygen -t ed25519
ssh-copy-id <사용자>@careernavi
```

- 데스크톱도 같은 Tailscale 계정이라 바로 VM 이름으로 접속됨
  - 공개키: VM에 걸어두는 자물쇠 (.pub)
  - 개인키: 내 컴퓨터에만 두는 열쇠. 절대 밖으로 보내지 않음
  - authorized_keys: VM에 들어올 수 있는 공개키 목록 파일 (`~/.ssh/authorized_keys`)
  - ssh-copy-id: 내 공개키를 서버의 authorized_keys에 자동으로 추가해주는 명령

### 7. 업데이트와 Docker 설치

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit
```

- 다시 접속한 뒤 확인

```bash
groups
docker run hello-world
```

- `groups`에 docker가 보이고, `Hello from Docker!` 출력 → Docker 설치·권한 정상
  - usermod -aG docker: 사용자를 docker 그룹에 추가 (a: 기존 그룹 유지하고 추가, G: 그룹)
  - docker 그룹: sudo 없이 docker 명령을 쓸 수 있는 권한. 컨테이너로 호스트 파일을 건드릴 수 있어서 사실상 관리자 권한
  - exit: 그룹 권한은 로그인할 때 읽어서 재접속해야 적용됨

### 8. 팀원 계정 만들기

- 내 계정을 같이 쓰지 않고 팀원 전용 계정 `teammate`을 따로 만듦 → 누가 무엇을 했는지 구분되고, 필요하면 이 계정만 막으면 됨
- 비밀번호 없이 SSH 키로만 들어오게 만듦

```bash
sudo adduser --disabled-password --gecos "" teammate
sudo usermod -aG docker teammate
sudo mkdir -p /home/teammate/.ssh
echo "팀원 공개키 한 줄" | sudo tee -a /home/teammate/.ssh/authorized_keys
sudo chmod 700 /home/teammate/.ssh
sudo chmod 600 /home/teammate/.ssh/authorized_keys
sudo chown -R teammate:teammate /home/teammate/.ssh
```

- 팀원에게는 개인키가 아니라 공개키(.pub 내용 한 줄)만 받음
  - --disabled-password: 비밀번호 로그인이 불가능한 계정으로 생성
  - --gecos "": 이름·전화번호 같은 추가 정보 질문 건너뛰기
  - tee -a: 파일 끝에 덧붙이기. -a 없이 쓰면 기존 키를 덮어씀
  - chmod 700 / 600: .ssh 폴더와 키 파일을 본인만 읽게 제한. 권한이 넓으면 SSH가 키를 무시함
  - chown: 파일 주인을 teammate로 바꿈 (sudo로 만들어서 주인이 root로 돼 있음)

### 9. Tailscale Share로 팀원 접속

- 내 Tailscale 관리 화면 → Machines → careernavi → Share → 팀원 이메일로 초대
- 내 Tailscale 네트워크 전체가 아니라 careernavi 한 대만 공유됨 (다른 VM·pve는 안 보임)
- 팀원이 자기 노트북에 Tailscale을 깔고 초대 수락 → `ssh teammate@careernavi` 접속 성공
- 처음엔 비밀번호를 물어보는 문제가 있었는데, 키를 다시 만들어 지문이 달라졌던 것 → 새 공개키로 다시 등록해서 해결 (트러블슈팅 1번 참고)
  - Tailscale Share: 내 네트워크의 특정 기기 하나만 다른 Tailscale 계정에 공유하는 기능
  - 지문(fingerprint): 키마다 고유한 짧은 식별값. 서로 비교하면 같은 키인지 확인 가능

### 10. 최종 상태

- careernavi VM : Ubuntu Server 26.04, 루트 28GB, Docker 설치
- 접속 가능한 사람 : 이해원(맥북·데스크톱 키), 팀원(노트북 키). 모두 Tailscale 안에서만, 키로만
- 공유기 포트는 하나도 열지 않음. 외부 공개는 이후 Cloudflare Tunnel로 함 (D 참고)

## D. 뼈대 배포와 도메인 연결

- 구조 : 방문자 → `https://careernavi.ihaewon.com` → Cloudflare(HTTPS·DNS) ⇄ 터널 ⇄ cloudflared(careernavi VM) → `localhost:8000` → FastAPI 컨테이너
- 도메인은 새로 사지 않고 갖고 있는 `ihaewon.com`의 서브도메인 `careernavi.ihaewon.com` 사용 → DNS 레코드만 추가하면 돼서 추가 비용 없음
  - 서브도메인: 도메인 앞에 이름을 붙여 만드는 하위 주소
- VM에 GitHub 배포 키(읽기 전용) 등록 → Private 레포를 `git clone`. write 권한을 안 줘서 VM은 코드를 받기만 하고 올리지 못함
  - 배포 키(Deploy key): 레포 하나에만 쓰는 SSH 키
- `~/.ssh/config`에 `Host github.com` → `IdentityFile ~/.ssh/github_deploy`로 어떤 키를 쓸지 지정
- FastAPI를 `python:3.12-slim` 컨테이너로 실행 (8000번, `--restart unless-stopped`)
- 코드 폴더를 `-v`로 컨테이너에 연결 → `git pull` 후 `docker restart api`만 하면 반영
- 첫 `curl`은 컨테이너가 아직 `pip install` 중이라 실패 → `docker logs -f api`로 `Uvicorn running` 확인 후 성공
  - `-v`(볼륨): VM 폴더를 컨테이너 안 폴더에 연결
  - `--restart unless-stopped`: VM이 재부팅돼도 컨테이너 자동 재시작
- cloudflared 설치 → 터널 `careernavi` 생성 → `/etc/cloudflared/config.yml` 작성 → `route dns` → systemd 서비스 등록 (포폴 사이트와 같은 방식, 터널만 별도)
  - ingress: 들어온 주소별로 어디로 보낼지 정하는 규칙 (여기선 `careernavi.ihaewon.com` → `http://localhost:8000`, 나머지는 404)
- 터널 인증 파일(.json)은 VM에만 두고 Git에 올리지 않음
- 외부에서 `https://careernavi.ihaewon.com/docs` 접속 성공
- 발표용 QR 생성 : `https://careernavi.ihaewon.com` (오류 보정 H단계, 인쇄물이 일부 가려져도 인식)

### 명령어·설정

#### 1. 배포 키 만들기 (VM)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub
```

- 출력된 공개키를 GitHub 레포 → Settings → Deploy keys → Add deploy key에 등록. `Allow write access`는 체크 안 함
  - -f: 키 파일 이름 지정 (기존 id_ed25519와 안 겹치게)
  - -N "": 키 비밀번호 없이 생성 (서버가 자동으로 pull해야 해서)

#### 2. ~/.ssh/config

```txt
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_deploy
```

```bash
ssh -T git@github.com     # 인증 확인
git clone git@github.com:<내 계정>/career-navi.git ~/career-navi
```

#### 3. FastAPI 컨테이너 (api)

```bash
docker run -d --name api --restart unless-stopped \
  -p 8000:8000 \
  -v ~/career-navi/backend:/app -w /app \
  python:3.12-slim \
  sh -c "pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000"

docker logs -f api                 # Uvicorn running 뜰 때까지 대기
curl localhost:8000/api/health     # {"status":"ok"}
```

- 이미지를 따로 만들지 않고, 공식 파이썬 이미지에 코드 폴더를 연결해서 시작할 때 패키지 설치 → 구조가 단순하고 코드 수정은 재시작만으로 반영
- 대신 컨테이너를 켤 때마다 `pip install`을 해서 첫 응답까지 수십 초 걸림 (첫 curl 실패 원인)
  - -d: 백그라운드 실행
  - -w /app: 컨테이너 안 작업 폴더
  - --host 0.0.0.0: 컨테이너 밖(VM)에서 들어오는 요청도 받게 함. 기본값(127.0.0.1)이면 컨테이너 안에서만 접속됨
  - slim: 꼭 필요한 것만 넣은 가벼운 이미지

#### 4. Cloudflare Tunnel

```bash
cloudflared tunnel login
cloudflared tunnel create careernavi
cloudflared tunnel route dns careernavi careernavi.ihaewon.com
```

`/etc/cloudflared/config.yml`

```yaml
tunnel: <터널 ID>
credentials-file: /etc/cloudflared/<터널 ID>.json

ingress:
  - hostname: careernavi.ihaewon.com
    service: http://localhost:8000      # E단계에서 80(Nginx)으로 바꿈
  - service: http_status:404
```

```bash
sudo cloudflared service install
sudo systemctl status cloudflared
```

- `route dns`가 Cloudflare DNS에 CNAME 레코드를 자동으로 만들어줌 → 대시보드에서 직접 안 만져도 됨
- 공유기 포트를 열지 않고, VM이 Cloudflare 쪽으로 먼저 연결을 맺는 방식이라 집 IP가 밖에 드러나지 않음
  - CNAME: 이 주소는 저 주소를 따라가라는 DNS 레코드
  - credentials-file: 이 터널을 쓸 수 있다는 인증 파일. 유출되면 남이 내 터널을 쓸 수 있어서 Git에 안 올림
  - http_status:404: 위 규칙에 안 맞는 주소는 404로 막음
  - systemd 서비스: VM 부팅 시 자동 실행되는 백그라운드 프로그램

#### 5. 코드 반영 방법

```bash
cd ~/career-navi && git pull
docker restart api
```

## E. React 화면과 Nginx 배포

- 구조 : 방문자 → `careernavi.ihaewon.com` → Cloudflare ⇄ 터널 → `localhost:80` → Nginx 컨테이너(web) → `/`는 React 빌드 파일(dist), `/api/`는 FastAPI 컨테이너(api, 8000)
- 맥북에서 `npm create vite`로 React 프로젝트 생성 → 입력창 2개 + 진단하기 버튼 + 결과(적합도·역량·추천) 화면 초안
  - Vite: React 프로젝트를 만들고 개발 서버(`npm run dev`, 5173)·빌드(`npm run build`)를 해주는 도구
  - proxy: 개발 중 화면(5173)의 `/api` 요청을 백엔드(8000)로 넘기는 설정
- Vite proxy를 써서 화면 코드에 서버 주소를 박지 않음
- 맥북 `localhost:5173`에서 진단하기 → 54% 확인 후 push
- VM에는 Node를 설치하지 않고 `node:22` 컨테이너로 한 번만 빌드 → `frontend/dist` 생성
  - 빌드: React 코드를 브라우저가 바로 읽는 html·js·css 파일로 묶는 것
- Nginx 컨테이너 `web`(80번) : `/`는 dist 파일, `/api/`는 FastAPI로 넘김
  - 리버스 프록시: 받은 요청을 뒤쪽 다른 서버로 대신 전달하는 것 (`proxy_pass`)
  - `host.docker.internal`: 컨테이너 안에서 VM 자신을 가리키는 이름. `--add-host`로 지정
  - `try_files $uri /index.html`: 없는 경로는 React 첫 화면으로 보냄
- 터널 대상을 8000(FastAPI) → 80(Nginx)으로 변경 → 외부에서 화면·API 모두 접속 (트러블슈팅 2번 참고)
- 확인 : `curl localhost` → `<!doctype html>`, `curl localhost/api/health` → `{"status":"ok"}`
- VM에서 `git push` 시도 → 배포 키가 읽기 전용이라 거부됨 (의도한 대로 동작)
- 데스크톱(윈도우) 공개키도 `authorized_keys`에 `>>`로 추가 → 집 안에서는 공유기 내부 IP로도 접속

### 명령어·설정

#### 1. React 프로젝트 (맥북)

```bash
cd ~/career-navi
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm run dev          # http://localhost:5173
```

`frontend/vite.config.js`

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- 화면 코드는 `fetch('/api/diagnose')`처럼 상대 주소만 씀 → 개발 땐 Vite가, 배포 땐 Nginx가 `/api`를 FastAPI로 넘겨서 코드 수정 없이 둘 다 동작
- 같은 주소(도메인)에서 화면과 API가 같이 나가서 배포 환경에선 CORS 문제도 안 생김

#### 2. 빌드 (VM)

```bash
cd ~/career-navi && git pull
docker run --rm -v ~/career-navi/frontend:/app -w /app node:22 \
  sh -c "npm install && npm run build"
ls frontend/dist      # index.html, assets/
```

- VM에 Node를 깔지 않고 빌드할 때만 컨테이너를 잠깐 띄움 → 서버에 도구가 쌓이지 않음
  - --rm: 실행이 끝나면 컨테이너 자동 삭제

#### 3. Nginx 설정 (`~/nginx/careernavi.conf`)

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://host.docker.internal:8000;
    }
}
```

#### 4. Nginx 컨테이너 (web)

```bash
docker run -d --name web --restart unless-stopped \
  -p 80:80 \
  --add-host host.docker.internal:host-gateway \
  -v ~/career-navi/frontend/dist:/usr/share/nginx/html \
  -v ~/nginx/careernavi.conf:/etc/nginx/conf.d/default.conf \
  nginx

curl localhost                 # <!doctype html>
curl localhost/api/health      # {"status":"ok"}
```

- Nginx 설정 파일은 서버 환경에 따라 달라서 레포가 아니라 VM에만 둠
  - host-gateway: 컨테이너에서 본 VM(호스트)의 주소
  - conf.d/default.conf: Nginx가 기본으로 읽는 설정 파일 자리. 여기에 내 설정을 덮어씌움

#### 5. 터널 대상 변경

```bash
sudo sed -i 's#http://localhost:8000#http://localhost:80#' /etc/cloudflared/config.yml
sudo systemctl restart cloudflared
```

- 반드시 VM 안에서 `curl localhost`가 html을 돌려주는 걸 확인한 뒤에 바꿈 (트러블슈팅 2번 참고)

#### 6. 이후 반영 방법

```bash
cd ~/career-navi && git pull
docker restart api                 # 백엔드만 바뀐 경우
docker run --rm -v ~/career-navi/frontend:/app -w /app node:22 sh -c "npm install && npm run build"
docker restart web                 # 화면까지 바뀐 경우
```

#### 최종 컨테이너 구성

| 컨테이너 | 이미지 | 포트 | 역할 |
| --- | --- | --- | --- |
| web | nginx | 80 | 화면 파일 + /api 전달 |
| api | python:3.12-slim | 8000 | FastAPI + AI 엔진 |
| db | pgvector/pgvector:pg16 | 127.0.0.1:5432 | 교내 자원 검색용 DB (3단계 A) |

## 남은 작업

- [x] Swagger에서 `POST /api/diagnose` 실행해 `fit_score: 54` 확인
- [x] 홈랩에 `careernavi` VM 만들기 (Tailscale, SSH 키, Docker)
- [x] 팀원 계정 만들고 SSH 키 등록, Tailscale로 VM 공유
- [x] 팀원 GitHub 아이디 받아서 Collaborator 초대
- [x] careernavi VM에 뼈대 배포, `careernavi.ihaewon.com` 연결, QR 생성
- [x] React 화면 만들고 Nginx로 배포 → 도메인에서 진단 화면 확인
- [x] Claude API 전용 워크스페이스(`career-navi`) + 키(`careernavi-server`, 30일) → VM `backend/.env`에만 (`chmod 600`)
- [x] `career-navi` 워크스페이스 지출 한도 $30
- [x] pgvector DB 컨테이너(`db`, 127.0.0.1:5432) + `vector` 확장
- [x] 팀원 엔진(`diagnose()`) 연결 + `/docs` 외부 차단 + 요청 횟수 제한(IP당 분당 5회, 하루 300회) + 입력 3000자 제한 (PR #4)

## 트러블슈팅

### 1. 팀원 SSH 접속 시 비밀번호를 물어봄

- 증상 : 팀원 노트북(윈도우)에서 `ssh teammate@careernavi` 접속 시 비밀번호 입력 창이 뜨고 들어가지지 않음. 계정은 비밀번호 없이(`--disabled-password`) 만들어서 키로만 들어갈 수 있음
- 확인한 것
  - 서버 로그 `sudo journalctl -u ssh -n 20` : `Failed password for teammate` 만 있고 `Accepted publickey` 없음 → 연결·아이디는 정상, 키 인증만 실패
  - 양쪽 키 지문 비교 `ssh-keygen -lf` : 팀원 노트북 `SHA256:ajaX...` vs 서버 등록 키 `SHA256:UzSn...` → 다름
- 원인 : 키를 보낸 뒤 팀원 노트북에서 `ssh-keygen`이 다시 실행돼 키가 새로 바뀜. 서버에는 예전 공개키가 등록돼 있었음
- 해결 : 현재 공개키를 다시 받아 `authorized_keys`를 덮어쓰고, 지문이 같은지 확인 후 접속 성공
- 재발 방지 : 키를 등록한 뒤에는 바로 양쪽 지문(`ssh-keygen -lf`)을 비교해서 맞는지 확인한다
  - 지문(fingerprint): 긴 공개키를 짧게 요약한 값. 같으면 같은 키
  - journalctl: systemd 서비스 로그를 보는 명령. `-u ssh`는 SSH 서버 로그만

### 2. 터널을 Nginx로 바꾼 뒤 사이트가 500 에러

- 증상 : 터널 대상을 8000 → 80(Nginx)으로 바꾸자 `careernavi.ihaewon.com`이 `500 Internal Server Error`
- 확인한 것
  - VM `git pull` → `Already up to date`, `ls frontend` → 비어 있음 → GitHub에 React 코드가 없음
  - `npm ci` 실패(`package-lock.json` 없음) → `frontend/dist` 생성 안 됨 → Nginx가 보낼 파일이 없어 500
- 원인 : React 코드를 맥북에서 만들고 push하지 않은 상태로 VM 배포를 진행. 빌드 결과를 확인하기 전에 터널부터 전환함
- 해결 : 터널을 8000으로 되돌려 기존 화면(Swagger) 복구 → 맥북에서 push → VM에서 `git pull`·`npm install && npm run build`·`docker restart web` → `curl localhost`로 html 확인 후 터널 80으로 전환
- 재발 방지 : 정문(터널)을 바꾸기 전에 새 대상이 VM 안에서 정상 응답하는지(`curl localhost`) 먼저 확인한다
  - `npm ci`: `package-lock.json`대로 정확히 설치하는 명령. lock 파일이 없으면 실패. `npm install`은 없어도 설치하면서 새로 만듦
