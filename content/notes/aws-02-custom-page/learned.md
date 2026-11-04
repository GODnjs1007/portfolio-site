---
title: "배운 점"
---

- sudo nginx -T \| grep root
    - nginx -T : 설정 파일 전체를 합쳐서 출력하는 명령어
    - <mark>grep root : root 지시어만 걸러내는 명령어</mark>
        - root : nginx가 요청 받으면 파일을 찾으러 가는 디렉터리
            - 기본값 : /usr/share/nginx/html
- 웹페이지 교체 방식
    - nginx root 디렉터리의 index.html을 바꾸면 됨
        - 파일만 바꾸었기 때문에 nginx 재시작 필요 X
        - 설정파일 (nginx.conf) 고쳤을 때 reload/restart 필요
- 파일 소유자 , 권한
    - <mark>/usr/share/nginx/html은 root 소유자라서 sudo vi로 열어야 저장된다.</mark>
        - nginx는 요청 처리할 때 이 파일을 읽어야되는데 권한이 없으면 서버는 살아있지만 403이 뜬다
- http:// public 주소 —\> nginx 웹페이지 확인
