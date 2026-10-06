---
title: "AWS 1단계 · EC2 + Nginx 기본 배포"
date: 2026-08-06
projects: ["aws-infra"]
step: 1
summary: "AWS EC2에 Nginx 웹서버를 배포해서 브라우저로 외부 접속에 성공하는 것을 목표로 함."
tags: ["구축", "리눅스"]
troubleshooting: []
draft: false
---

## 목표

AWS EC2에 Nginx 웹서버를 배포해서 브라우저로 외부 접속에 성공하는 것을 목표로 함.

## A. 환경 세팅

- AWS 계정 생성, 리전 서울(ap-northeast-2) 설정
- 예산 알림(Zero-Spend Budget) \$1 기준 생성
- EC2 인스턴스 생성 (Amazon Linux, t3.micro)
    - t2.micro가 프리티어 대상이 아니어서 t3.micro로 변경
    - (2025.7.15 이후 계정은 프리티어 정책 변경 — 매달 750시간 무료 방식 → 가입 크레딧 차감 방식)
- 키 페어(my_first_key.pem) 생성 및 보관
- 네트워크 설정에서 HTTP 트래픽 허용 체크

## B. Nginx 설치

- EC2 Instance Connect로 터미널 접속
- 아래 명령어 순서대로 실행

`sudo yum update -y            # 설치된 패키지들을 최신 버전으로 갱신`

`sudo yum install nginx -y     # Nginx 웹서버 설치`

`sudo systemctl start nginx    # Nginx 지금 실행`

`sudo systemctl enable nginx   # 서버 재부팅돼도 자동으로 켜지게 등록`

### 접속 확인

- 브라우저에서 http://\[퍼블릭IP\] 접속 → "Welcome to nginx!" 확인
- `curl localhost` 로 서버 내부에서도 정상 응답 확인

## 1단계 용어

1단계에서 처음 나온 개념과 명령어. **A → B 진행 순서대로** 정리했다.

### A. 환경 세팅

#### 계정과 비용

| 용어 | 한 줄 설명 |
| --- | --- |
| 리전(Region) | AWS 데이터센터가 있는 지역. 서울은 ap-northeast-2 |
| 루트 사용자 | 계정 생성 시 만들어지는 최상위 계정. 모든 권한을 가짐 |
| IAM 사용자 | 루트가 만드는 하위 계정. 필요한 권한만 부여 |
| 예산 알림(Budgets) | 사용 금액이 기준을 넘으면 알려주는 기능. 차단은 하지 않음 |
| 프리티어 | 신규 계정 무료 사용 범위. 2025년 7월 이후 계정은 크레딧 차감 방식 |

#### EC2

| 용어 | 한 줄 설명 |
| --- | --- |
| EC2 | AWS에서 빌려 쓰는 가상 서버 |
| 인스턴스(Instance) | EC2로 빌린 가상 컴퓨터 한 대 |
| 인스턴스 유형 | t3.micro 형식. t=계열(범용·버스터블), 3=세대, micro=크기 |
| 인스턴스 상태 | running(실행·과금) / stopped(중지·EBS 비용만) / terminated(삭제·복구 불가) |
| AMI (Amazon Machine Image) | OS가 설치된 상태의 서버 초기 이미지 |
| Amazon Linux | AWS가 EC2용으로 제공하는 리눅스 배포판 |
| 키 페어 | SSH 접속용 인증 수단(.pem 파일). 재발급 불가 |

#### 접속과 방화벽

| 용어 | 한 줄 설명 |
| --- | --- |
| 퍼블릭 IP | 인터넷에서 서버를 찾아올 수 있는 외부용 주소 |
| 포트(port) | 서버의 여러 서비스를 구분하는 번호. HTTP=80, SSH=22 |
| 보안 그룹 | 인스턴스에 붙는 방화벽. 허용한 트래픽만 통과 |
| EC2 Instance Connect | 브라우저에서 터미널로 접속하는 AWS 기능 |

---

### B. Nginx 설치

#### 개념

| 용어 | 한 줄 설명 |
| --- | --- |
| Nginx | 브라우저 요청을 받아 파일을 돌려주는 웹서버 프로그램 |
| 패키지 관리자 | 프로그램 설치·갱신·삭제를 명령어로 처리하는 도구. Amazon Linux는 yum |
| 서비스(service) | 백그라운드에서 계속 도는 프로그램. systemctl로 관리 |
| 웹 루트 | 웹서버가 요청받은 파일을 찾으러 가는 폴더. Nginx 기본값은 /usr/share/nginx/html |
| index.html | 파일명 지정 없이 접속했을 때 웹서버가 기본으로 찾는 파일 |

EC2는 서버라는 "컴퓨터"고 Nginx는 그 위에서 도는 "프로그램"이다. EC2만 띄우면 아무 응답도 하지 않으며, Nginx를 설치해야 웹 요청에 응답한다.

#### 명령어

| 명령어 | 뜻 |
| --- | --- |
| sudo | 관리자 권한으로 명령 실행하는 접두어 |
| yum update -y | 설치된 패키지 목록을 최신으로 갱신. -y는 확인 질문에 모두 yes |
| yum install nginx -y | Nginx 설치 |
| systemctl start | 서비스를 지금 실행 |
| systemctl enable | 부팅 시 자동 시작하도록 등록. start와 별개다 |
| systemctl status | 서비스 현재 상태 확인 (active / inactive) |
| curl localhost | 서버 자신에게 요청을 보내 응답 확인 |

`start`만 하면 재부팅 시 꺼지고, `enable`만 하면 지금은 실행되지 않는다. 둘 다 실행해야 한다.
