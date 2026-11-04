---
title: "배운 점"
---

### A. 백엔드 뼈대와 서버 배포
- 목적
    - 화면이 일정을 달라고 하면 DB에서 꺼내 주는 서버 (Django)와 DB (PostgreSQL)를 띄운다
- 설명
    - 컨테이너 3개로 나눔 (docker-compose.yml)

        ```yaml
        db:         # PostgreSQL. 일정·회원 정보 저장. 외부 포트 없음
        web:        # Django. 요청 받아서 DB 조회 후 JSON으로 응답
        frontend:   # nginx. 화면 파일 주고, /api/ 요청은 web으로 넘김

        restart: unless-stopped          # 서버 재부팅돼도 자동으로 다시 켜짐
        depends_on:
          db:
            condition: service_healthy   # DB가 준비된 뒤에 Django 켜기
        ```

        - 각자 역할이 달라서 따로 띄움
        - 컨테이너끼리는 이름으로 부름 (web:8000, db)
        - docker compose : 컨테이너 여러 개를 파일 하나로 묶어서 한 번에 키고 끄는 도구
        - healthcheck : 컨테이너 가 진짜 준비됐는지 주기적으로 확인
    - nginx가 주소 보고 길을 나눔 (infra/nginx/default.conf)

        ```yaml
        location ~ ^/(api|admin|django-static)/ {
            proxy_pass http://web:8000;   # Django로
        }
        location / {
            try_files $uri $uri/ =404;    # 화면 파일
        }
        ```

        - /api/로 시작하면 장고로 보내고 나머지는 화면 파일을 줌
        - 주소 하나 (calendar.ihaewon.com)에 화면과 API가 같이 있음
        - proxy\_pass : 받은 요청을 다른 서버로 넘겨주는 nginx 설정
        - API : 화면이 서버에 데이터를 달라고 하는 창구 (주소 + 규칙)
    - 일정 테이블 구조 (events/models.py)

        ```py
        class Event(models.Model):
            owner = ForeignKey(User, null=True)  # 비면 공식 일정
            source = CharField()       # 어디서 온 일정
            external_id = CharField()  # 원래 사이트 글 번호
            title = CharField()
            start_at = DateTimeField()
            end_at = DateTimeField(null=True)    # 마감 없어도 됨
            raw = JSONField()          # 크롤링 원본
        ```

        ```py
        UniqueConstraint(
            fields=["source", "external_id"],   # 둘 다 같으면 같은 일정
            condition=Q(owner__isnull=True),    # 공식 일정에만
        )
        ```
