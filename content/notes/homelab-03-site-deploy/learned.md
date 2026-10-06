---
title: "배운 점"
---

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
