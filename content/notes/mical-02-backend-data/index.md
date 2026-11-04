---
title: "MiCAL 2단계 · 백엔드 배포와 데이터 적재"
date: 2026-11-02
projects: ["web-project"]
step: 2
summary: "(진행 중) 1단계에서 만든 서버 위에 Django 백엔드(회원가입·로그인, 일정 API)와 PostgreSQL을 실제로 띄우고, 팀원 크롤러가 모은 학사·장학금·공모전·비교과 데이터를 DB에 넣는다. 팀원 중 서버가 필요한 사람에게만 계정을 준다."
tags: ["Django", "PostgreSQL", "Docker Compose", "Nginx", "트러블슈팅", "진행 중"]
troubleshooting:
  - "크롤러 결과 저장 실패 (Permission denied)"
  - "소프트웨어학부 공지만 SSL 오류"
  - "컨테이너를 띄운 직후 curl이 Connection reset"
draft: false
---

## 목표

1단계에서 만든 서버 위에 Django 백엔드(회원가입·로그인, 일정 API)와 PostgreSQL을 실제로 띄우고, 팀원 크롤러가 모은 학사·장학금·공모전·비교과 데이터를 DB에 넣는다. 팀원 중 서버가 필요한 사람에게만 계정을 준다. (11/2 진행 회의 1 준비 사항)

## A. 백엔드 뼈대와 서버 배포

- Django 5.2 + Django REST Framework로 백엔드 뼈대를 만듦 (`backend/`, PR #2)
  - `config/` 설정·주소 연결, `accounts/` 회원, `events/` 일정
  - DRF: Django로 JSON API를 쉽게 만들게 해주는 추가 도구
- 일정 테이블 `Event`는 `docs/data-format.md`와 1:1로 맞춤. 팀원이 추가한 `description`(내용)도 포함
  - `owner`가 비어 있으면 모두가 보는 공식 일정, 차 있으면 그 사람만 보는 개인 일정
  - 중복 방지 규칙 2개: 공식 일정은 `source + external_id`, 개인·런어스 일정은 `owner + source + external_id`
  - 부분 유니크 제약: 조건에 맞는 행끼리만 중복을 막는 DB 규칙. 같은 과제가 사람마다 따로 있어도 충돌하지 않음
- API
  - `POST /api/auth/signup/` · `login/` · `logout/`, `GET /api/auth/me/`
  - `GET /api/events/?start=&end=&source=&department=` 공식 일정 + 내 개인 일정
  - `POST / PATCH / DELETE /api/events/` 내 개인 일정만. 남의 일정이나 공식 일정을 지우려면 403
  - `GET /api/health/` 서버 살아 있는지 확인용
- 로그인 정보 관리
  - 비밀번호는 원문이 아니라 해시(PBKDF2)로만 저장. 8자 이상, 흔한 비번·숫자만인 비번 거절
  - 해시: 원래 값으로 되돌릴 수 없게 바꾼 값. DB가 유출돼도 비번 원문은 안 나옴
  - 토큰 인증: 로그인하면 긴 문자열(토큰)을 받고, 이후 요청마다 헤더에 붙여서 본인임을 증명
  - DB 비번·`DJANGO_SECRET_KEY`는 서버 `.env`에만. 깃에는 이름만 적은 `.env.example`
  - 런어스는 아이디·비번을 받지 않음 (iCal URL 방식, 차주 논의)
- 테스트 8개 작성 → 통과 (해시 저장, 약한 비번 거절, 남의 개인 일정 안 보임, 공식 일정 삭제 막힘, import 중복 없음 등)
- `docker-compose.yml`에 `web`(Django) 컨테이너 추가
  - 컨테이너가 켜질 때마다 `migrate` → `collectstatic` → gunicorn 순서로 실행 (`entrypoint.sh`)
  - gunicorn: 파이썬 웹 앱을 실제 서비스로 돌려주는 서버 프로그램
  - migrate: 코드에 적은 테이블 구조를 실제 DB에 반영하는 명령
  - db에 healthcheck를 넣고 web은 db가 준비된 뒤에 켜지게 함
  - healthcheck: 컨테이너가 진짜 일할 수 있는 상태인지 주기적으로 확인하는 검사
- nginx 설정(`infra/nginx/default.conf`): `/api/`, `/admin/`, `/django-static/`은 Django로, 나머지는 프론트 정적 파일
  - 리버스 프록시: 앞에서 요청을 받아 주소에 따라 뒤쪽 서버로 나눠 보내는 역할
  - 화면과 API가 같은 주소(`calendar.ihaewon.com`)라 CORS 설정이 필요 없음
  - CORS: 다른 주소의 화면이 내 API를 부르는 걸 브라우저가 막는 보안 규칙
- VM에서 배포: `.env` 작성 → `docker compose up -d --build` → 컨테이너 3개(db healthy, web, frontend) 확인

```txt
campus-calendar-db-1         postgres:16           Up (healthy)   5432/tcp
campus-calendar-frontend-1   nginx:alpine          Up             127.0.0.1:8080->80/tcp
campus-calendar-web-1        campus-calendar-web   Up             8000/tcp
```

- `curl -i localhost:8080/api/health/` → `200 OK`, `{"status": "ok"}`
  - 띄운 직후 첫 curl은 `Connection reset` (트러블슈팅 3번 참고)

```txt
HTTP/1.1 200 OK
Server: nginx/1.31.8
Content-Type: application/json

{"status": "ok"}
```

- `createsuperuser`로 관리자 계정 생성 → `https://calendar.ihaewon.com/admin/` 로그인 확인
  - 관리자 아이디는 `admin`을 피함. 공격하는 쪽이 가장 먼저 넣어보는 이름이라
- 관리자 페이지에 인증 및 권한(그룹·사용자), 인증 토큰, 일정(Events) 메뉴가 보임

## B. 팀원 서버 계정

- 서버 할당 기준: 서버에서 직접 무엇을 돌려야 하는 사람만 계정을 줌
  - 크롤링 담당 팀원: 크롤러 실행과 데이터 적재 때문에 계정 발급
  - 나머지 팀원(PM·UI·UX): 서버 접속 없이 GitHub으로만 작업
- calendar VM에 팀원 계정 `teammate` 생성
  - `adduser --disabled-password`: 비밀번호 로그인 없이 SSH 키로만 들어오게 함
  - docker 그룹에 추가 → `docker compose exec`로 데이터 넣기를 직접 할 수 있음
- 팀원 공개키는 커리어 내비(careernavi) VM에 등록돼 있던 것을 그대로 가져와 `authorized_keys`에 넣음
  - 공개키는 공개해도 되는 열쇠라 같은 사람이면 서버 여러 대에 같은 키를 등록해도 됨
  - `ssh 서버 "sudo ..."`처럼 한 줄로 sudo를 보내면 비번 입력창이 없어 실패 → `ssh -t`로 터미널을 붙여서 해결
  - `-t`: 원격 명령에 입력창(터미널)을 붙여주는 옵션
- `id teammate`으로 docker 그룹 포함 확인

```txt
uid=1001(teammate) gid=1001(teammate) groups=1001(teammate),100(users),983(docker)
```

- Tailscale에서 `calendar` 기기를 팀원에게 공유 (팀원은 이 VM에만 접근)
- 맥북 키도 calendar VM에 등록돼 있음을 확인 (비번 없이 접속)

## C. 크롤링 데이터 적재

- PR #1(팀원 크롤러) → PR #2(백엔드) 순서로 main에 합침
  - `.gitignore` 한 줄 충돌 → 팀원 쪽 주석으로 맞추고 테스트 다시 돌려 통과 확인
  - GitHub 무료 요금제는 Private 저장소에 main 브랜치 보호를 못 걸어서 "main 직접 push 금지"는 팀 약속으로 지킴
- VM을 main으로 맞추고 다시 빌드
- 크롤러는 VM에 파이썬 가상환경(`~/crawler-venv`)을 따로 만들어 실행
  - 가상환경(venv): 프로젝트별로 패키지를 따로 설치하는 공간. 서버 전체 파이썬을 건드리지 않음
- `python -m crawler.run --since 2026-09-01` (2학기 것만)
  - 경영학부 공지 9, With YONSEI 비교과 267, 학교 학사일정 168, 장학금(학생복지처) 31, 공모전 5
  - 소프트웨어학부 공지만 SSL 오류로 실패 (트러블슈팅 2번 참고)
  - 결과 파일 저장에서 권한 오류 (트러블슈팅 1번 참고)
- `docker compose exec web python manage.py import_events /crawler/output`로 DB에 적재
  - `source + external_id`가 같으면 덮어쓰기(upsert)라 여러 번 돌려도 중복 없음
  - 런어스는 사람별 데이터라 이 명령에서는 건너뜀
- 폴더 권한 고친 뒤 다시 실행 → **새로 740건** 적재 (건너뜀 0)
  - 학교 학사일정 168, 경영학부 6, 장학금 28, 공모전 24, 비교과 514
  - 수집 건수와 일정 건수가 다른 이유: 날짜를 못 찾은 공지는 빠지고(경영 9→6, 장학금 31→28), 비교과·공모전은 글 하나에 [신청] 일정과 운영 일정 2개가 나옴(비교과 257→514)
- 소프트웨어학부는 중간 인증서 등록 후 `curl`로 200 OK 확인. 크롤러 재실행 → 소프트웨어학부 4건 수집, 일정 2건 (트러블슈팅 2번)
- 재실행 import 결과: 새로 2 / 갱신 740 / 건너뜀 0 → 이미 있던 740건은 새로 안 생기고 덮어써짐. upsert가 설계대로 동작하는 것 확인
- 최종 DB 일정 742건 (학사 168, 소웨 2, 경영 6, 장학금 28, 공모전 24, 비교과 514)

```txt
합계: 새로 2 / 갱신 740 / 건너뜀 0   (소웨 추가 후 재실행)
```

## D. 비밀키 교체와 API 연결 데모

- Django 비밀키 새로 발급
  - 이유: 작업 로그에 키가 그대로 찍혔음
  - 새 키를 화면에 출력하지 않고 `.env`에 바로 넣음
  - 비밀키(SECRET_KEY): Django가 로그인 세션·서명에 쓰는 값. 새면 다른 사람이 서명을 위조할 수 있음

```bash
sed -i "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')|" .env
docker compose up -d --force-recreate web
grep -c '^DJANGO_SECRET_KEY=.\+' .env    # 1
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/api/health/   # 200
```

- `--force-recreate`: 설정이 바뀌었으니 컨테이너를 새로 만들어서 새 키를 읽게 함
- API 연결 데모 페이지 추가 (`frontend/api-demo.html`, PR #3)
  - 주소: [calendar.ihaewon.com/api-demo.html](https://calendar.ihaewon.com/api-demo.html)
  - 디자인 시안(calendar-a~d)은 프론트 담당 파일이라 건드리지 않고, 별도 페이지로 연결 방법만 보여줌
  - 화면: 종류별 건수 카드(누르면 켜고 끔), 월간 달력(시작일·마감일 구분), 날짜별 상세, 요청·응답 예시
  - 같은 도메인에서 `/api/events/`를 부르기 때문에 CORS 설정이 필요 없음
- 반영: VM에서 `git pull`만 하면 됨 (nginx가 frontend 폴더를 그대로 읽음)

## 트러블슈팅

### 1. 크롤러 결과 저장 실패 (Permission denied)

- 증상 : 크롤링은 끝났는데 저장할 때 `PermissionError: [Errno 13] Permission denied: '.../crawler/output/academic_school.json'`. DB에는 0건
- 확인한 것 : `crawler/output` 폴더가 root 소유
- 원인 : `docker-compose.yml`에서 이 폴더를 web 컨테이너에 연결(bind mount)해두었는데, 폴더가 아직 없는 상태에서 `docker compose up`을 하자 Docker가 root 권한으로 폴더를 만듦. haewonlee 계정은 거기에 파일을 못 씀
  - bind mount: 서버의 폴더를 컨테이너 안에 그대로 보이게 연결하는 것
- 해결 : `sudo chown -R haewonlee:haewonlee crawler/output` 후 크롤러 다시 실행 → 저장 성공, DB에 740건 적재
- 재발 방지 : bind mount할 폴더는 `docker compose up` 전에 내 계정으로 미리 만든다 (`mkdir -p crawler/output`)

### 2. 소프트웨어학부 공지만 SSL 오류

- 증상 : `[소프트웨어학부 공지] ... 실패`, `SSLCertVerificationError: certificate verify failed: unable to get local issuer certificate` (sw.yonsei.ac.kr)
- 확인한 것 : 같은 서버에서 다른 출처 5개(경영학부, With YONSEI, 학사일정, 학생복지처, 대학 공지)는 성공. 팀원 컴퓨터(윈도우)에서는 소웨도 수집됐음
- 원인 : sw.yonsei.ac.kr 서버가 HTTPS 인증서를 보낼 때 중간 인증서를 빠뜨림. 윈도우·맥은 빠진 인증서를 알아서 받아오지만 리눅스 서버는 안 받아와서 신뢰 체인이 끊김
  - 인증서 체인: 사이트 인증서 → 중간 인증서 → 최상위 인증서 순서로 이어지는 신뢰 고리. 가운데가 빠지면 확인 실패
- 해결 : 사이트 인증서에 적힌 주소(AIA)에서 중간 인증서를 받아 서버 신뢰 목록에 등록 (`/usr/local/share/ca-certificates/` → `update-ca-certificates`)
  - 빠진 중간 인증서: Sectigo Public Server Authentication CA DV R36 (`http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt`)
  - DER 형식으로 받아서 PEM으로 변환 후 등록 → `1 added`
  - `curl -sI https://sw.yonsei.ac.kr/notice` → `HTTP/1.1 200 OK` 확인
  - DER / PEM: 인증서를 저장하는 두 형식. DER은 바이너리, PEM은 글자(BEGIN CERTIFICATE)로 된 것. 리눅스 신뢰 목록은 PEM을 씀
  - AIA: 인증서 안에 "내 상위 인증서는 여기서 받으세요"라고 적힌 주소
  - 인증서 확인을 끄는 방법(`verify=False`)은 쓰지 않음. 가짜 사이트에 연결돼도 모르는 보안 구멍이라
- 재발 방지 : 내 컴퓨터에서 되던 크롤러가 서버에서 안 되면 인증서 체인부터 확인한다 (`openssl s_client -connect 도메인:443`)

### 3. 컨테이너를 띄운 직후 curl이 Connection reset

- 증상 : `docker compose up -d` 바로 뒤 `curl localhost:8080/...` → `Recv failure: Connection reset by peer`
- 확인한 것 : `docker compose logs web`에서 migrate·collectstatic이 끝난 뒤에 gunicorn이 켜짐. 몇 초 뒤 다시 치니 `200 OK`
- 원인 : 컨테이너는 "Started"인데 안의 프로그램은 아직 준비 중이었음
- 해결 : 기다렸다가 다시 확인
- 재발 방지 : 배포 직후 확인은 로그에서 `Listening at`을 본 뒤에 한다. 응답 내용까지 보려면 `curl -i`

## 남은 작업

- [x] 소프트웨어학부 공지 SSL 해결 (트러블슈팅 2번)
- [x] 크롤러 다시 돌려 소프트웨어학부 공지 추가 (최종 742건)
- [x] `.env` 비밀키 새로 발급 (작업 로그에 노출됨, D 참고)
- [ ] 크롤러 주기 실행 (cron) 방식 팀원과 결정
