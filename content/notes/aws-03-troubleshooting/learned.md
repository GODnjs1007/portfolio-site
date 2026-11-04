---
title: "배운 점"
---

### 장애 1 : Nginx 설정 파일 문법 오류 (일부 줄 세미콜론 제거)

- sudo nginx -t 로 사전 문법 오류 검사
    - <mark>nginx: [emerg] unexpected "}" in /etc/nginx/nginx.conf:15</mark>
        - 세미콜론이 없으면 지시어가 아직 안 끝났다 보고 다음 줄 까지 계속 읽는데 }를 만나는 순간 문법이 깨져서 오류.
            - <mark>에러 알려주는 줄 번호는 터진 지점이고 원인 지점이 아님! —> 윗 줄까지 봐야함</mark>
        - emerg : 심각한 오류라는 뜻
- <mark>sudo cat -n /etc/nginx/nginx.conf \| sed -n '10,17p'</mark>
    - 10번째 줄 부터 17번째 줄까지 표시 (sed 문법)
- sudo vi /etc/nginx/nginx.conf —> 들어가서 수정
- sudo nginx -t → 성공 확인
    - nginx: the configuration file /etc/nginx/nginx.conf syntax is ok<br>nginx: configuration file /etc/nginx/nginx.conf test is successful

### 장애 2 : 보안 그룹에 HTTP 포트 차단

- curl localhost
    - 입력했을 때 내가 작성한 html 정상 출력
- http:// public IP 입력했을 때 연결 실패
    - <mark>여기서 알 수 있는 점은 curl 시도했을 때 살아있는 걸 보면 nginx 는 죽지 않았고 연결시켜주는 네트워크 접근 차단이 돼었다는 걸 알 수 있음</mark>
- 오류
    - <mark>ERR_CONNECTION_TIMED_OUT → 요청이 서버에 도달조차 못함 (방화벽에서 차단)</mark>
        - 보안 그룹은 막힌 요청을 버리기만 하고 거절 응답을 보내지 않는다.
            - <mark>브라우저가 기다리다 타임아웃</mark>

### 장애 3 : HTML 권한 오류

- index.html 의 권한을 chmod 000 으로 제한해보았다.
- <mark>403 Forbidden</mark><br>nginx/1.30.3
    - 권한을 000으로 제한하면 403 오류가 나오는 것을 확인했다.
    - 403이 뜨면 nginx는 응답을 돌려줬다는 뜻으로 네트워크와 프로세스는 정상이지만 문제는 뒤쪽 파일이다.
        - nginx 워커 프로세스는 nginx 유저로 돌기 때문에 others 읽기 권한이 없으면 읽지 못 한다.
            - root 소유 파일이어도 644면 읽을 수 있다.

### 장애 4 : nginx 프로세스 중지

- <mark>sudo systemctl status nginx</mark>
    - nginx가 활성화 돼있는지 알 수 있는 코드
    - <mark>활성화 돼있으면 active로 표시</mark>
- sudo systemctl stop nginx
    - nginx 비활성화
- sudo systemctl status nginx<br><mark>sudo ss -lntp</mark>
    - nginx 는 inactive
    - 네트워크는 SSH만 살아있음
    - -lntp : 지금 이 서버에서 몇 번 포트를 누가 듣고 있는지 보는 명령어
        - -l : 들고 있는 소켓만
        - -n : 포트를 숫자로
        - -t : TCP만
        - -p : 그 포트를 쓰는 프로세스 이름
- sudo systemctl start nginx<br>sudo systemctl status nginx<br>sudo ss -lntp
    - nginx 는 active 로 변경
    - 네트워크 80포트도 활성화
- <mark>sudo systemctl is-enabled nginx</mark>
    - enabled 확인
- 오류
    - <mark>ERR_CONNECTION_REFUSED → 서버까지는 도달했으나 80번 포트에 대기 중인 프로세스가 없어 즉시 거절</mark>

### 로그 위치

- /var/log/nginx/error.log : 403의 이유가 여기 남음
- /var/log/nginx/access.log : 요청이 들어왔는지 , 어떤 응답 코드로 끝났는지 남음
    - <mark>브라우저 에러는 어디까지 갔는지만 알려주고 이유는 로그에 남음</mark>

| 에러 | 어디까지 도달? | 원인 |
| --- | --- | --- |
| ERR_CONNECTION_TIMED_OUT (2번째) | 서버에 도달 못함 | 보안 그룹·방화벽 |
| ERR_CONNECTION_REFUSED (4번째) | 서버는 도달, 프로세스 없음 | 서비스 중지 |
| 403 (3번째) | Nginx가 응답까지 함 | 파일 권한 |
| emerg (1번째) | 서비스 시작 자체가 불가 | 설정 파일 문법 |

**<mark>—> 에러 메시지를 먼저 범위를 네트워크 , 프로세스 , 파일 권한, 설정 중 하나로 좁히고 그 다음 로그로 원인을 확정한다</mark>**
