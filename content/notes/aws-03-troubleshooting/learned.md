---
title: "배운 점"
---

### 장애 1 : Nginx 설정 파일 문법 오류 (일부 줄 세미콜론 제거)

- sudo nginx -t 로 사전 문법 오류 검사
    - nginx: [emerg] unexpected "}" in /etc/nginx/nginx.conf:15
    - —> 15번 째 줄 } 가 닫히면 안 되는데 닫힘. ( emerg → 치명적)
- sudo cat -n /etc/nginx/nginx.conf \| sed -n '10,17p'
    - 10번째 줄 부터 17번째 줄까지 표시 (sed 문법)
- sudo vi /etc/nginx/nginx.conf —> 들어가서 수정
- sudo nginx -t → 성공 확인
    - nginx: the configuration file /etc/nginx/nginx.conf syntax is ok<br>nginx: configuration file /etc/nginx/nginx.conf test is successful

### 장애 2 : 보안 그룹에 HTTP 포트 차단

- curl localhost
    - 입력했을 때 내가 작성한 html 정상 출력
- http:// public IP 입력했을 때 연결 실패
    - 여기서 알 수 있는 점은 curl 시도했을 때 살아있는 걸 보면 nginx 는 죽지 않았고 연결시켜주는 네트워크 접근 차단이 돼었다는 걸 알 수 있음
- 오류
    - ERR_CONNECTION_TIMED_OUT → 요청이 서버에 도달조차 못함 (방화벽에서 차단)

### 장애 3 : HTML 권한 오류

- index.html 의 권한을 chmod 000 으로 제한해보았다.
- 403 Forbidden<br>nginx/1.30.3
    - 권한을 000으로 제한하면 403 오류가 나오는 것을 확인했다.

### 장애 4 : nginx 프로세스 중지

- sudo systemctl status nginx
    - nginx가 활성화 돼있는지 알 수 있는 코드
    - 활성화 돼있으면 active로 표시
- sudo systemctl stop nginx
    - nginx 비활성화
- sudo systemctl status nginx<br>sudo ss -lntp
    - nginx 는 inactive
    - 네트워크는 SSH만 살아있음
- sudo systemctl start nginx<br>sudo systemctl status nginx<br>sudo ss -lntp
    - nginx 는 active 로 변경
    - 네트워크 80포트도 활성화
- sudo systemctl is-enabled nginx
    - enabled 확인
- 오류
    - ERR_CONNECTION_REFUSED → 서버까지는 도달했으나 80번 포트에 대기 중인 프로세스가 없어 즉시 거절

| 에러 | 어디까지 도달? | 원인 |
| --- | --- | --- |
| ERR_CONNECTION_TIMED_OUT (2번째) | 서버에 도달 못함 | 보안 그룹·방화벽 |
| ERR_CONNECTION_REFUSED (4번째) | 서버는 도달, 프로세스 없음 | 서비스 중지 |
| 403 (3번째) | Nginx가 응답까지 함 | 파일 권한 |
| emerg (1번째) | 서비스 시작 자체가 불가 | 설정 파일 문법 |
