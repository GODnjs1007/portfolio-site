---
title: "배운 점"
---

#### A. 깃허브 조직과 서버 저장소

- 목적 : 팀원이랑 같이 쓰는 저장소를 한 사람 계정이 아닌 팀 이름 아래 둠
- 설명
    - 조직 만든 이유
        - 개인 계정으로 레포를 만들면 그 레포는 내 거가 되고 팀원은 설정도 바꾸지 못 함
        - yeoulmok 아래 주인 두 명으로 설정
            - owner 두 명 (팀원, 나)
                - 팀원도 앱, 웹 저장소를 조직안에 직접 만들어서 권한 같게 함
    - 조직 (Organization) : 여러 사람이 저장소를 같이 소유하는 깃헙 팀 계정
    - Owner : 조직의 모든 저장소와 설정 바꿀 수 있는 최고 권한
    - .env.example : 필요한 키 이름만 적어둔 빈 양식
        - 실제 값은 서버에만 둠
        - API 키는 VM의 ~/secrets/yeoulmok.env에만 두고 저장소에는 키 이름만 적힌 .env.example만 올림
        - 깃에 이게 필요한 이유 : 실행용이 아니라 안내용.
            - 나중에 내가 새 서버 만들거나 팀원이 서버 돌려볼 때 어떤 키인지 알기 위해서

#### B. 서버 VM과 저장소 연결

```bash
ssh-keygen -t ed25519 -f ~/.ssh/yeoulmok_server        # 이 저장소 전용 키 한 쌍을 새로 만듦
cat ~/.ssh/yeoulmok_server.pub                          # 공개키 출력 → GitHub Deploy keys에 붙여넣음
git clone git@github.com:yeoulmok/server.git ~/yeoulmok # 서버 저장소를 VM으로 복사
ssh -T git@github.com                                   # 연결 확인 → "Hi yeoulmok/server!"면 성공
set -a; source ~/secrets/yeoulmok.env; set +a           # API 키 파일을 환경변수로 불러옴
```

- 목적 : 홈랩 VM이 서버 저장소에 코드를 받고 (pull) 올릴 수 있게 (push) 그리고 API키는 저장소 밖에 두기 위함
- 설명
    - 디스크 확장 : LVM으로 남은 공간까지 늘려서 할당한 저장공간 전부 활용
    - 배포키 사용 이유 : 내 개인 SSH키를 VM에 넣으면 VM이 털렸을 때 내 모든 저장소가 위험.
    - ~/.ssh/config에 키 저장한 이유 : 키가 여러 개면 SSH가 아무거나 내밀기 때문에 적어두고 헷갈리지 않게 해둠
    - API 키 저장소 밖에 둔 이유 : 저장소가 공개라 키는 VM 안에만 두고 chmod 600으로 나만 읽게 해둠
    - 도메인을 /api로 나눈 이유 : api.yeoulmok.ihaewon.com 처럼 두 번이 들어가면 Cloudflare 무료 인증서가 안 되기 때문에 yeoulmok.ihaewon.com 하나에 웹을 두고 API는 /api/… 경로로 나눔
- 단어
    - ssh-keygen : SSH 키 한 쌍 (공개키, 비밀키)을 만드는 명령어
    - 배포 키 (Deploy Key) : 저장소 하나에만 접근하는 SSH키
    - LVM : 디스크 공간을 나중에 늘리거나 줄일 수 있게 묶어 관리하는 방식
    - set -a / set +a : 그 사이에 불러온 변수를 전부 환경변수로 등록 , 끄기
