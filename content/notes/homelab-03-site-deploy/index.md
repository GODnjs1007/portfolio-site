---
title: "홈랩 3단계 · 포트폴리오 사이트 컨테이너 배포"
date: 2026-10-01
projects: ["homelab"]
step: 3
summary: "portfolio VM에 웹 서버를 컨테이너로 띄우고, 포트폴리오 사이트를 배포한다."
tags: ["구축", "컨테이너", "트러블슈팅"]
troubleshooting:
  - "hugo --minify 빌드 실패"
  - "ssh-keygen 키 저장 실패"
draft: false
---

## 목표

portfolio VM에 웹 서버를 컨테이너로 띄우고, 포트폴리오 사이트를 배포한다. 먼저 테스트 페이지로 컨테이너 실행과 접속을 확인한 뒤 실제 사이트로 교체한다.

## 진행 과정

## A. Nginx 컨테이너로 테스트 페이지 띄우기

### 목적

- 실제 사이트를 만들기 전에 VM에서 웹 서버 컨테이너가 동작하고 다른 기기에서 접속되는지 먼저 확인

### 1. 테스트 페이지 작성 (portfolio VM)

```bash
mkdir -p ~/site && echo '<h1>Hello from my homelab</h1>' > ~/site/index.html
```

### 2. Nginx 컨테이너 실행

```bash
docker run -d --name site -p 80:80 -v ~/site:/usr/share/nginx/html:ro --restart unless-stopped nginx
```

| 옵션 | 뜻 |
| --- | --- |
| `-d` | 백그라운드 실행 |
| `--name site` | 컨테이너 이름 지정 |
| `-p 80:80` | VM의 80번 포트를 컨테이너 80번 포트에 연결 |
| `-v ~/site:/usr/share/nginx/html:ro` | VM의 `~/site` 폴더를 Nginx 기본 웹 폴더에 연결. `ro`는 읽기 전용 |
| `--restart unless-stopped` | VM이 재부팅돼도 자동으로 다시 실행. 직접 멈춘 경우는 제외 |
| `nginx` | Docker Hub의 공식 Nginx 이미지 |

- 1번 프로젝트 8단계에서는 Dockerfile로 index.html을 넣은 이미지를 만들었음. 이번에는 폴더를 연결해서, 파일만 고치면 이미지를 다시 만들지 않아도 바로 반영됨

### 3. 접속 확인

- 맥북 브라우저에서 `http://<Tailscale IP>` → 테스트 페이지 표시

<!-- 이미지: 2-3A-01 맥북에서 Tailscale 주소로 portfolio VM의 웹 페이지 접속 -->

### 현재 접근 범위

| 접속하는 곳 | 주소 | 가능 여부 |
| --- | --- | --- |
| Tailscale에 로그인한 내 기기 | `<Tailscale IP>` | 가능 |
| 집 와이파이에 연결된 기기 | `<내부 IP>` | 가능 |
| 외부 일반 사용자 | 없음 | 불가 |

- 아무나 접속할 수 있게 하는 것은 4단계(도메인·HTTPS·Reverse Proxy)에서 진행

## B. Hugo 사이트 구성과 GitHub 업로드

### 구조

```plain text
글(.md) → Hugo 변환 → public/ → Nginx 컨테이너 → 브라우저
원본 코드는 GitHub portfolio-site 저장소에 보관
```

### 1. Hugo 설치 (portfolio VM)

```bash
sudo snap install hugo
hugo version
```

- Hugo: 마크다운 글을 디자인·메뉴가 붙은 HTML 사이트로 변환하는 정적 사이트 생성기
- 선택 이유: 노션 글을 마크다운으로 내보내 거의 그대로 옮길 수 있고, 설치가 간단함
- 설치 버전: v0.165.0 extended

### 2. 사이트 생성과 테마

```bash
hugo new site ~/portfolio-site && cd ~/portfolio-site
git init
git submodule add --depth=1 https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod
```

- 테마는 PaperMod. 테마 코드는 내 저장소에 복사하지 않고 submodule로 원본 저장소를 참조함
- 설정 파일 `hugo.toml`: 사이트 제목, 테마, 첫 화면 소개 문구, 메뉴(Projects) 지정

### 3. 첫 글 작성

- `content/posts/proxmox-homelab.md` 생성
- 파일 맨 위 `---` 사이는 글 정보(front matter): title, date, draft, summary
- `draft: false`여야 빌드 결과에 포함됨

### 4. 빌드와 반영

```bash
hugo
docker rm -f site
docker run -d --name site -p 80:80 -v ~/portfolio-site/public:/usr/share/nginx/html:ro --restart unless-stopped nginx
```

- `hugo`: `public/` 폴더에 완성된 사이트 생성
- A에서 띄운 컨테이너를 지우고, Nginx가 `public/`을 보여주도록 다시 실행
- `--minify` 옵션은 빌드 오류가 나서 제외함 (트러블슈팅 1)

<!-- 이미지: 2-3B-01 Hugo + PaperMod로 만든 포트폴리오 사이트 첫 화면 -->

- 이후 글 추가 방법: `content/posts/`에 .md 파일을 넣고 `hugo` 실행. 컨테이너는 다시 띄울 필요 없음

### 5. GitHub 업로드

- 목적: 원본 코드를 VM 밖에 보관. VM이 손상돼도 복구 가능하고, 이후 자동 배포(6단계)의 출발점이 됨
- GitHub에 빈 저장소 `portfolio-site`(Public) 생성. README, .gitignore는 만들지 않음

#### 올리지 않을 파일 지정

```plain text
# .gitignore
public/
resources/_gen/
.hugo_build.lock
```

- `public/`은 `hugo`로 언제든 다시 만들 수 있는 결과물이라 원본만 올림

#### VM에서 GitHub 쓰기 권한 받기 (Deploy key)

```bash
ssh-keygen -t ed25519 -C "portfolio-vm" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

- 출력된 공개키를 저장소 Settings → Deploy keys에 등록, Allow write access 체크
- Deploy key를 쓴 이유: 이 키는 portfolio-site 저장소 하나에만 접근 가능. VM이 뚫려도 다른 저장소는 안전함

```bash
ssh -T git@github.com
```

- `Hi <GitHub 계정>/portfolio-site! You've successfully authenticated` 확인

#### 업로드

```bash
git add .
git commit -m "Hugo 포트폴리오 사이트 초기 구성"
git branch -M main
git remote add origin git@github.com:<GitHub 계정>/portfolio-site.git
git push -u origin main
```

<!-- 이미지: 2-3B-02 GitHub portfolio-site 저장소에 원본 코드 업로드 완료 -->

### 정리: 열쇠 두 개

| 열쇠 | 있는 곳 | 용도 |
| --- | --- | --- |
| 맥북 키 | 맥북 | 맥북 → VM SSH 접속 |
| portfolio-vm 키 | portfolio VM | VM → GitHub portfolio-site 업로드 |

- 저장소 주인 계정으로는 맥북이나 GitHub 웹에서도 수정 가능. Deploy key는 VM에만 준 출입증

## 트러블슈팅

### 1. hugo --minify 빌드 실패

- **증상**

```plain text
ERROR error building site: render: failed to process "/posts/proxmox-homelab/index.html": expected comma character or an array or object ending on line 106 and column 40
```

- **원인**: `--minify`가 테마가 만든 HTML 안의 코드 조각을 해석하다 실패함. Hugo 최신 버전(v0.165)과 테마 사이의 호환 문제로 추정
- **해결**: `--minify` 없이 `hugo`로 빌드. 사이트 동작에는 영향 없음. 용량 최적화는 나중에 다시 확인
- **참고**: `WARN deprecated`는 앞으로 바뀔 설정 이름에 대한 경고라 빌드에는 영향 없음

### 2. ssh-keygen 키 저장 실패

- **증상**

```plain text
Saving key "cat ~/.ssh/id_ed25519.pub" failed: No such file or directory
```

- **원인**: 키 저장 위치를 묻는 질문 칸에 다음 명령어(`cat ...`)까지 같이 붙여넣어져 파일 이름으로 인식됨
- **해결**: 질문이 나오지 않게 옵션을 미리 지정

```bash
ssh-keygen -t ed25519 -C "portfolio-vm" -f ~/.ssh/id_ed25519 -N ""
```

- **재발 방지**: 질문을 던지는 명령어는 한 줄씩 실행. 가능하면 옵션으로 답을 미리 넘김

## 3단계 용어

- **Hugo** : 마크다운 글을 HTML 웹사이트로 바꿔주는 정적 사이트 생성기
- **정적 사이트** : 미리 만들어둔 HTML 파일을 그대로 보여주는 사이트. DB나 서버 코드가 필요 없음
- **마크다운 (.md)** : `#` 제목, `-` 목록처럼 간단한 기호로 서식을 정하는 문서 형식
- **테마** : 사이트의 디자인과 배치를 정해둔 묶음. 여기서는 PaperMod
- **front matter** : 글 파일 맨 위 `---` 사이에 적는 글 정보(제목, 날짜, 요약 등)
- **빌드** : 원본(글, 설정, 테마)을 실제 보여줄 결과물(`public/`)로 만드는 과정
- **bind mount (-v)** : VM의 폴더를 컨테이너 안 폴더에 연결하는 것. VM에서 파일을 바꾸면 컨테이너에도 바로 보임
- **git submodule** : 다른 저장소를 내 저장소 안에 복사하지 않고 참조로 연결하는 방식
- **.gitignore** : GitHub에 올리지 않을 파일 목록
- **commit / push** : commit은 현재 상태를 메모와 함께 저장, push는 그 저장본을 GitHub에 올리는 것
- **remote (origin)** : 내 코드를 올릴 원격 저장소 주소. 기본 이름이 origin
- **Deploy key** : 저장소 하나에만 접근할 수 있는 SSH 키. 서버에 최소 권한만 주기 위해 사용
- **공개키 / 개인키** : 공개키는 상대방에 달아두는 자물쇠, 개인키는 내가 가진 열쇠. 개인키는 밖으로 꺼내지 않음

## 배운 점

### A. Nginx 컨테이너로 테스트 페이지 띄우기

- 실제 사이트 만들기 전 웹 서버 컨테이너가 동작하는 지 확인
  - 웹 서버 : 브라우저가 페이지 요청하면 파일 보내주는 프로그램
    - Nginx : 제일 많이 쓰는 웹 서버
- 테스트 페이지 작성

  ```bash
  mkdir -p ~/site && echo '<h1>Hello from homelab</h1>' > ~/site/index.html
  ```

  - mkdir -p ~/site : home 폴더에 site 폴더 만들기 , -p는 이미 있어도 에러 안 내는 코드
  - \> : 출력한 걸 파일에 저장
- Nginx 컨테이너 실행

  ```bash
  docker run -d --name site -p 80:80 -v ~/site:/usr/share/nginx/html:ro --restart unless-stopped nginx
  ```

  - -d : 백그라운드 실행
  - --name site : 컨테이너 이름 지정
  - -p 80:80 ⇒ vm 80번 포트를 컨테이너 80 포트에 연결
    - 80번은 웹사이트 기본 창구.
    - VM과 컨테이너 연결시켜주는 선이 -p
  - -v \~\~ : VM의 \~\~ 폴더를 Nginx 기본 웹 폴더에 연결.
  - ro  : 읽기 전용
  - --restart unless-stopped : VM이 재부팅되도 자동으로 Nginx 재실행. 직접 멈춘 경우 제외
- 접속 확인
  - `http://<Tailscale IP>`
    - s 없음 : 암호화 안 된 연결 (아직 인증서가 없음)
    - 포트 안 쓴 이유 : 80 기본이라
