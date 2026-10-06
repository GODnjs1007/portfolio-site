---
title: "배운 점"
---

### A. Docker 기초와 이미지 만들기

- 방식의 변화
    - 지금까지의 방식
        - 가상컴퓨터 → 프로그램 설치 → 실행 (VM—> OS 전체)
            1. 느리다
            2. 무겁다
            3. 손으로 고치면 거기에만 있음.
    - 새로운 방식
        - 컨테이너 : 프로그램과 프로그램이 돌아가는 데 필요한 것들을 통째로 한 덩어리로 묶어 그대로 실행
            - VM은 OS를 들고다니고, 컨테이너는 호스트의 OS를 빌려 씀
            - 컨테이너 안에서 고친 건 컨테이너를 지우면 사라짐
                - 고칠 게 있으면 컨테이너가 아니라 이미지를 새로 만들어야 함

```bash
docker run -d -p 8080:80 --name test nginx
```

- 컨테이너와 계층구조
    - docker : 도구 (만들고, 받아오고, 실행시켜주는 프로그램)
    - 이미지 : 파일 (층으로 쌓인 덩어리, 안 변함)
        - nginx : 틀 이름
    - 컨테이너 : 실행 상태 (이미지를 돌린 것, 프로세스 하나)
        - 지금 까지 EC2는 가상컴퓨터 한 대였다면, 컨테이너는 프로세스 (실행중인 프로그램 하나)
- run -d -p 8080:80
    - 8080 : 내 맥 —> 맘대로 설정 가능
    - 80 : 컨테이너 —> 컨테이너 안 80번의 nginx가 응답
    - -p : 내 맥에서 컨테이너로 들어갈 수 있게 해주는 역할
    - run : 이미지로 컨테이너를 만들어 실행
    - -d : 백그라운드에서 실행
        - 백그라운드 : 상태  (터미널이 묶이냐 안 묶이냐의 상태) / 컨테이너를 돌리는 건 docker

### B . ECR 이미지 푸시

- A에서 만든 이미지는 내 Docker 안에서만 존재 —> ECR가 필요한 이유
    - ECR : 이미지를 올려둔 AWS 창고
    - ECS : 창고에서 이미지를 꺼내서 실제로 돌려주는 곳
        - 다른 곳에서 실행되기 때문에 이미지를 볼 수 없었다. 그래서 ECR이 필요

```bash
aws ecr create-repository --repository-name myweb --region ap-northeast-2
```

- 리포지토리
    - 이미지 한 종류를 담는 칸
    - 다른 애플리케이션이면 다른 리포지토리 필요

```bash
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com
```

- 인증
    - ECR은 인증없이 push 할 수 없다.
    - get-login-password
        - 12시간짜리 임시 토큰 발급 —> 파이프로 docker login에 넘김
            - 기존 aws ecr get-login-password --region ap-northeast-2 으로 로그인하게 되면 화면에 비밀번호가 뜬다.
                - docker login -u AWS -p \<토큰\> 으로 로그인하면 히스토리에 남음
            - 이 코드를 사용하면 화면을 비밀번호랑 입력하는 칸이 뜨지않고 바로 프로그램으로 넘어간다.
        - 사용자 이름이 AWS로 고정인 것도 ECR이 정해둔 값

```bash
docker tag myweb:1.0 <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb:1.0
docker images | grep myweb
```

- 태그
    - 이미지 이름 뒤 : 다음에 붙는 버전 표시
        - myweb : 1.0
    - 추후에 index.html 고쳐서 다시 빌드 —> myweb : 1.1 생김
        - 1.0 , 1.1 둘 다 있게 되면서 나중에 롤백할 때 가능
    - docker tag
        - 이미지를 복사하는 게 아니라 이름을 하나 더 붙이는 것

```bash
docker push <계정 ID>.dkr.ecr.ap-northeast-2.amazonaws.com/myweb:1.0
```

- 푸시
    - 이름의 앞부분을 보고 목적지를 정한다.
    - 덩어리가 아닌 레이어 단위로 올라감

### C . ECS Fargate 배포와 장애 주입 테스트

- B에서 ECR에 올린 myweb:1.0 을 ECS Fargate로 실행
    - ALB를 통해 인터넷에 접속되는 구조를 Terraform으로 만듦
        - 인터넷 (port : 80) → ALB (public subnet 2개) → 타겟 그룹 → ECS Service → Task  2 (ECR의 myweb:1.0)
- network.tf
    - ALB는 서로 다른 public subnet 2개를 요구.
        - 7단계 network.tf 랑 다른 점
        - AZ 한 곳이 죽어도 ALB는 살아있어야하기 때문에 2개를 요구
    - 전이랑 다른 점
        - cidr_block : 10.0.2.0/24
        - 기존 public subnet : 10.0.1.0/24
            - 새로 만들지 않고 7단계에서 만들었던 public routing table 그대로 연결
            - 둘 다 0.0.0.0/0 ⇒ IGW로 나가기 때문에 중복해서 만들이유 X
