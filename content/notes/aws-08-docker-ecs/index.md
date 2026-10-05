---
title: "AWS 8단계 · Docker·ECS"
date: 2026-09-07
projects: ["aws-infra"]
step: 8
summary: "7단계에서 EC2에 직접 설치해 운영하던 웹 서버를 컨테이너 이미지로 만들고, ECS Fargate에서 실행되도록 전환한다."
tags: ["컨테이너", "IaC", "구축", "트러블슈팅"]
troubleshooting:
  - "docker run 이 데몬에 연결하지 못함"
  - "브라우저에서 접속 실패 (ERR_CONNECTION_REFUSED)"
  - "컨테이너 이름 충돌 (Conflict. The container name is already in use)"
draft: false
---

## 목표

7단계에서 EC2에 직접 설치해 운영하던 웹 서버를 컨테이너 이미지로 만들고, ECS Fargate에서 실행되도록 전환한다. VPC·서브넷·보안 그룹은 7단계 구성을 재사용하되, ALB가 서로 다른 AZ의 퍼블릭 서브넷 2개를 요구하므로 퍼블릭 서브넷을 하나 추가한다.

RDS는 이번 단계에서 사용하지 않는다. 배포하는 이미지가 정적 페이지를 제공하는 nginx라 DB를 사용할 이유가 없고, 프라이빗 RDS 접근 제어는 7단계에서 이미 검증했기 때문이다.

## 사전 계획

### 컨테이너는 어디서 왔나

서버를 어떻게 마련하느냐는 계속 바뀌어 왔다. 한 줄로 관통하는 질문은 **"어디까지 아낄 수 있나"**다.

| 단계 | 방식 | 남은 한계 |
| --- | --- | --- |
| ① 온프레미스 | 기업이 서버를 직접 사서 직접 관리 | 장비값 + 관리 인력. 놀고 있어도 돈이 나간다 |
| ② 호스팅 | 업체가 산 컴퓨터를 월 단위로 빌려 씀 | 컴퓨터 1대 = 고객 1명. 자원 낭비가 그대로다 |
| ③ 가상화(VM) | 컴퓨터 1대 안에 가상 컴퓨터 여러 대 | 대수만큼 OS를 올려야 해서 무겁다 |
| ④ 컨테이너 | OS는 1개만 두고 실행 공간만 격리 | 개수가 많아지면 사람이 관리할 수 없다 |
| ⑤ 오케스트레이션 | 컨테이너 수백\~수천 개를 자동으로 배치·감시·재시작 | — |

각 단계가 앞 단계를 없앤 것이 아니라, **아끼는 대상이 장비 → OS → 관리 인력 순으로 옮겨간 것**이다. ③에서 클라우드가 시작됐고, ④를 쉽게 만들어 준 도구가 Docker다.

**8단계는 ④에 서 있다.** 7단계까지 쓴 EC2가 ③(가상 컴퓨터 1대)이고, Docker로 ④를 익힌 뒤 ECS로 ⑤의 입구까지 간다. 쿠버네티스가 ⑤의 대표 도구이고, ECS는 AWS가 만든 같은 자리의 서비스다.

### 바꾸려는 것

7단계까지는 EC2에 SSH로 접속해 필요한 것을 직접 설치해 운영했다. 8단계는 그 서버 자리를 **컨테이너**로 교체한다.

```plain text
7단계   Internet → EC2 (SSH 접속 후 직접 설치) → RDS
8단계   Internet → ALB → ECS Fargate (컨테이너) → RDS
                          └ 한 층만 갈아끼운다
```

VPC·서브넷·보안 그룹·RDS는 7단계 구성을 그대로 사용한다. 새로 배우는 것은 **컨테이너**와 **그것을 AWS에서 돌리는 방법(ECS)** 두 가지다.

### 5단계와 같은 3단 구조

```plain text
5단계   AMI           → Launch Template  → ASG
8단계   Docker 이미지  → Task Definition  → ECS Service
         (무엇으로)      (어떻게 띄울지)     (몇 개 유지할지)
```

이름만 다를 뿐 역할은 같다. 5단계를 이해했다면 8단계의 구조는 새로운 것이 아니다.

### 진행 순서

| 단계 | 내용 | 장소 |
| --- | --- | --- |
| 1 | Docker 기본 동작 익히기 (남의 이미지로 컨테이너 실행) | 로컬(맥북) |
| 2 | Dockerfile로 내 이미지 만들기 | 로컬 |
| 3 | ECR에 이미지 올리기 | AWS |
| 4 | ECS Fargate로 배포 + ALB 연결 | AWS |
| 5 | RDS 연결 확인 및 검증 | AWS |

1–2단계는 AWS를 쓰지 않아 요금이 발생하지 않는다. 3번부터 과금이 시작되므로 실습이 끝나면 반드시 `destroy`한다.

### 예상 비용

| 리소스 | 시간당 약정 요금 | 비고 |
| --- | --- | --- |
| NAT Gateway | $0.059 | 가장 비쌀. 컨테이너가 ECR에서 이미지를 받는 통로 |
| ALB | $0.0225 |  |
| RDS db.t3.micro | $0.026 |  |
| Fargate | $0.012 | 0.25 vCPU / 0.5GB 기준 |

24시간 켜두면 월 12만 원 수준이지만, 실습할 때만 띄우고 `destroy`하면 하루 4시간 기준 700원 수준이다. **켜둔 채 잠드는 것이 가장 큰 위험이다.**

### 사전 준비물

- Docker Desktop 설치 및 실행 확인
- AWS 요금 알림 $5 / $20 / $50 3단계 설정
- 7단계 state 파일 동기화 확인 (구글 드라이브)

## 진행 과정

## A. Docker 기초와 이미지 만들기

### 목표

남이 만든 이미지로 컨테이너를 띄워 Docker의 기본 동작을 익히고, 이어서 내 이미지를 직접 만든다. 여기까지는 전부 로컬(맥북)에서 진행하며 AWS는 쓰지 않는다.

### 1. Docker 데몬 확인

설치만으로는 안 되고 **Docker Desktop(데몬)이 실행 중**이어야 한다.

```bash
docker run -d -p 8080:80 --name test nginx
```

데몬이 꺼져 있으면 아래 에러가 난다.

```plain text
failed to connect to the docker API at unix:///Users/.../docker.sock;
check if the path is correct and if the daemon is running
```

Docker는 **명령어(CLI)와 실제 작업을 하는 데몬이 분리**되어 있다.

```plain text
docker 명령어  →  docker.sock (통로)  →  Docker 데몬 (실제 작업)
```

데몬이 꺼져 있으면 통로 파일 자체가 없으므로 `connection refused`가 아니라 `no such file or directory`가 뜬다. **에러 문구가 원인을 정확히 가리킨다.**

### 2. 첫 컨테이너 실행

```bash
docker run -d -p 8080:80 --name test nginx
```

뒤에서부터 읽는다.

| 조각 | 의미 |
| --- | --- |
| nginx | 무엇으로 만들지 — 이미지 이름 |
| --name test | 만든 컨테이너를 뭐라고 부를지 |
| -p 8080:80 | 밖(8080)에서 안(80)으로 가는 길을 놓는다 |
| -d | 백그라운드 실행. 터미널이 기다리지 않는다 |
| run | 이미지로 컨테이너를 만들어 실행 |

#### 실행 결과

```plain text
Unable to find image 'nginx:latest' locally   로컬에 없음
latest: Pulling from library/nginx            Docker Hub에서 받아옴
a3d95972273c: Pull complete   (× 9줄)         ← 레이어별로 받는다
Status: Downloaded newer image for nginx:latest
76cd5b955cf2...                               생성된 컨테이너 ID
```

<!-- 이미지: 8A-01 nginx 이미지 pull 화면 (터미널) -->

↑ 8A-01 이미지 pull 화면 (터미널)

**줄이 9개인 것이 핵심이다.** 이미지는 한 덩어리가 아니라 레이어(층)가 쌓인 구조이며, 층별로 캐시된다. 두 번째 실행부터는 이 다운로드 과정이 나오지 않는다.

#### -p 포트 매핑

컨테이너는 격리되어 있어 밖에서 바로 접근할 수 없다. `-p`가 그 통로를 만든다.

```plain text
-p 8080 : 80
     ↑      ↑
   내 맥   컨테이너 안
   (자유)  (프로그램이 정한 값)
```

- **왼쪽은 내가 정한다.** 비어 있는 포트면 아무 번호나 가능하다
- **오른쪽은 정할 수 없다.** nginx 이미지가 80번으로 대기하도록 만들어져 있어서 80이다. 바꾸려면 이미지 자체를 새로 만들어야 한다
- 80번 포트를 내가 연 것이 아니라, **원래 열려 있던 80번까지 밖에서 가는 길을 놓은 것**이다

#### -d 가 하는 일

백그라운드는 장소가 아니라 상태다.

|  | 동작 |
| --- | --- |
| -d 없음 | 터미널이 컨테이너에 묶인다. 로그가 계속 출력되고 다른 명령을 못 친다. Ctrl+C를 누르면 컨테이너도 함께 종료된다 |
| -d 있음 | 터미널은 즉시 프롬프트로 돌아오고, 컨테이너는 Docker가 계속 돌린다 |

컨테이너를 돌리는 주체는 어느 쪽이든 Docker이며, 차이는 **터미널이 붙어 있느냐**뿐이다.

### 3. docker ps 읽기

```bash
docker ps
```

```plain text
CONTAINER ID   IMAGE   STATUS         PORTS                  NAMES
76cd5b955cf2   nginx   Up 2 minutes   0.0.0.0:8080->80/tcp   test
```

| 칸 | 읽는 법 |
| --- | --- |
| CONTAINER ID | run 결과로 나온 64자리의 앞 12자리 |
| IMAGE | 어떤 이미지로 만들었나 |
| STATUS | Up = 실행 중 / Exited = 종료됨 |
| PORTS | -p 로 뚫은 길. 0.0.0.0은 내 맥의 모든 주소 |
| COMMAND | 컨테이너가 실행 중인 명령. 이 명령이 끝나면 컨테이너도 종료된다 |

<!-- 이미지: 8A-02 docker ps 출력 화면 -->

↑ 8A-02 docker ps 출력

COMMAND 칸이 중요하다. 컨테이너는 가상 서버가 아니라 **격리된 프로세스 하나**이며, 이것이 EC2와 근본적으로 다른 지점이다.

### 4. 접속 확인

브라우저에서 `localhost:8080` → `Welcome to nginx!`

`localhost`는 내 맥 자신을 가리키는 주소이므로 인터넷을 거치지 않는다.

<!-- 이미지: 8A-03 브라우저에 표시된 Welcome to nginx! 화면 -->

↑ 8A-03 브라우저 Welcome to nginx! 화면

#### 확인한 것

- **Nginx는 내 맥에 설치되지 않았다.** 터미널에서 `nginx -v`를 쳐도 없다고 나온다
- Nginx는 컨테이너 안에만 존재하며, 컨테이너를 지우면 설정도 로그도 흔적이 남지 않는다
- 7단계에서 EC2를 띄우고 SSH로 접속해 설치하는 데 몇 분이 걸렸던 작업이 **명령어 한 줄, 10초**로 끝났다

### 5. 정리

```bash
docker stop test
docker rm test
docker ps -a
```

`stop`은 멈추기만 하고 `rm`이 삭제한다. 컨테이너는 종료되어도 디스크에 남아 있기 때문에 두 명령이 나뉘어 있다. `docker ps -a`는 종료된 컨테이너까지 보여주므로, 아무것도 나오지 않으면 정리가 끝난 것이다.

#### AMI와의 대응

|  | AMI | Docker 이미지 |
| --- | --- | --- |
| 무엇을 만드나 | EC2 인스턴스 | 컨테이너 |
| 내용물 | OS 전체 (커널 포함) | 앱 + 필요한 것만 |
| 크기 | 수 GB | 수십\~수백 MB |
| 시작 시간 | 수십 초 | 1초 이내 |

개념은 같다. 컨테이너는 호스트의 커널을 빌려 쓰기 때문에 OS를 들고 다니지 않아 가볍고 빠르다. 7단계 `ec2.tf`에서 `ami = data.aws_ami...`를 적던 자리가, 여기서는 `nginx`라는 이미지 이름이 들어가는 자리다.

### 6. 작업 폴더와 파일 준비

여기서부터는 남의 이미지가 아니라 **내 이미지**를 만든다.

```bash
mkdir -p ~/docker-practice
cd ~/docker-practice
```

7단계 Terraform 폴더와 분리했다. Terraform은 폴더 단위로 state를 관리하기 때문에 실습 파일이 섞이면 의도치 않은 리소스가 계획에 잡힐 수 있다.

이미지에 넣을 페이지를 만든다.

```bash
cat > index.html <<'EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>이해원</title>
</head>
<body>
  <h1>안녕하세요, 이해원입니다.</h1>
  <p>이 페이지는 제가 직접 만든 Docker 이미지 안에 들어 있습니다.</p>
</body>
</html>
EOF
```

### 7. Dockerfile 작성

**Dockerfile은 "이미지를 이렇게 만들어라"라고 적은 설명서**다. 한 줄이 층 하나가 된다.

```bash
cat > Dockerfile <<'EOF'
FROM nginx:latest
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
EOF
```

파일명은 정확히 `Dockerfile`이어야 한다. 확장자가 없고 D가 대문자다. `docker build`가 이 이름을 찾는다.

| 줄 | 하는 일 |
| --- | --- |
| FROM nginx:latest | 바닥에 깔 이미지. 맨땅이 아니라 이미 nginx가 설치된 이미지 위에 얹는다. 7단계에서 apt install nginx 하던 일을 이 한 줄이 대신한다 |
| COPY index.html ... | 내 맥의 파일을 이미지 안으로 복사한다. 오른쪽 경로는 nginx가 웹페이지를 찾는 기본 자리라, 여기 덮어쓰면 Welcome to nginx 대신 내 페이지가 뜬다. 이 줄이 새 층 하나가 된다 |
| EXPOSE 80 | 실제로 포트를 열지 않는다. "이 이미지는 80번을 쓴다"는 문서용 표시일 뿐이다 |

**EXPOSE는 함정이다.** 실제로 길을 뚫는 것은 `docker run -p 8080:80`의 `-p`다. `EXPOSE`를 지워도 `-p`만 있으면 정상 동작한다. 그럼에도 적어 두는 이유는 이 이미지를 받은 사람이 어떤 포트를 쓰는지 알 수 있고, ECS 같은 곳에서 이 정보를 참고하기 때문이다.

<!-- 이미지: 8A-05 작업 폴더 파일 목록과 Dockerfile 내용 터미널 화면 -->

↑ 8A-05 작업 폴더 파일 목록과 Dockerfile 내용

### 8. 이미지 빌드

```bash
docker build -t myweb:1.0 .
```

| 조각 | 의미 |
| --- | --- |
| -t myweb:1.0 | 이름표. myweb이 이름, 1.0이 태그(버전)다. 이제 nginx처럼 myweb:1.0으로 부를 수 있다 |
| . (점) | 빌드 컨텍스트. 현재 폴더를 통째로 데몬에게 보내라는 뜻이다. 빠뜨리면 에러가 난다 |

점이 필요한 이유는 **CLI와 데몬이 분리되어 있기 때문**이다. 실제 빌드는 데몬이 하므로, 데몬이 `index.html`을 보려면 CLI가 폴더를 넘겨줘야 한다. 그래서 폴더에 불필요한 파일이 많으면 전송량이 늘어 빌드가 느려지고, 이를 걸러내는 것이 `.dockerignore`다.

`latest` 대신 `1.0`을 붙인 이유는 이후 ECR에 올릴 때 버전 구분이 없으면 무엇이 배포됐는지 추적할 수 없기 때문이다.

#### 출력 읽는 법

```plain text
[+] Building 0.2s (7/7) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring context: 302B              ← 점(.)이 보낸 폴더 크기
 => [1/2] FROM docker.io/library/nginx:latest  ← 1층: 다운로드 없음
 => [2/2] COPY index.html /usr/share/nginx/... ← 2층: 내 파일
 => => naming to docker.io/library/myweb:1.0
```

| 볼 곳 | 의미 |
| --- | --- |
| transferring context: 302B | 점(.)이 실제로 보낸 양. index.html 263바이트에 해당한다 |
| FROM 줄에 다운로드가 없음 | 어제 받아 둔 nginx 층을 재사용했다. 처음이었다면 Pull complete 9줄이 다시 나온다 |
| 단계가 1/2, 2/2 두 개뿐 | Dockerfile은 세 줄인데 층은 두 개다. EXPOSE는 층을 만들지 않는다 |
| 0.2초 | 268MB짜리 이미지를 만들었지만 새로 생긴 것은 302바이트뿐이다 |

<!-- 이미지: 8A-06 docker build 출력과 docker images 목록 터미널 화면 -->

↑ 8A-06 docker build 출력과 docker images 목록

### 9. 층이 공유된다는 것을 숫자로 확인

`docker images` 목록에서 `myweb:1.0`과 `nginx:latest`가 각각 268MB, 271MB로 표시된다. 그러나 두 배를 쓰는 것이 아니다.

```bash
docker system df
```

```plain text
TYPE     TOTAL   ACTIVE   SIZE      RECLAIMABLE
Images   3       1        9.556GB   205.9MB (2%)
```

| 계산 | 값 |
| --- | --- |
| 개별 크기 단순 합계 (268 + 271 + 9280) | 약 9,819MB |
| 실제 디스크 사용량 | 9,556MB |
| 차이 | 약 263MB — nginx 이미지 하나 크기 |

`myweb`은 `nginx` 위에 얹혀 있으므로 아래 층은 한 벌만 저장된다. **층 공유가 숫자로 확인된 지점이다.**

<!-- 이미지: 8A-07 docker system df 출력 화면 -->

↑ 8A-07 docker system df 출력

### 10. 내 이미지로 컨테이너 실행

```bash
docker run -d -p 8080:80 --name myweb-test myweb:1.0
docker ps
```

첫 컨테이너를 띄울 때와 **명령의 마지막 한 조각만 다르다.**

```plain text
2번   docker run -d -p 8080:80 --name test       nginx
10번  docker run -d -p 8080:80 --name myweb-test myweb:1.0
                                                 └ 남의 틀 → 내 틀
```

`docker ps`의 `IMAGE` 칸이 `myweb:1.0`으로 나오면 성공이다.

<!-- 이미지: 8A-08 docker ps 화면 — IMAGE 칸이 myweb:1.0 -->

↑ 8A-08 docker ps — IMAGE 칸이 myweb:1.0

브라우저에서 `localhost:8080`에 접속하면 `Welcome to nginx!`가 아니라 직접 작성한 페이지가 표시된다.

<!-- 이미지: 8A-08b 브라우저에 표시된 직접 만든 페이지 -->

↑ 8A-08b 브라우저에 표시된 내 페이지

#### 확인한 것

- **파일을 서버에 올린 것이 아니다.** 파일은 이미 이미지 안에 들어 있었고, 컨테이너는 그 이미지를 실행했을 뿐이다
- 7단계에서는 EC2 생성 → SSH 접속 → 파일 업로드 → nginx 재시작 순서가 필요했다. 여기서는 명령 한 줄이다
- 같은 이미지로 컨테이너를 몇 개를 만들어도 내용이 동일하다. 손으로 고친 내용이 특정 서버에만 남는 문제가 구조적으로 발생하지 않는다

### 11. 정리

```bash
docker ps
docker rm -f myweb-test
```

`rm -f`는 실행 중인 컨테이너도 강제로 삭제한다. `stop` 후 `rm`을 따로 하는 것과 결과가 같다.

로컬 실습이라 비용은 발생하지 않지만, **실습이 끝나면 그 자리에서 정리하는 습관**이 필요하다. 이번 실습에서 이틀 전 컨테이너가 그대로 실행 중이었고, 그것이 8080 포트를 점유해 다음 실행을 막았다. 같은 상황이 AWS였다면 이틀치 요금이 발생했을 것이다.

## B. ECR 이미지 푸시

### 목표

로컬(맥북)에만 있던 `myweb:1.0` 이미지를 AWS ECR에 올려, ECS가 가져다 쓸 수 있는 상태로 만든다.

### 1. ECR이 필요한 이유

A에서 만든 이미지는 내 맥북의 Docker 안에만 있다. ECS는 다른 곳에서 실행되므로 이 이미지를 볼 수 없다. 컨테이너를 클라우드에서 실행하려면 이미지가 **AWS가 접근할 수 있는 저장소**에 있어야 하고, 그 역할을 하는 것이 ECR이다.

Docker Hub도 같은 역할을 하지만 ECR을 쓰는 이유는 두 가지다.

- 같은 리전 안에 있어 이미지를 당겨오는 속도가 빠르고 외부 전송 비용이 없다
- IAM으로 접근 권한을 통제한다. 별도 계정 없이 기존 AWS 자격 증명을 그대로 쓴다

### 2. 리포지토리 생성

```bash
aws ecr create-repository --repository-name myweb --region ap-northeast-2
```

결과의 `repositoryUri`가 앞으로 쓸 주소다.

```plain text
<계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb
```

리포지토리는 이미지 한 종류를 담는 칸이고, 그 안에 태그(`1.0`, `1.1` …)로 버전을 쌓는다. 다른 애플리케이션이면 리포지토리를 따로 만든다.

### 3. 인증

```bash
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com
```

```plain text
Login Succeeded
```

ECR은 인증 없이는 push할 수 없다. `get-login-password`가 12시간짜리 임시 토큰을 발급하고, 파이프로 `docker login`에 그대로 넘긴다.

**파이프를 쓰는 것이 핵심이다.** 토큰을 화면에 출력해 복사·붙여넣기 하면 터미널 화면과 셸 히스토리에 그 값이 남는다. `--password-stdin`은 표준 입력으로 받아 그 노출을 없앤다.

사용자 이름이 `AWS`로 고정인 것은 ECR이 정해둔 값이다.

### 4. 태그 지정

```bash
docker tag myweb:1.0 <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb:1.0
docker images | grep myweb
```

두 줄이 나오고 **IMAGE ID가 서로 같다.**

`docker tag`는 이미지를 복사하지 않는다. 같은 이미지에 이름을 하나 더 붙일 뿐이라 디스크 사용량이 늘지 않는다.

이 긴 이름이 필요한 이유는 `docker push`가 **이름의 앞부분을 보고 목적지를 정하기 때문**이다. `myweb:1.0`을 그대로 push하면 Docker Hub로 향한다. 레지스트리 주소가 이름에 포함되어 있어야 ECR로 간다.

### 5. 푸시

```bash
docker push <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb:1.0
```

```plain text
The push refers to repository [<계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb]
7cb6e1b14b86: Pushed
bf7af0229701: Pushing [==========>        ]  6.291MB/30.16MB
bf7af0229701: Pushed
...
1.0: digest: sha256:84ec21a889513b50da25f0f4aa9705e3a873d83aecdcb1a1f865b421f94fbd7d  size: 856
```

한 덩어리가 아니라 **레이어 단위로 올라간다.** A에서 확인한 이미지의 층 구조가 전송에서도 그대로 유지되는 것이다. 이미 같은 층이 ECR에 있으면 `Layer already exists`로 건너뛴다.

마지막 `digest` 줄이 성공 표시다.

<!-- 이미지: 8B-01 ECR 콘솔 — myweb 리포지토리에 1.0 태그 이미지가 올라간 상태 -->

↑ 8B-01 ECR 콘솔 — myweb 리포지토리에 1.0 태그 이미지가 올라간 상태

### 비용

ECR은 저장 용량 기준으로 과금되며 프리티어는 월 500MB다. 이번 이미지는 그 안에 들어가므로 사실상 비용이 발생하지 않는다.

이 단계까지는 NAT Gateway·ALB·Fargate 같은 **시간당 과금 리소스가 하나도 없다.** 실행 중인 리소스가 없으므로 여기서 중단해도 요금이 쌓이지 않는다.

## C. ECS Fargate 배포와 장애 주입 테스트

### 목표

B에서 ECR에 올린 `myweb:1.0`을 ECS Fargate로 실행하고, ALB를 통해 인터넷에서 접속되는 구조를 Terraform으로 만든다. 7단계 VPC 코드를 재사용하되 ALB 요구사항에 맞춰 확장한다.

### 1. 5단계 구조와의 대응

새로 배우는 개념처럼 보이지만 **5단계 ALB·Auto Scaling 구성과 1:1로 대응된다.**

| 5단계 | 8단계 | 역할 |
| --- | --- | --- |
| AMI | ECR 이미지 | 무엇을 띄울지 |
| Launch Template | 태스크 정의 | 어떤 스펙으로 띄울지 |
| Auto Scaling Group | ECS 서비스 | 몇 개를 유지할지 |
| EC2 인스턴스 | 태스크(컨테이너) | 실제로 돌아가는 것 |
| 타겟 그룹 → 인스턴스 ID | 타겟 그룹 → 컨테이너 IP | ALB가 무엇을 등록하는가 |

가장 큰 차이는 **서버가 없다는 것**이다. 5단계에서는 EC2가 실제로 존재해 SSH로 들어갈 수 있었고 OS 패치도 내 책임이었다. Fargate는 접속할 서버 자체가 없고 "CPU 0.25개, 메모리 0.5GB만큼" 쓴 만큼만 비용을 낸다. `ecs.tf`에 EC2 관련 코드가 한 줄도 없는 것이 그 뜻이다.

### 2. 구성

```plain text
인터넷
  ↓ :80
ALB            ← 퍼블릭 서브넷 2개(다른 AZ)
  ↓
타겟 그룹     ← target_type = "ip"
  ↓
ECS 서비스    ← desired_count = 2
  ↓
태스크 ×2     ← ECR의 myweb:1.0 을 받아 실행
```

### 3. 7단계 코드에서 바꿈 — 퍼블릭 서브넷 추가

7단계 `network.tf`에는 퍼블릭 서브넷이 `10.0.1.0/24` 하나뿐이었다. 그러나 **ALB는 서로 다른 AZ의 퍼블릭 서브넷 2개를 요구한다.** 5단계에서 AZ를 2개 썼던 것과 같은 이유다.

```hcl
# 퍼블릭 서브넷 B (ALB용, 다른 AZ)
resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true
}

# 기존 퍼블릭 라우팅 테이블 연결
resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}
```

라우팅 테이블은 새로 만들지 않고 **7단계에서 만든 퍼블릭 라우팅 테이블을 그대로 연결했다.** 둘 다 "0.0.0.0/0 → IGW"로 나가면 되므로 표를 중복해 만들 이유가 없다.

`rds.tf`와 `ec2.tf`는 이번 단계에서 쓰지 않으므로 파일명을 `.bak`로 바꿔 계획에서 제외했다. RDS는 생성에 10분이 걸리고 시간당 비용이 발생하는데, 8단계의 목표인 컨테이너 배포와는 직접 관계가 없다.

### 4. ALB와 보안 그룹

보안 그룹을 두 개로 나누어, 컨테이너가 인터넷에서 직접 접근되지 않도록 했다.

```hcl
# ALB 보안그룹 — 인터넷에서 80 허용
resource "aws_security_group" "alb" {
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ...
}

# ECS 태스크 보안그룹 — ALB에서 오는 것만 허용
resource "aws_security_group" "ecs_task" {
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  ...
}
```

`cidr_blocks` 대신 `security_groups`를 쓴 것이 핵심이다. **7단계에서 RDS가 EC2 보안 그룹만 허용했던 것과 같은 패턴**이며, 컨테이너 IP가 수시로 바뀌어도 규칙을 고칠 필요가 없다.

```hcl
resource "aws_lb_target_group" "main" {
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"      # ← Fargate는 반드시 ip

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    matcher             = "200"
  }
}
```

**`target_type = "ip"`가 5단계와 가장 크게 달라진 지점이다.** 5단계에서는 EC2 인스턴스 ID를 타겟으로 등록했지만, Fargate는 EC2 자체가 없으므로 등록할 인스턴스가 없다. 기본값인 `instance`로 두면 apply에서 오류가 난다.

### 5. ECS 구성

#### 실행 역할(IAM)

```hcl
resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
```

컨테이너를 띄우려면 **ECR에서 이미지를 당겨오고 CloudWatch에 로그를 쓸 권한**이 필요하다. 내 계정 권한이 아니라 **ECS가 대신 쓸 권한**이므로, 신뢰 주체를 `ecs-tasks.amazonaws.com`으로 지정한다.

#### 태스크 정의

```hcl
resource "aws_ecs_task_definition" "myweb" {
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"    # ← M4 맥에서 빌드한 이미지
  }

  container_definitions = jsonencode([{
    name  = "myweb"
    image = "<계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb:1.0"
    portMappings = [{ containerPort = 80, protocol = "tcp" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/tf-step8-myweb"
        "awslogs-region"        = "ap-northeast-2"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}
```

**`runtime_platform`을 ARM64로 지정한 것이 중요하다.** 작업 환경이 Apple Silicon(M4) 맥이라 `docker build`가 ARM64 이미지를 만들었는데, Fargate 기본값은 x86_64다. 불일치하면 컨테이너가 시작 직후 `exec format error`로 죽는다. 실습 전에 `uname -m`으로 아키텍처를 확인해 이 오류를 사전에 피했다.

#### 서비스

```hcl
resource "aws_ecs_service" "myweb" {
  desired_count = 2
  launch_type   = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.ecs_task.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "myweb"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]
}
```

**태스크 정의와 서비스의 관계는 이미지와 컨테이너의 관계와 같다.** 태스크 정의는 설계도일 뿐 실행하지 않고, 서비스가 그 설계도로 2개를 띄우고 개수를 유지한다.

#### assign_public_ip 선택

컨테이너가 ECR에서 이미지를 받으려면 밖으로 나가는 경로가 필요하다. 선택지는 둘이었다.

| 방식 | 비용 | 비고 |
| --- | --- | --- |
| 프라이빗 서브넷 + NAT Gateway | 시간당 $0.059 + 데이터 요금 | 정석 구성 |
| 퍼블릭 서브넷 + 퍼블릭 IP | 0 | 보안그룹으로 직접 접근 차단 |

실습 목적이고 컨테이너가 ALB를 통해서만 접근되도록 보안 그룹을 구성했으므로 **두 번째를 선택해 시간당 과금 리소스 하나를 없앱다.** 실제 운영 환경이라면 프라이빗 서브티 + NAT이 정석이다.

### 6. 배포

```bash
terraform init && terraform plan
```

```plain text
Plan: 22 to add, 0 to change, 0 to destroy.
```

```bash
terraform apply
```

```plain text
aws_lb.main: Creation complete after 2m21s
aws_lb_listener.http: Creation complete after 1s
aws_ecs_service.myweb: Creation complete after 1s

Apply complete! Resources: 22 added, 0 changed, 0 destroyed.

Outputs:
alb_dns = "<ALB DNS>"
```

**ALB 생성에만 2분21초가 걸렸다.** 나머지 리소스는 수 초 안에 끝난다.

apply 직후 접속하면 `503 Service Temporarily Unavailable`가 나올 수 있다. 컨테이너가 ECR에서 이미지를 받고 nginx가 뜨고 ALB 헬스체크를 2회 통과해야 타겟 그룹에 등록되기 때문이며, 1～3분이 걸린다.

### 7. 검증

#### 서비스가 희망 개수를 유지하는가

ECS 콘솔에서 태스크 2개가 실행 중이고 서비스가 `2/2`로 표시된다.

<!-- 이미지: 8C-01 ECS 콘솔 — 태스크 2개 실행 중 -->

↑ 8C-01 ECS 태스크 2개 실행 중

<!-- 이미지: 8C-02 ECS 서비스 목록 — 2/2 태스크 -->

↑ 8C-02 ECS 서비스 목록 — 2/2 태스크

#### 외부에서 접속되는가

`alb_dns` 주소로 접속하면 A에서 이미지 안에 넣었던 페이지가 그대로 표시된다. 파일을 서버에 올린 적이 없고, **로컬에서 만든 이미지가 ECR을 거쳐 AWS에서 그대로 실행된 것이다.**

<!-- 이미지: 8C-03 ALB 주소로 접속해 직접 만든 페이지가 표시된 브라우저 화면 -->

↑ 8C-03 ALB 주소로 접속 성공

#### ALB가 컨테이너를 정상으로 잡고 있는가

서비스 상태 화면의 로드 밸런서 대상 상태가 **2 정상 / 0 비정상**으로 표시된다. 타겟 그룹에 등록된 것은 EC2 인스턴스가 아니라 컨테이너의 프라이빗 IP다.

<!-- 이미지: 8C-04 로드 밸런서 대상 상태 — 2 정상 / 0 비정상 -->

↑ 8C-04 로드 밸런서 대상 상태 — 2 정상 / 0 비정상

### 8. 장애 주입 테스트

구현만으로는 "서비스가 개수를 유지한다"는 것이 코드상의 설정일 뿐이므로, **의도적으로 태스크 하나를 중지시켜 자동 복구 동작을 검증했다.**

ECS 콘솔 → 태스크 탭 → 실행 중인 태스크 하나 선택 → 중지

<!-- 이미지: 8C-05 ECS 콘솔에서 태스크를 중지한 직후 화면 -->

↑ 8C-05 태스크 중지 직후

바로 다음 상태가 이번 단계의 핵심 검증 화면이다.

```plain text
70070cf8...   실행 중       ← 원래 있던 태스크
77a4905b...   활성화 중     ← ECS가 자동으로 띄운 새 태스크
372d2486...   비활성화 중   ← 의도적으로 중지시킨 태스크
```

<!-- 이미지: 8C-06 태스크 자동 교체 — 중지된 태스크와 새 태스크가 동시에 보이는 화면 -->

↑ 8C-06 태스크 자동 교체 — 죽은 태스크와 새 태스크가 동시에 존재

#### 확인한 것

- 아무것도 지시하지 않았는데 **ECS 서비스가 스스로 새 태스크를 띄워 다시 2개를 만들었다.** 5단계 Auto Scaling Group이 하던 역할을 서비스가 대신한다
- 죽은 태스크가 완전히 사라지기 전에 새 태스크가 먼저 올라왔다. **실행 개수가 0으로 떨어지는 구간이 없다**
- 태스크 ID가 바뀌었음에도 ALB 주소는 그대로였다. **컨테이너 IP가 바뀌어도 사용자는 알 필요가 없다**는 것이 ALB를 두는 이유다

> 이 장애는 실제로 발생한 것이 아니라 동작 검증을 위해 의도적으로 주입한 테스트다.

### 9. 비용

| 리소스 | 과금 |
| --- | --- |
| ALB | 시간당 약 $0.027 |
| Fargate (0.25 vCPU / 0.5GB × 2) | 시간당 약 $0.02 |
| NAT Gateway | 사용하지 않음 |

시간당 과금 리소스가 있으므로 실습을 여러 날에 나누지 않고 **한 번에 구축·검증·삭제까지 끝내는 방식으로 진행했다.** 실제 소요 시간은 약 1시간이었다.

삭제 기록은 9단계 문서에 함께 남겼다. 8단계와 9단계가 같은 인프라를 공유하기 때문이다.

## 트러블슈팅

8단계에서 실제로 만난 문제와 해결 과정. **증상 / 확인한 것 / 원인 / 해결 / 재발 방지** 순서로 기록한다.

### 1. docker run 이 데몬에 연결하지 못함

#### 증상

```plain text
failed to connect to the docker API at unix:///Users/<사용자>/.docker/run/docker.sock;
check if the path is correct and if the daemon is running:
dial unix /Users/<사용자>/.docker/run/docker.sock: connect: no such file or directory
```

#### 확인한 것

- `docker` 명령어 자체는 실행됐다 → CLI는 설치되어 있다
- 에러가 `connection refused`가 아니라 **`no such file or directory`**다 → 연결을 거부당한 것이 아니라 **연결할 대상 파일 자체가 없다**

#### 원인

Docker Desktop(데몬)이 실행되지 않은 상태였다. Docker는 명령어(CLI)와 실제 작업을 수행하는 데몬이 분리되어 있고, 둘은 `docker.sock`이라는 소켓 파일로 통신한다. 데몬이 꺼져 있으면 이 파일이 생성되지 않는다.

```plain text
docker 명령어  →  docker.sock  →  Docker 데몬
                  (없음)
```

<!-- 이미지: 8A-00 docker.sock 연결 실패 에러가 출력된 터미널 화면 -->

↑ 8A-00 docker.sock 에러 터미널 화면

#### 해결

Docker Desktop을 실행하고 메뉴바 아이콘이 running 상태가 된 뒤 명령을 재실행했다.

#### 재발 방지

작업 시작 전 `docker ps`로 데몬 상태를 먼저 확인한다. 정상이면 목록이(비어 있더라도) 출력되고, 꺼져 있으면 같은 에러가 난다.

#### 배운 점

에러 문구가 원인을 좁혀 준다. `refused`였다면 데몬은 떠 있는데 권한 등 다른 문제였을 것이고, `no such file`이므로 데몬 자체가 없다는 뜻이다. 3단계에서 본 `Connection refused` / `timed out` 구분과 같은 방식의 진단이다.

### 2. 브라우저에서 접속 실패 (ERR_CONNECTION_REFUSED)

#### 증상

브라우저에서 `사이트에 연결할 수 없음 / localhost에서 연결을 거부했습니다 / ERR_CONNECTION_REFUSED`

<!-- 이미지: 8A-04 주소창에 localhost:8000을 입력해 ERR_CONNECTION_REFUSED가 뜬 브라우저 화면 -->

↑ 8A-04 브라우저 ERR_CONNECTION_REFUSED 화면 (주소창에 localhost:8000)

#### 확인한 것

- `docker ps` 결과 `STATUS`가 `Up`이었다 → 컨테이너는 정상 실행 중
- `PORTS`가 `0.0.0.0:8080->80/tcp`였다 → 열려 있는 포트는 **8080**
- 브라우저 주소창은 `localhost:8000`이었다 → **요청한 포트가 다르다**

#### 원인

주소창에 포트를 `8080`이 아닌 `8000`으로 잘못 입력했다. 8000번에는 대기 중인 프로세스가 없으므로 운영체제가 즉시 연결을 거절했다.

#### 해결

`localhost:8080`으로 접속하여 `Welcome to nginx!` 확인.

#### 재발 방지

접속이 안 될 때는 주소를 의심하기 전에 `docker ps`의 `PORTS` 칸을 먼저 본다. 실제로 열려 있는 포트가 거기에 그대로 적혀 있다.

#### 배운 점

`timed out`이 아니라 `refused`가 난 것이 단서였다. 내 컴퓨터(localhost)까지는 도달했고, 그 포트에 아무도 없어서 거절당한 것이다. 도달조차 못 했다면 시간 초과가 났을 것이다.

또한 이것은 5단계에서 미해결로 남겨 두었던 **502 에러의 원인 중 하나(포트 불일치)**와 같은 종류의 문제다. ALB가 80으로 보내는데 컨테이너가 다른 포트로 열려 있으면 같은 이유로 실패한다.

### 3. 컨테이너 이름 충돌 (Conflict. The container name is already in use)

#### 증상

내 이미지로 컨테이너를 띄우려 하자 실행되지 않았다.

```plain text
docker: Error response from daemon: Conflict.
The container name "/myweb-test" is already in use by container
"288fd2dfb900f733ed7df33197134f866ca822d7a39169c891cb9b17d4940d2e".
You have to remove (or rename) that container to be able to reuse that name.
```

<!-- 이미지: 8A-09 이름 충돌로 실패한 docker run 터미널 화면 -->

↑ 8A-09 포트 점유로 실패한 docker run

#### 확인한 것

- `docker ps` 결과가 **비어 있었다** → 실행 중인 컨테이너는 없다
- 그런데 에러는 그 이름이 **이미 쓰이고 있다**고 한다 → 실행 중이 아닌 컨테이너가 존재한다
- `docker ps -a` 로 확인하니 `myweb-test`가 있었다

<!-- 이미지: 8A-10 test 컨테이너가 8080 포트를 점유 중인 docker ps 화면 -->

↑ 8A-10 test 컨테이너가 8080을 점유 중인 docker ps

#### 원인

직전에 이전 실습의 컨테이너(`test`)가 8080 포트를 점유한 상태에서 `docker run`을 실행했다. Docker는 **컨테이너를 먼저 만들고 그다음 시작**하기 때문에, 포트 충돌로 시작에 실패해도 **생성된 컨테이너는 그대로 남는다.** 그 껍데기가 이름을 계속 붙들고 있었다.

```plain text
docker run  →  ① 컨테이너 생성   (성공, 이름 점유)
               ② 컨테이너 시작   (실패, 포트 충돌)
                                  → 이름만 남은 컨테이너가 잔류
```

#### 해결

```bash
docker ps -a          # 꺼진 컨테이너까지 확인
docker rm myweb-test  # 남아 있던 컨테이너 삭제
docker run -d -p 8080:80 --name myweb-test myweb:1.0
```

#### 재발 방지

- 실습이 끝나면 그 자리에서 `docker rm`까지 한다. `stop`만으로는 이름과 디스크가 정리되지 않는다
- 이름 충돌 에러가 나면 **무조건 `docker ps -a`부터** 본다

#### 배운 점

`docker ps`는 실행 중인 것만 보여 준다. 화면에 안 보인다고 없는 것이 아니다. 컨테이너는 종료되어도 디스크에 남고 이름도 계속 점유한다는 것이 이 에러로 눈에 보였다.

또한 **에러 문구를 정확히 읽는 것이 진단의 시작**이라는 점이 다시 확인됐다. 포트 문제라고 넘겨짚었지만 문구는 `name ... already in use`, 즉 **이름 문제**였다. 같은 명령이 포트 때문에 실패할 때는 `port is already allocated`로 전혀 다르게 나온다.

## 8단계 용어

8단계에서 새로 나온 개념과 명령어. **진행 순서대로** 정리했다.

### 핵심 개념

| 용어 | 한 줄 설명 |
| --- | --- |
| 컨테이너(Container) | 프로그램과 그것이 돌아가는 데 필요한 것을 함께 담아 격리해 실행한 것. 가상 서버가 아니라 격리된 프로세스 하나다 |
| 이미지(Image) | 컨테이너를 만들기 위한 템플릿. 실행되지 않는 파일이며, 이미지 하나로 컨테이너를 여러 개 만들 수 있다 |
| 레이어(Layer) | 이미지를 이루는 층. 층 단위로 캐시되어, 겹치는 층은 다시 받지 않는다 |
| Docker Hub | 공개 이미지 저장소. 이미지 이름만 적으면 여기서 받아온다 |
| Docker 데몬 | 실제로 컨테이너를 만들고 돌리는 프로그램. 명령어(CLI)와 분리되어 있다 |
| docker.sock | CLI가 데몬에 요청을 전달하는 통로 파일. 데몬이 꺼져 있으면 이 파일 자체가 없다 |
| 격리(Isolation) | 컨테이너 안은 밖과 분리되어 있어, 포트를 연결해 주지 않으면 접근할 수 없다 |

### 명령어

| 명령어 | 한 줄 설명 |
| --- | --- |
| docker run | 이미지로 컨테이너를 만들어 실행한다. 로컬에 이미지가 없으면 자동으로 받아온다 |
| docker ps | 실행 중인 컨테이너 목록 |
| docker ps -a | 종료된 컨테이너까지 포함한 전체 목록 |
| docker stop | 컨테이너를 멈춘다. 삭제되지는 않는다 |
| docker rm | 멈춘 컨테이너를 삭제한다 |

### 옵션

| 옵션 | 한 줄 설명 |
| --- | --- |
| -p 8080:80 | 포트 매핑. **왼쪽이 호스트, 오른쪽이 컨테이너**다. 왼쪽은 내가 정하고, 오른쪽은 컨테이너 안 프로그램이 대기 중인 포트라 임의로 바꿀 수 없다 |
| -d (detached) | 백그라운드 실행. 터미널이 컨테이너를 기다리지 않고 바로 다음 명령을 받는다. 없으면 터미널이 묶이고 Ctrl+C 시 컨테이너도 종료된다 |
| --name | 컨테이너에 이름을 붙인다. 이후 ID 대신 이 이름으로 다룰 수 있다 |

### 출력 읽기

| 항목 | 한 줄 설명 |
| --- | --- |
| CONTAINER ID | 컨테이너 고유 번호. 표시되는 것은 앞 12자리다 |
| STATUS | Up = 실행 중 / Exited = 종료됨 |
| COMMAND | 컨테이너가 실행 중인 명령. 이 명령이 끝나면 컨테이너도 종료된다 |
| 0.0.0.0 | 호스트의 모든 네트워크 주소를 뜻한다 |
| localhost | 내 컴퓨터 자신을 가리키는 주소. 인터넷을 거치지 않는다 |

### 컨테이너 이전의 서버

컨테이너가 왜 나왔는지를 이해하려면 앞 단계들의 이름을 알아야 한다.

| 용어 | 한 줄 설명 |
| --- | --- |
| 온프레미스(On-premise) | 서버를 빌리지 않고 회사가 직접 사서 직접 관리하는 방식. 장비값과 관리 인력이 모두 자기 몫이다 |
| 호스팅 | 업체가 소유한 서버를 월 단위로 빌려 쓰는 방식. 컴퓨터 1대를 고객 1명이 쓴다 |
| 가상화(Virtualization) | 물리 컴퓨터 1대를 쪼개 여러 대처럼 쓰는 기술. 여기서 클라우드가 시작됐다 |
| VM(가상 머신) | 가상화로 만들어진 컴퓨터 한 대. OS가 통째로 올라간다. EC2가 여기에 해당한다 |
| 하이퍼바이저 | 물리 자원을 나눠 VM들에게 배분하는 소프트웨어 |
| 오케스트레이션 | 컨테이너를 여러 서버에 걸쳐 배치·감시·재시작해 주는 것. 죽으면 자동으로 새로 띄운다 |
| 쿠버네티스(K8s) | 오케스트레이션의 대표 도구. ECS는 AWS가 만든 같은 자리의 서비스다 |
| EC2 vs ECS | EC2는 가상 컴퓨터를 빌려주는 서비스, ECS는 컨테이너를 돌려주는 서비스. 이름이 비슷하지만 다루는 층이 다르다 |

### 웹 서비스의 3대 요소

| 구성 | 역할 |
| --- | --- |
| 웹 서버 | 바뀌지 않는 것(HTML·이미지·CSS)을 그대로 내려준다. Nginx가 여기다 |
| WAS | 사람마다 다른 결과를 계산해서 내려준다. 로그인 후 화면처럼 매번 달라지는 부분 |
| DB | 데이터를 보관한다. 7단계에서 만든 RDS |

지금 컨테이너에 띄운 nginx는 셋 중 **웹 서버**다. 뒤에 WAS와 DB가 붙으면 3단 구성이 완성되고, 8단계의 최종 목표인 `ALB → ECS → RDS`가 정확히 그 모양이다.

### 이전 단계와의 연결

| 연결 | 내용 |
| --- | --- |
| AMI ↔ Docker 이미지 | 둘 다 실행 단위를 찍어내는 템플릿. AMI는 OS 전체(수 GB, 수십 초), 이미지는 앱과 필요한 것만(수백 MB, 1초 이내) |
| 5단계 ↔ 8단계 구조 | AMI → Launch Template → ASG 가 Docker 이미지 → Task Definition → ECS Service 와 같은 3단 구조다 |
| 포트 불일치 ↔ 502 | 5단계에서 본 502의 원인 중 하나가 포트 불일치다. 컨테이너에서도 -p 오른쪽 값이 틀리면 같은 증상이 난다 |
| 불변 인프라 | 5단계에서 서버에 손으로 고친 내용이 새 서버에 없던 문제. 컨테이너는 변경을 이미지에 넣기 때문에 이 문제가 구조적으로 사라진다 |

## 배운 점

### A. Docker 기초와 이미지 만들기

- 방식의 변화
    - 지금까지의 방식
        - 가상컴퓨터 → 프로그램 설치 → 실행 (VM—> OS 전체)
            1. 느리다
            2. 무겁다
            3. 손으로 고치면 거기에만 있음.
    - 새로운 방식
        - 컨테이너 : 프로그램과 프로그램이 돌아가는 데 필요한 것들을 통째로 한 덩어리로 묶어 그대로 실행
            - VM은 OS를 들고다니고, 컨테이너는 호스트의 OS를 빌려 씀
            - 컨테이너 안에서 고친 건 컨테이너를 지우면 사라짐
                - 고칠 게 있으면 컨테이너가 아니라 이미지를 새로 만들어야 함

```bash
docker run -d -p 8080:80 --name test nginx
```

- 컨테이너와 계층구조
    - docker : 도구 (만들고, 받아오고, 실행시켜주는 프로그램)
    - 이미지 : 파일 (층으로 쌓인 덩어리, 안 변함)
        - nginx : 틀 이름
    - 컨테이너 : 실행 상태 (이미지를 돌린 것, 프로세스 하나)
        - 지금 까지 EC2는 가상컴퓨터 한 대였다면, 컨테이너는 프로세스 (실행중인 프로그램 하나)
- run -d -p 8080:80
    - 8080 : 내 맥 —> 맘대로 설정 가능
    - 80 : 컨테이너 —> 컨테이너 안 80번의 nginx가 응답
    - -p : 내 맥에서 컨테이너로 들어갈 수 있게 해주는 역할
    - run : 이미지로 컨테이너를 만들어 실행
    - -d : 백그라운드에서 실행
        - 백그라운드 : 상태  (터미널이 묶이냐 안 묶이냐의 상태) / 컨테이너를 돌리는 건 docker

### B . ECR 이미지 푸시

- A에서 만든 이미지는 내 Docker 안에서만 존재 —> ECR가 필요한 이유
    - ECR : 이미지를 올려둔 AWS 창고
    - ECS : 창고에서 이미지를 꺼내서 실제로 돌려주는 곳
        - 다른 곳에서 실행되기 때문에 이미지를 볼 수 없었다. 그래서 ECR이 필요

```bash
aws ecr create-repository --repository-name myweb --region ap-northeast-2
```

- 리포지토리
    - 이미지 한 종류를 담는 칸
    - 다른 애플리케이션이면 다른 리포지토리 필요

```bash
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com
```

- 인증
    - ECR은 인증없이 push 할 수 없다.
    - get-login-password
        - 12시간짜리 임시 토큰 발급 —> 파이프로 docker login에 넘김
            - 기존 aws ecr get-login-password --region ap-northeast-2 으로 로그인하게 되면 화면에 비밀번호가 뜬다.
                - docker login -u AWS -p \<토큰\> 으로 로그인하면 히스토리에 남음
            - 이 코드를 사용하면 화면을 비밀번호랑 입력하는 칸이 뜨지않고 바로 프로그램으로 넘어간다.
        - 사용자 이름이 AWS로 고정인 것도 ECR이 정해둔 값

```bash
docker tag myweb:1.0 <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb:1.0
docker images | grep myweb
```

- 태그
    - 이미지 이름 뒤 : 다음에 붙는 버전 표시
        - myweb : 1.0
    - 추후에 index.html 고쳐서 다시 빌드 —> myweb : 1.1 생김
        - 1.0 , 1.1 둘 다 있게 되면서 나중에 롤백할 때 가능
    - docker tag
        - 이미지를 복사하는 게 아니라 이름을 하나 더 붙이는 것

```bash
docker push <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb:1.0
```

- 푸시
    - 이름의 앞부분을 보고 목적지를 정한다.
    - 덩어리가 아닌 레이어 단위로 올라감

### C . ECS Fargate 배포와 장애 주입 테스트

- B에서 ECR에 올린 myweb:1.0 을 ECS Fargate로 실행
    - ALB를 통해 인터넷에 접속되는 구조를 Terraform으로 만듦
        - 인터넷 (port : 80) → ALB (public subnet 2개) → 타겟 그룹 → ECS Service → Task  2 (ECR의 myweb:1.0)
- network.tf
    - ALB는 서로 다른 public subnet 2개를 요구.
        - 7단계 network.tf 랑 다른 점
        - AZ 한 곳이 죽어도 ALB는 살아있어야하기 때문에 2개를 요구
    - 전이랑 다른 점
        - cidr_block : 10.0.2.0/24
        - 기존 public subnet : 10.0.1.0/24
            - 새로 만들지 않고 7단계에서 만들었던 public routing table 그대로 연결
            - 둘 다 0.0.0.0/0 ⇒ IGW로 나가기 때문에 중복해서 만들이유 X
