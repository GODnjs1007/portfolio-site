---
title: "배운 점"
---

### A. GitHub 저장소와 프로젝트 뼈대
- 목적
    - 팀 5명이 한 저장소에서 서로 안 부딪히고 작업할 수 있는 틀 만들기
- 설명
    - 역할 : 백엔드 (Django API)
    - 크롤러와 DB가 주고받을 데이터 형식 정하기 (docs/data-format.md)
        1. source : scholarship —> 어디서 온 일정인지
        2. external\_id : 12345  —> 원래 사이트 글 번호
        3. title : 국가장학금 2차
        4. start\_at : “2026-11-03T00:00\:00+09\:00”
        5. raw : \{…\}                    —> 긁어온 원본 통째로
            - 가공 전 원본 데이터. 파싱 실수했을 때 다시 안 긁고 고칠 수 있음

        - 팀원은 이 모양대로만 넘기고 난 이 모양대로 받음
    - DB는 PostgreSQL
        - 크롤러랑 웹이 동시에 써도 안 막히고 중복이면 갱신하는 기능 (upsert)이 존재
        - upsert : 없으면 새로 넣고 (insert) 있으면 고치는 (update) 것
    - 비밀값은 깃에 올리지 않음
        - .env : 진짜 비번 —> 서버에
        - .env.example —> 깃 올림 (키 이름만)
    - 런어스는 iCal 주소 받음
        - 진짜 비번 받고 서버에 저장하는 건 위험
    - polling : 서버가 정해진 주기마다 가서 다시 받아오는 방식 (실시간 X)

### B. 서버 VM 구축
- 목적
    - 이 프로젝트만 쓰는 서버를 홈랩에 따로 만듦
- 설명
    - VM 105 calendar 생성 (2코어, 4GB , 32GB)
    - 기초 세팅

        ```bash
        sudo apt update && sudo apt upgrade -y        # 패키지 최신화
        sudo apt install -y qemu-guest-agent git curl  # 필요한 도구 설치
        sudo timedatectl set-timezone Asia/Seoul       # 한국 시간으로
        sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv  # 안 쓰던 디스크 절반까지 다 쓰게 늘림
        ```

        - Qemu Agent : VM 안에서 돌면서 Proxmox에 IP·상태를 알려주는 프로그램
        - lvextend : 디스크 파티션 크기를 늘리는 명령어
    - Docker 설치 후 sudo 없이 쓰게 함

        ```bash
        sudo usermod -aG docker haewonlee   # docker 그룹에 추가 (다시 로그인해야 적용)
        ```

        - 도커 그룹 : 여기 들어가야 sudo 없이 docker 명령어 사용 가능
    - 저장소 전용 배포 키

        ```bash
        ssh-keygen -t ed25519 -f ~/.ssh/campus_calendar   # 이 저장소 전용 키 만들기
        git clone git@github-calendar:<내 계정>/campus-calendar.git   # 아래 별칭으로 클론
        ```

        ```bash
        # ~/.ssh/config 파일 내용 (명령어 아님)
        Host github-calendar                  # 별칭
            HostName github.com
            IdentityFile ~/.ssh/campus_calendar   # 이 별칭으로 접속할 때 쓸 키
        ```

        - 한 VM에 여러 저장소 키가 있어도 별칭으로 구분
    - 다 끝낸 상태를 스냅샷 base-setup으로 저장

### C. 시안 배포와 도메인 연결
- 목적
    - 프론트 시안을 calendar.ihaewon.com으로 밖에서 볼 수 있게 만듦
- 설명
    - nginx 컨테이너로 시안 띄움

        ```bash
        docker compose up -d frontend     # nginx 컨테이너 실행
        curl -I localhost:8080            # 200 OK면 정상
        ```

        - nginx가 frontend/ 폴더를 바로 읽어서, 시안 바뀌면 git pull만 하면 반영
    - 포트를 127.0.0.1에만 묶음

        ```bash
        frontend:
          image: nginx:alpine
          ports:
            - "127.0.0.1:8080:80"
        ```

        - Docker 설정 —> VM과 컨테이너 사이를 어떻게 연결할지 정하는 코드
            - 들어오는 길
                - 사용자 브라우저 (calendar.ihaewon.com) —> Cloudflare (터널) —> VM 안 cloudflared (localhost:8080) —> docker —> nginx 컨테이너 :80
                - 같은 VM 안의 cloudflared 만 접속 가능. 밖에선 터널로만 들어옴
        - <mark>포트 매핑 : VM 포트와 컨테이너 포트를 이어주는 설정 (VM주소 : VM포트 : 컨테이너 포트)</mark>
    - Cloudflare Tunnel 연결

        ```bash
        calendar.ihaewon.com → http://localhost:8080   # Route 규칙
        ```

        - 공유기 포트를 안 열어도 외부 공개 가능. cloudflared를 서비스로 깔아서 재부팅해도 자동 연결
            - Route : 이 주소로 오면 터널 안 어느 서비스로 보낼지 정하는 규칙
            - CNAME : 이 주소는 저 주소의 별칭이라고 알려주는 DNS 기록
            - <mark>Cloudflare Tunnel : 서버가 Cloudflare 쪽으로 먼저 연결을 열어서 공유기 포트를 안 열고도 외부에 공개하는 방식</mark>
