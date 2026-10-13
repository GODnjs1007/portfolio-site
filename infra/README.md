# infra

홈랩(Proxmox 미니PC) 운영 설정. 사이트 빌드(Hugo)와는 무관한 폴더.

## 서버

| 이름 | 역할 |
|---|---|
| proxmox | Proxmox VE 호스트 |
| portfolio | 포트폴리오 사이트(Hugo, Docker Nginx, Cloudflare Tunnel) + 통합 모니터링 |
| paper | 논문 실측 수집 (cron) |
| ecg | 산학 테스트 서버 (기업 PC 오면 종료 예정) |

## 통합 모니터링 (`infra/monitoring/`)

```
portfolio VM
 └ Prometheus + Grafana (:3000)
      ↑ 15초마다 수집 (Tailscale)
 ┌────┼─────────┬─────────┐
portfolio  paper     ecg      proxmox
node-exp   node-exp  node-exp node-exp
cAdvisor
```

- 중앙 한 곳에서 모든 서버를 봄. 다른 서버엔 node-exporter만 설치
- 중앙은 항상 켜두는 portfolio VM에 둠 (ecg는 곧 끌 예정)
- 알림 규칙 4개: 서버다운(2분), 디스크 85%, 메모리 90%, CPU 90%(10분). 지금은 `:9090/alerts`에서 확인만

### 설치

1) paper, ecg, proxmox 호스트에 node-exporter (각 서버에서)
```bash
sudo apt update && sudo apt install -y prometheus-node-exporter
curl -s localhost:9100/metrics | head -3     # 숫자가 나오면 성공
```

2) `infra/monitoring/prometheus/targets.yml`에 각 서버 Tailscale IP 넣기

3) portfolio VM에서 중앙 띄우기
```bash
cd ~/portfolio-site/infra/monitoring
GRAFANA_PASSWORD=비밀번호 docker compose up -d
```

4) 확인
- `http://100.117.220.8:9090/targets` → node 4개 모두 UP
- `http://100.117.220.8:3000` → Dashboards → Homelab → 홈랩 서버 전체

### 서버 추가
`targets.yml`에 한 줄 추가하면 30초 안에 반영 (재시작 불필요)

### 컨테이너 이름 대조
cAdvisor가 컨테이너 ID 앞 12자리로 보여줌 → `sh infra/monitoring/container_names.sh`
