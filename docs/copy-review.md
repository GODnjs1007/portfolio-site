# 문구 점검 결과

`python3 scripts/check_copy.py`로 다시 만들 수 있다. 고친 뒤 다시 돌려서 0건이 되는지 확인.

## 1. 깨진 문자 (�) (0건)

없음

## 2. 오타 후보 (노션 원문 포함, 고칠지는 직접 판단) (8건)

- `content/notes/aws-06-terraform/index.md:418` — **바뀜다** → 바뀐다
- `content/notes/aws-08-docker-ecs/index.md:676` — **없앱다** → 없앤다
- `content/notes/aws-08-docker-ecs/index.md:676` — **서브티** → 서브넷
- `content/notes/aws-09-cloudwatch/index.md:73` — **바뀜다** → 바뀐다
- `content/notes/aws-09-cloudwatch/index.md:145` — **곷** → 곧
- `content/notes/aws-01-ec2-nginx/learned.md:9` — **설지** → 설치
- `content/notes/aws-05-alb-asg/learned.md:8` — **트랙픽** → 트래픽
- `content/notes/homelab-03-site-deploy/learned.md:31` — **되도** → 돼도

## 3. AI 말투 후보 (사이트 문구만) (17건)

- `i18n/ko.toml:11` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "이 사이트는 Hugo로 만들어, 제 방 미니PC의 Proxmox VM에서 직접 운영합니다. 상태 표시는 실시간 조회가 아니라 직접 갱신하는 기록입니다."
- `i18n/ko.toml:65` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 확인한 결과"
- `i18n/ko.toml:73` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 표시"
- `i18n/ko.toml:113` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 작성"
- `i18n/ko.toml:117` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "이 단계에서 배운 점은 제가 직접 정리했습니다."
- `i18n/ko.toml:121` — '직접' 반복. 정말 강조할 곳만 남기기
  > other = "직접 정리한 배운 점"
- `i18n/ko.toml:143` — '직접' 반복. 정말 강조할 곳만 남기기
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
- `content/projects/sanhak-ecg/index.md:3` — '직접' 반복. 정말 강조할 곳만 남기기
  > summary: "산학 프로젝트 팀장으로 팀을 이끌며 서버·백엔드를 맡고 있습니다. 홈랩 VM 101에 팀 개발 서버를 직접 구축해 운영합니다."
- `content/learned/_index.md:3` — '직접' 반복. 정말 강조할 곳만 남기기
  > summary: "각 단계를 마치고 제가 직접 정리한 배운 점만 모았습니다. 진행 과정은 기록에, 이해한 내용은 여기에 있습니다."

## 4. [작성 필요] 남은 곳 (2건)

- `content/projects/startup-contest/index.md:4` — role: "[작성 필요]"
- `content/projects/startup-contest/index.md:15` — [작성 필요]

## 5. 옮기지 못한 이미지 (110곳)

- `content/notes/aws-02-custom-page/index.md` — 1곳
- `content/notes/aws-03-troubleshooting/index.md` — 14곳
- `content/notes/aws-04-vpc-security/index.md` — 20곳
- `content/notes/aws-05-alb-asg/index.md` — 20곳
- `content/notes/aws-06-terraform/index.md` — 13곳
- `content/notes/aws-07-private-rds/index.md` — 7곳
- `content/notes/aws-08-docker-ecs/index.md` — 19곳
- `content/notes/aws-09-cloudwatch/index.md` — 7곳
- `content/notes/homelab-01-proxmox/index.md` — 1곳
- `content/notes/homelab-02-vm-docker/index.md` — 4곳
- `content/notes/homelab-02-vm-docker/learned.md` — 1곳
- `content/notes/homelab-03-site-deploy/index.md` — 3곳
