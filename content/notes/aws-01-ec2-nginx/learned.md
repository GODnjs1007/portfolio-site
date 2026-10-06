---
title: "배운 점"
---

- EC2 : AWS에서 빌려 쓰는 가상 서버. 물리 컴퓨터를 사는 대신 필요한 만큼 빌리고 쓴 시간만큼 낸다.
- Nginx : 그 서버 위에서 도는 웹서버 프로그램. 브라우저가 보낸 요청을 받아서 해당 파일을 찾아 돌려준다.
    - 설치 명령어
        - sudo yum update -y                 : 설치된 패키지들 최신 버전 갱신
        - sudo yum install nginx -y         : nginx 웹 서버 설지
        - sudo systemctl start nginx       : nginx 실행
        - sudo systemctl enable nginx   : nginx
