---
title: "홈랩 4단계 · 도메인·HTTPS로 외부 공개"
date: 2026-10-12
projects: ["homelab"]
step: 4
summary: "Tailscale 사설망에서만 보이던 포트폴리오 사이트를 도메인(ihaewon.com)으로 외부에 공개한다. 공유기 포트는 열지 않고 Cloudflare Tunnel로 연결하며, HTTPS를 적용한다."
tags: ["구축", "네트워크", "보안"]
troubleshooting: []
draft: false
---

## 목표

Tailscale 사설망에서만 보이던 포트폴리오 사이트를 도메인([ihaewon.com](https://ihaewon.com))으로 외부에 공개한다. 공유기 포트는 열지 않고 Cloudflare Tunnel로 연결하며, HTTPS를 적용한다.

## 구성

```plain text
방문자 → https://ihaewon.com → Cloudflare(HTTPS·DNS) ⇄ 터널 ⇄ cloudflared(portfolio VM) → localhost:80 → Nginx 컨테이너
```

- VM이 Cloudflare 쪽으로 **먼저 연결을 열어두는** 방식(아웃바운드)이라 집 공유기에 들어오는 포트를 열 필요가 없음
- HTTPS 인증서는 Cloudflare가 자동 관리

## A. 도메인 구매

- Cloudflare Registrar에서 `ihaewon.com` 구매 ($10.46/년, 원가 판매)
  - 자동 갱신 ON → 갱신 놓치면 남이 가져갈 수 있고 이력서 링크가 깨짐
  - 등록자 정보는 영어 주소로 입력. WHOIS 정보는 Cloudflare가 기본으로 가려줌
  - Cloudflare에서 사면 DNS도 자동으로 Cloudflare에 연결됨

## B. cloudflared 설치 (portfolio VM)

```bash
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared
```

- 서명키 → 저장소 추가 → 설치 순서. 서명키는 진짜 Cloudflare 패키지인지 확인하는 용도
- `docker ps`로 사이트 컨테이너가 80번 포트로 열려 있는 것 확인

## C. 터널 생성과 도메인 연결

```bash
cloudflared tunnel login
cloudflared tunnel create portfolio
```

- `login` : 브라우저에서 ihaewon.com 승인 → VM에 인증서(cert.pem) 저장
- `create` : 터널 생성 + 터널 인증 파일(.json) 생성. **.json은 터널 비밀번호라 외부 공유 금지**

설정 파일 `/etc/cloudflared/config.yml`

```yaml
tunnel: <터널 ID>
credentials-file: /etc/cloudflared/<터널 ID>.json
ingress:
  - hostname: ihaewon.com
    service: http://localhost:80
  - hostname: www.ihaewon.com
    service: http://localhost:80
  - service: http_status:404
```

- ingress : 들어온 주소별로 어디로 보낼지 정하는 규칙. 위에서부터 순서대로 확인
- 마지막 줄 : 위에 없는 주소는 404로 거절 (필수)

```bash
cloudflared tunnel route dns portfolio ihaewon.com
cloudflared tunnel route dns portfolio www.ihaewon.com
sudo cloudflared --config /etc/cloudflared/config.yml tunnel ingress validate
sudo cloudflared service install
systemctl status cloudflared --no-pager
```

- `route dns` : Cloudflare DNS에 도메인 → 터널 CNAME 레코드 자동 생성
- `ingress validate` : 설정 파일 문법 검사 → OK
- `service install` : systemd 서비스로 등록 → VM 재부팅 시 터널 자동 실행
- `active (running)` 확인

## D. 검증

- 근로처 컴퓨터(Tailscale 없음, 외부 네트워크)에서 `https://ihaewon.com` 접속 성공

## 남은 작업

- [ ] Hugo `baseURL`을 `https://ihaewon.com/`으로 변경
- [ ] 휴대폰 LTE로 접속 확인
- [ ] BIOS 정전 후 자동 부팅 설정 (사이트가 집 미니PC에서 돌아가므로)
