---
title: "배운 점"
---

- <mark>EC2 : AWS에서 빌려 쓰는 가상 서버. 물리 컴퓨터를 사는 대신 필요한 만큼 빌리고 쓴 시간만큼 낸다</mark>.
- Nginx : 그 서버 위에서 도는 웹서버 프로그램. 브라우저가 보낸 요청을 받아서 해당 파일을 찾아 돌려준다.
    - 설치 명령어
        - sudo yum update -y                  : 설치된 패키지들 최신 버전 갱신
        - sudo yum install nginx -y         : nginx 웹 서버 설치
        - sudo systemctl start nginx       : nginx 실행
        - sudo systemctl enable nginx   : 재부팅돼도 자동으로 켜지게 등록
            - <mark>start는 지금 켜는 것, enable은 부팅 때 켜지게 등록하는 것</mark>
    - 아마존 리눅스 2023은 dnf가 표준이고 yum은 호환용 링크이다.
        - yum을 입력해도 실제로는 dnf가 실행된다.
- 접속 방식
    - 키 페어 (.pem)
        - 개인키 : 터미널에서 <mark>ssh -i 키.pem ec2-user@퍼블릭IP</mark> 로 접속
        - 공개키 : EC2 안에 가지고 있음
    - EC2 Instance Connect (브라우저)로 접속해서 .pem 은 사용하지 않음
        - <mark>Instance Connect : AWS가 접속할 때마다 임시 키를 서버에 넣어주는 방식</mark>
            - SSH를 내 IP로 제한하면 Instance Connect도 막힘 (AWS 쪽 IP에서 들어오기 때문)
- 확인 방법
    - <mark>브라우저에 http://퍼블릭IP : 밖에서 들어오는 길까지 확인</mark>
    - <mark>curl localhost : 서버 안에서만 확인</mark>

        —> 둘을 나눠서 본다면 nginx가 죽은 건지 네트워크가 막힌 건지 확인 가능
