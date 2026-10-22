# 문구 점검 결과

`python3 scripts/check_copy.py`로 다시 만들 수 있다. 고친 뒤 다시 돌려서 0건이 되는지 확인.

## 1. 깨진 문자 (�) (0건)

없음

## 2. 오타 후보 (노션 원문 포함, 고칠지는 직접 판단) (8건)

- `content/notes/aws-06-terraform/index.md:416` — **바뀜다** → 바뀐다
- `content/notes/aws-08-docker-ecs/index.md:674` — **없앱다** → 없앤다
- `content/notes/aws-08-docker-ecs/index.md:674` — **서브티** → 서브넷
- `content/notes/aws-09-cloudwatch/index.md:73` — **바뀜다** → 바뀐다
- `content/notes/aws-09-cloudwatch/index.md:145` — **곷** → 곧
- `content/notes/aws-01-ec2-nginx/learned.md:9` — **설지** → 설치
- `content/notes/aws-05-alb-asg/learned.md:8` — **트랙픽** → 트래픽
- `content/notes/homelab-03-site-deploy/learned.md:35` — **되도** → 돼도

## 3. AI 말투 후보 (사이트 문구만) (23건)

- `i18n/ko.toml:11` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "이 사이트는 Hugo로 만들어, 제 방 미니PC의 Proxmox VM에서 직접 운영합니다. 상태 표시는 실시간 조회가 아니라 직접 갱신하는 기록입니다."
- `i18n/ko.toml:67` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 확인한 결과"
- `i18n/ko.toml:75` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 표시"
- `i18n/ko.toml:99` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "정리된 과정을 다시 보면서 제가 이해한 내용을 직접 썼습니다. 초록색 박스로 따로 표시했습니다."
- `i18n/ko.toml:125` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 작성"
- `i18n/ko.toml:129` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 쓴 배운 점"
- `i18n/ko.toml:133` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "진행 과정은 실습 내용을 AI와 함께 정리했고, 배운 점은 그걸 보고 제가 이해한 대로 직접 썼습니다."
- `i18n/ko.toml:137` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 정리한 배운 점"
- `i18n/ko.toml:159` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 해본 것"
- `hugo.toml:11` — '~해두었습니다' 반복은 소개문 티가 남
  > intro = "제가 만든 것들이 서로 어떻게 이어지는지 그려두었습니다."
- `hugo.toml:11` — 추상적인 표현. 무엇이 무엇으로 이어지는지 구체적으로
  > intro = "제가 만든 것들이 서로 어떻게 이어지는지 그려두었습니다."
- `content/projects/_index.md:3` — '직접' 반복. 정말 강조할 곳만 남기기
  > summary: "직접 만들고 운영한 것들. 분류와 연결 관계로 볼 수 있습니다."
- `content/projects/aws-infra/index.md:14` — '직접' 반복. 정말 강조할 곳만 남기기
  > why: "콘솔에서 서버 한 대를 띄우는 것부터 시작해, 서버를 늘리고 코드로 만들고 컨테이너로 옮기고 감시하는 과정을 한 단계씩 직접 해봤습니다."
- `content/projects/homelab/index.md:15` — '직접' 반복. 정말 강조할 곳만 남기기
  > why: "AWS에서 매니지드 서비스가 대신 해주던 서버, 네트워크, 접속 관리, 배포를 직접 구성해보면서 그 서비스들이 무엇을 대신하는지 확인하려고 시작했습니다."
- `content/projects/portfolio-site/index.md:3` — '직접' 반복. 정말 강조할 곳만 남기기
  > summary: "Hugo로 만든 정적 사이트를 홈랩 VM의 Docker Nginx 컨테이너에서 직접 운영합니다. 지금 보고 계신 페이지입니다."
- `content/projects/portfolio-site/index.md:15` — '직접' 반복. 정말 강조할 곳만 남기기
  > why: "만든 것과 겪은 문제를 한곳에 쌓아두고, 그 사이트 자체도 직접 운영하는 서버 위에 올리려고 만들었습니다."
- `content/projects/portfolio-site/index.md:33` — '~해두었습니다' 반복은 소개문 티가 남
  > 배포 과정은 홈랩 3단계 기록과 같은 작업이라, 자세한 내용은 그 기록에 모아두었습니다.
- `content/projects/yeoulmok/index.md:15` — 영어식 줄표(em dash). 한국어 문장에선 쉼표나 마침표로
  > - "두 단계 경보 설계 — 상류 1시간 누적 강수량 기준 초과 시 사전 경보, 하류 직전 30분 수위 상승폭 기준 초과 시 즉시 경보"
- `content/projects/yeoulmok/index.md:20` — 영어식 줄표(em dash). 한국어 문장에선 쉼표나 마침표로
  > - "쓸 공공데이터 조사 — 한강홍수통제소 수위·유량·댐 방류, 기상청 레이더강수량, 산림청 산악기상"
- `content/projects/yeoulmok/index.md:24` — 영어식 줄표(em dash). 한국어 문장에선 쉼표나 마침표로
  > - "대상 지역을 강원 영서권으로 좁힘 — 강릉은 동해안 수계라 한강홍수통제소 관측망 밖인 것 확인"
- `content/projects/yeoulmok/index.md:25` — 영어식 줄표(em dash). 한국어 문장에선 쉼표나 마침표로
  > - "도달시간을 공식으로 못 박지 않기로 함 — 소양강 중권역에 6개 공식을 적용하면 10~46시간까지 벌어진다는 선행연구 확인"
- `content/notes/_index.md:3` — '직접' 반복. 정말 강조할 곳만 남기기
  > summary: "AWS와 홈랩을 직접 구축하면서 단계별로 남긴 실습 로그입니다."
- `content/learned/_index.md:3` — '직접' 반복. 정말 강조할 곳만 남기기
  > summary: "각 단계를 마치고 제가 직접 정리한 배운 점만 모았습니다. 진행 과정은 기록에, 이해한 내용은 여기에 있습니다."

## 4. [작성 필요] 남은 곳 (0건)

없음

## 5. 옮기지 못한 이미지 (0곳)

