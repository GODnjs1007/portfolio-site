---
title: "AWS 3단계 · 장애 발생 및 트러블슈팅"
date: 2026-07-30
projects: ["aws-infra"]
step: 3
summary: "일부러 장애를 만들고, 로그/명령어로 원인을 진단하고 복구하는 연습"
tags: ["트러블슈팅", "리눅스", "네트워크"]
troubleshooting:
  - "장애 1: Nginx 설정 파일 문법 오류"
  - "장애 2: 보안 그룹으로 80번 포트 차단"
  - "장애 3: HTML 파일 권한 오류 (403 에러)"
  - "장애 4: Nginx 프로세스 중지"
  - "브라우저에 변경사항이 반영되지 않음"
draft: false
---

## 목표

일부러 장애를 만들고, 로그/명령어로 원인을 진단하고 복구하는 연습

## 진행 과정

## 장애 1: Nginx 설정 파일 문법 오류

**증상**

`/etc/nginx/nginx.conf`의 `worker_connections 1024` 뒤 세미콜론(`;`)을 일부러 제거하고 저장

**확인**

```bash
sudo nginx -t
```

```plain text
nginx: [emerg] unexpected "}" in /etc/nginx/nginx.conf:15
nginx: configuration file /etc/nginx/nginx.conf test failed
```

에러는 15번째 줄을 가리켰지만, 원인 확인을 위해 주변 줄도 함께 확인:

```bash
sudo cat -n /etc/nginx/nginx.conf | sed -n '10,17p'
```

```plain text
13  events {
14      worker_connections 1024
15  }
```

**원인**

에러가 15번째 줄(`}`)로 표시됐지만, 실제 원인은 14번째 줄의 세미콜론 누락. Nginx가 14번째 줄 문장이 아직 안 끝났다고 판단하고 계속 읽어가다가, 15번째 줄의 `}`를 만나 예상치 못한 문법으로 에러를 발생시킨 것. **에러 줄 번호와 실제 원인 줄이 다를 수 있음**을 확인.

**해결**

```bash
sudo vi /etc/nginx/nginx.conf
```

14번째 줄에 세미콜론 추가 → `worker_connections 1024;`

**해결 확인**

```bash
sudo nginx -t
```

```plain text
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

<!-- 이미지: 세미콜론 추가 후 sudo nginx -t 문법 검사 성공 화면 -->

```bash
sudo systemctl restart nginx
sudo systemctl status nginx
```

→ active (running) 확인

**재발 방지**

- 설정 파일 수정 후에는 `systemctl restart` 전에 반드시 `nginx -t`로 먼저 문법 검증
- 에러 줄 번호만 보지 말고 그 위쪽 줄도 함께 확인하는 습관

## 장애 2: 보안 그룹으로 80번 포트 차단

**증상**

EC2 보안 그룹의 인바운드 규칙에서 HTTP(80번 포트) 규칙을 일부러 삭제

**확인**

서버 내부 확인:

```bash
curl localhost
```

→ 정상적으로 HTML 응답 (서버 자체는 문제없음)

<!-- 이미지: 서버 내부에서 curl localhost 실행 시 HTML 정상 응답 화면 -->

외부 브라우저 접속 시도:

```plain text
http://[퍼블릭IP]
```

→ 연결 실패, `ERR_CONNECTION_TIMED_OUT`

<!-- 이미지: 외부 브라우저 접속 시 ERR_CONNECTION_TIMED_OUT 화면 -->

**원인**

서버 내부(`curl localhost`)는 정상 응답하는데 외부 브라우저는 타임아웃되는 패턴 → **서버(Nginx) 자체 문제가 아니라, 보안 그룹이 외부 요청 자체를 막고 있는 네트워크 접근 문제**로 판단. Nginx가 죽었다면 `curl localhost`도 함께 실패했을 것이므로, 이 대비를 통해 원인을 구분할 수 있음.

**해결**

1. EC2 콘솔 → 보안 그룹 → 인바운드 규칙 편집
2. 규칙 추가 → 유형: HTTP, 소스: Anywhere-IPv4(0.0.0.0/0)
3. 규칙 저장

**해결 확인**

브라우저에서 `http://[퍼블릭IP]` 재접속 → 정상적으로 페이지 뜨는 것 확인

<!-- 이미지: HTTP 규칙 재추가 후 브라우저에서 페이지 정상 표시 화면 -->

**재발 방지**

- 외부 접속 장애 발생 시, 서버 내부(`curl localhost`)와 외부 접속을 먼저 비교해서 "서버 문제인지 네트워크 문제인지"부터 구분하는 진단 순서를 습관화
- 보안 그룹 규칙 변경 시 되돌리는 방법(규칙 추가)도 함께 숙지해둘 것

## 장애 3: HTML 파일 권한 오류 (403 에러)

**진행**

파일 권한 확인

```bash
ls -l /usr/share/nginx/html/index.html
```

<!-- 이미지: ls -l로 index.html 파일 권한 확인 화면 -->

권한 제거

```bash
sudo chmod 000 /usr/share/nginx/html/index.html
```

<!-- 이미지: chmod 000으로 index.html 권한 제거 화면 -->

브라우저 재접속 → 403 Forbidden 확인

```plain text
403 Forbidden
nginx/1.30.3
```

<!-- 이미지: 브라우저에 403 Forbidden 표시 화면 -->

원인: 파일 권한이 000(권한 없음)으로 설정되어 Nginx가 파일을 읽지 못해 접근 거부됨. 이전 장애(타임아웃)와 달리 이번엔 403 에러 발생 → 요청은 서버에 도달했으나 내부에서 거부된 케이스

권한 복구

```bash
sudo chmod 644 /usr/share/nginx/html/index.html
```

<!-- 이미지: chmod 644로 index.html 권한 복구 화면 -->

브라우저 새로고침 → 페이지 정상 표시 확인

**배운 점**

- 리눅스 파일 권한 개념 (`chmod`, 권한 표기 `rwx`)
- 403 Forbidden(서버 내부 권한 문제)과 타임아웃(네트워크 문제)의 차이

## 장애 4: Nginx 프로세스 중지

**진행**

현재 서비스 상태 확인 (정상 상태 기준점)

```bash
sudo systemctl status nginx
```

→ `active (running)` 확인

<!-- 이미지: systemctl status nginx로 active (running) 확인 화면 -->

서비스 중지

```bash
sudo systemctl stop nginx
```

브라우저 강제 새로고침(`Ctrl + Shift + R`) → 접속 실패

```plain text
사이트에 연결할 수 없음
ERR_CONNECTION_REFUSED
```

<!-- 이미지: Nginx 중지 후 브라우저 ERR_CONNECTION_REFUSED 화면 -->

원인 진단 — 서비스 상태 및 포트 리스닝 확인

```bash
sudo systemctl status nginx
sudo ss -lntp
```

→ 상태는 `inactive (dead)`, `ss -lntp` 목록에서 80번 포트가 사라지고 22번(SSH)만 남아있음

<!-- 이미지: systemctl status nginx 결과 inactive (dead) 화면 -->

<!-- 이미지: ss -lntp 결과 22번 포트만 리스닝 중인 화면 -->

복구 및 재확인

```bash
sudo systemctl start nginx
sudo systemctl status nginx
sudo ss -lntp
```

→ `active (running)` 복귀, 80번 포트 다시 리스닝 확인

부팅 후 자동 시작 설정 확인

<!-- 이미지: Nginx 재시작 후 active (running) 및 80번 포트 리스닝 확인 화면 -->

```bash
sudo systemctl is-enabled nginx
```

→ `enabled` 확인 (서버 재부팅 시에도 자동 실행됨)

<!-- 이미지: systemctl is-enabled nginx 결과 enabled 화면 -->

---

**배운 점**

에러 코드에 따라 원인 범위를 좁힐 수 있음

| 에러 | 요청이 도달한 지점 | 의심할 원인 |
| --- | --- | --- |
| `ERR_CONNECTION_TIMED_OUT` | 서버에 도착조차 못 함 | 네트워크 / 보안 그룹 / 방화벽 |
| `ERR_CONNECTION_REFUSED` | 서버까지는 도착, 포트에서 받아줄 프로세스 없음 | 서비스(프로세스) 중지 |
| `403 Forbidden` | 서버가 응답까지 함, 명시적으로 거부 | 파일 권한 / 설정 문제 |

- `ss -lntp`로 현재 서버가 어떤 포트를 열고 대기 중인지 직접 확인할 수 있음. "서비스가 정말 죽었는지" 검증하는 가장 확실한 방법
- `systemctl is-enabled`로 부팅 후 자동 시작 여부를 확인. **"지금 실행 중인 것"과 "재부팅 후에도 살아나는 것"은 별개 문제**이며, `enable` 설정이 없으면 재부팅 시 서비스가 안 올라와 장애가 이어짐

## 트러블슈팅

**브라우저에 변경사항이 반영되지 않음**

- 증상: 장애 3에서 파일 권한을 `000`으로 변경한 뒤 브라우저를 새로고침했는데, 기존 페이지가 그대로 표시됨
- 원인: 브라우저 캐시. 브라우저가 이전에 받아둔 페이지를 저장해두고 서버에 재요청하지 않은 채 그대로 보여준 것
- 해결: 강제 새로고침(`Ctrl + Shift + R`)으로 캐시를 무시하고 서버에 재요청 → 실제 상태인 403 Forbidden 확인
- 재발 방지: 서버 쪽 변경이 반영 안 된 것처럼 보일 때, 서버 문제로 단정하기 전에 **캐시 가능성부터 강제 새로고침으로 확인**할 것

## 3단계 용어

3단계에서 처음 나온 개념과 명령어. **장애 1 → 4 순서대로** 정리했다.

### 장애 1: 설정 파일 문법 오류

| 용어 / 명령어 | 뜻 |
| --- | --- |
| 설정 문법 오류 | 세미콜론 누락, 괄호 불일치 등으로 서비스가 시작되지 않는 상황 |
| 에러 레벨 | 로그의 심각도 구분. emerg(최상위) → alert → crit → error → warn → notice → info → debug |
| emerg (emergency) | Nginx 에러 로그에서 가장 심각한 수준. 서비스 시작 자체가 불가 |
| nginx -t | Nginx 설정 파일 문법 오류를 사전 검사 (소문자 t) |
| cat -n | 파일 내용을 줄 번호와 함께 출력 |
| sed -n '시작,끝p' | 파일에서 특정 범위의 줄만 출력 |

### 장애 2: 보안 그룹으로 포트 차단

| 용어 / 명령어 | 뜻 |
| --- | --- |
| ERR_CONNECTION_TIMED_OUT | 요청이 서버에 도달조차 못해 기다리다 시간초과. 방화벽 차단이 원인 |
| curl | 서버에 요청을 보내고 응답을 받아오는 도구 |

`curl localhost`는 정상인데 외부 접속만 실패한다면, 웹서버는 살아있고 **네트워크 접근이 차단된 것**이다. 이렇게 안팎을 나눠 확인하면 원인 범위를 좁힐 수 있다.

### 장애 3: 파일 권한 오류

| 용어 / 명령어 | 뜻 |
| --- | --- |
| 403 Forbidden | 요청은 도달했으나 서버가 권한 등의 이유로 거부한 응답 |
| 파일 권한 | 읽기(r)·쓰기(w)·실행(x)을 소유자·그룹·기타별로 지정. 644, 755 등 숫자로 표기 |
| ls -l | 파일 목록을 권한·소유자 정보와 함께 표시 |
| chmod | 파일의 읽기·쓰기·실행 권한을 변경 (예: 644, 000) |

403은 Nginx가 요청을 받아 응답까지 했다는 뜻이므로, 네트워크와 서비스는 정상이고 **파일 쪽 문제**임을 알 수 있다.

### 장애 4: 프로세스 중지

| 용어 / 명령어 | 뜻 |
| --- | --- |
| 프로세스 | 실행 중인 프로그램 하나하나 |
| ERR_CONNECTION_REFUSED | 서버까지 도달했으나 해당 포트에 대기 중인 프로세스가 없어 즉시 거절 |
| systemctl stop / restart | 서비스 중지 / 재시작 |
| systemctl is-enabled | 부팅 시 자동 시작 설정 여부 확인 |
| ss -lntp | 현재 서버가 열고 대기 중인 포트 목록 확인 |

### 진단 원칙

| 용어 | 한 줄 설명 |
| --- | --- |
| 트러블슈팅 순서 | 증상 확인 → 로그 확인 → 원인 파악 → 조치 → 재발방지 기록 |

**에러 메시지가 곧 단서다.** 어디까지 도달했는지를 보면 원인 위치가 좁혀진다.
