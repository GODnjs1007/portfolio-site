---
title: "배운 점"
---

### A. 도메인 구매
- 도메인 : 숫자 IP 대신 쓰는 사람이 읽는 주소 (ihaewon.com)
    - 필요한 이유 : Tailscale 주소 (100.x.x.x) 는 내 기기에서만 열리기 때문에 외부용 주소가 필요
- Cloudflare 에서 구매
    - 원가 판매 (년에 10달러) +  DNS가 자동으로 Cloudflare에 연결
- 자동갱신 ON
    - 갱신 놓치면 ihaewon.com 도메인을 다른 사람이 가져감
- WHOIS : 도메인 주인 정보를 누구나 조회하는 명부
    - Cloudflare가 기본적으로 가려줌
        - 가려주지 않으면 사이트를 본 아무나 우리 집 주소 및 전화번호를 알 수 있음
        - whois ihaewon.com 쳐보면 다 나오는 걸 막아

### B. cloudflared 설치
```bash
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared

```

- cloudflared : VM에 까는 터널 프로그램
- 순서 : 서명키 받기 → 저장소 추가 → 설치
    - 서명키 : 진짜 cloudflare 패키지인지 확인하는 키
    - 1단계 proxmox 저장소 설정이랑 같은 원리
- docker ps 로 사이트 컨테이너가 80번에 떠있는지 확인 → 터널이 연결할 대상

### C. 터널 생성과 도메인 연결
- VM이 먼저 cloudflare로 연결을 열어둠 (아웃바운드) → 방문자 요청이 그 연결을 타고 들어옴 → 공유기 포트 안 열어도 됨
    - 포트포워딩 : 공유기 문을 열어 밖에서 들어오게 하는 것 (집 IP 노출 및 공격위험성 농후)
- 흐름 : <mark>방문자 → Cloudflare(HTTPS) → 터널 → cloudflared → localhost:80 → nginx 컨테이너</mark>
    - VM의 cloudflared가 먼저 Cloudflare 서버로 연결을 걺.
        - 안에서 밖으로 나가는 거라 공유기가 막지 않음.
        - 이 연결을 끊지 않고 열어두는 것이 터널
            - 터널 : 안에서 밖으로 전화를 걸어두고 그 통화로 대화
    - 방문자가 ihaewon.com 에 접속하면 DNS가 Cloudflare로 가라고 안내.
        - 방문자는 집이 아니라 Cloudflare에 도착함
        - Cloudflare 은 열려있는 터널로 보냄.
        - DNS : 인터넷 전화번호부
            - 사람들은 도메인을 기억, 컴퓨터는 104.21.x.x 같은 숫자 (IP) 로만 찾아가고 그것을 연결시켜줌
    - cloudflared가 받아서 같은 VM안에 있는 Nginx(localhost:80)으로 넘기고 응답은 터널 타고 다시 돌아감

    ```bash
    cloudflared tunnel login
    cloudflared tunnel create portfolio
    ```

    - login : 브라우저에서 ihaewon.com 승인 → VM에 인증서 (cert.pem) 저장
    - create: 터널 생성 + 인증파일 (.json) 생성. .json 은 터널 비밀번호라 공유 금지
- 설정파일 (/etc/cloudflared/config.yml)

    ```bash
    tunnel: <터널 ID>
    credentials-file: /etc/cloudflared/<터널 ID>.json
    ingress:
      - hostname: ihaewon.com
        service: http://localhost:80
      - hostname: www.ihaewon.com
        service: http://localhost:80
      - service: http_status:404
    ```

    - 터널 ID는 create 할 때 나온 긴 문자열 (보안상 적지 않음)
    - ingress : 들어온 주소별로 어떻게 보낼지 정하는 규칙
    - service : http_status : 404 —> 위에 없는 주소는 404로 거절

    ```bash
    cloudflared tunnel route dns portfolio ihaewon.com
    cloudflared tunnel route dns portfolio www.ihaewon.com
    sudo cloudflared --config /etc/cloudflared/config.yml tunnel ingress validate
    sudo cloudflared service install
    systemctl status cloudflared --no-pager
    ```

    - route dns : 도메인 → 터널로 가는 CNAME 기록을 자동으로 만듦 (터널을 가리키는 CNAME 기록을 두 개 만듦.)
        - DNS 기록 종류
            - A : 이름 → IP (ihaewon.com —> 104.21.x.x)
            - CNAME : 이름 → 다른 이름 (별명) (ihaewon.com → 터널ID.cfargotunnel.com)
                - 나 대신 저 이름에게 물어보라는 뜻
    - ingress validate : 설정 파일 문법 검사
    - service install : systemd에 등록 —> VM 재부팅해도 터널 자동 실행  (3단계 --restart랑 같은 목적)
    - HTTPS 인증서는 Cloudflare가 자동 관리 —> 1단계 proxmox 웹 UI 처럼 경고가 뜨지 않음
        - 외부에 열린 건 사이트 하나 뿐. SSH, proxmox 는 여전히 Tailscale로
    - systemctl status cloudflared --no-pager : cloudflared 서비스가 잘 돌아가고 있는지 확인
        - --no-pager : 결과를 한 번에 쭉 출력하고  끝내기
            - 이걸 붙이지 않으면 결과가 길 때 페이지 넘기는 화면이 떠서 q를 눌러야 빠져나옴
        - status : 상태 보기
        - systemctl :  systemd (리눅스 프로그램 관리자) 한테 명령하는 도구
- Cloudflare 단점
    - Cloudflare가 멈추면 사이트도 같이 멈춤 (의존성)
