# 디자인 시안 인계 (design/site-structure)

## 이번 작업 결과
- `AGENTS.md`: 사이트 목적, 기술 제약, 콘텐츠 사실성, 디자인 원칙, 검증, 배포 제한
- `docs/portfolio-plan.md`: 프로젝트 9개 분류·상태·공개 범위와 할 일
- `design-previews/`: 실제 사이트와 분리된 HTML/CSS 시안 3개
  - `index.html` 비교 인덱스
  - `a-magazine/` A 기술 매거진 (홈 + 홈랩 상세)
  - `b-system-map/` B 시스템 지도 (홈 + 홈랩 상세)
  - `c-workshop/` C 엔지니어 작업실 (홈 + 홈랩 상세)
  - `screenshots/` 1440px·390px 전체 페이지 스크린샷 14장
- 실제 사이트의 `content/`, `layouts/`, `assets/`, `static/`, `hugo.toml`은 바꾸지 않았다.

## 여는 방법
- 저장소를 받은 뒤 `design-previews/index.html`을 브라우저로 직접 연다. 서버 불필요.
- 글꼴은 Google Fonts에서 받는다. 오프라인이면 시스템 글꼴로 대체된다.

## 시안별 차이
| | A 기술 매거진 | B 시스템 지도 | C 엔지니어 작업실 |
|---|---|---|---|
| 홈 구조 | 표지 문장 + 커버 스토리 1 + 옆 기사 2 | 분류 3열 지도(홈랩 안에 VM) + 같은 내용의 표 | 왼쪽 고정 소개·분류 + 월별 작업 일지 |
| 탐색 | 위에서 아래로 읽기 | 관계를 따라 이동, 표로도 가능 | 시간순 스크롤 |
| 상세 | 고정 요약 + 긴 본문 | 접속 경로 도면 + 진행 단계 사이드 | 노트 한 장, 서버 행 펼치기 |
| 맞는 경우 | 글 중심, 대표작 소수 | 프로젝트 간 연결이 핵심 | 기록이 계속 쌓일 때 |

## 추천: B 시스템 지도
- AWS → 홈랩 → 그 위의 서비스로 이어지는 흐름이 이 포트폴리오의 핵심 이야기이고, 인프라 직무에 가장 직접적으로 보인다.
- 지도만으로는 접근성이 떨어질 수 있어 같은 내용을 표로도 제공한다.
- 대안: B의 홈 + C의 기록 목록(월별 일지)을 섞는 것도 가능.

## 확인한 것 / 못한 것
- 확인: 7개 페이지 × 1440·390px 렌더링, 가로 넘침 없음, `hugo` 빌드 결과에 `design-previews` 미포함
- 못한 것: 실제 기기 터치 테스트, 스크린리더 테스트, Lighthouse 측정

## 다음 단계 (시안 선택 후)
1. 선택한 시안을 `layouts/` 오버라이드 + `assets/css/extended/`로 옮긴다 (PaperMod 원본 수정 금지).
2. `content/projects/<slug>/index.md` 구조로 프로젝트 3개(홈랩, AWS, 이 사이트)부터 옮기고, 나머지는 `draft: true`.
3. 기존 `/posts/proxmox-homelab/` 주소는 `aliases`로 유지.
4. `[작성 필요]` 칸(배운 점, AWS 기간, 이력서)은 직접 작성.
5. VM 배포는 사용자가 `git pull` + `hugo`로 직접.

---

# 2차: B 시안 실제 적용 (design/apply-b)

## 한 것
- 노션 실습 로그 12개 단계(AWS 1~9, 홈랩 1~3)를 `content/notes/<slug>/index.md`로 옮김. 규칙: `docs/notion-import-spec.md`
  - 문장은 노션 원문 그대로. 오타도 그대로라 직접 고칠 것
  - 민감정보 치환: Tailscale·내부·퍼블릭 IP, 계정 ID, 리소스 ID, 계정명, ALB/RDS 주소, 산학 VM 이름(ecg→산학 VM)
  - 이미지는 노션 파일 서버 접근이 막혀 못 옮김. 자리에 `<!-- 이미지: 설명 -->` 주석만 있음 (총 약 110곳)
  - AWS 10단계는 노션 페이지가 비어 있어 기록 없음
  - date는 노션 수정일 기준이라 실제 작업일과 다를 수 있음
- 프로젝트: `content/projects/` 공개 3개(AWS, 홈랩, 이 사이트) + 초안 6개(`draft: true`, 빌드에서 제외)
- 프로젝트 상세 맨 위 "30초 요약"(왜 / 내가 한 일 / 직접 확인한 결과), 진행 단계 → 기록 링크, 관련 기록 목록
- 소개 페이지: 역량 → 근거 기록 표
- 기록 페이지: 프로젝트별 단계 목록 + 트러블슈팅 사례 태그
- 레이아웃: `layouts/`(baseof, home, projects/, notes/, about, partials), CSS: `assets/css/extended/site.css`. PaperMod 원본 미수정. PaperMod CSS는 로드하지 않음
- 기존 `/posts/proxmox-homelab/` → `/projects/homelab/`, `/posts/` → `/projects/` 리다이렉트(aliases)
- `hugo.toml`: 메뉴 4개, goldmark unsafe(=details, br 렌더링), locale

## 확인
- `hugo` 빌드 오류 없음(경고 1: PaperMod rss.xml의 deprecated 함수, 테마 원본이라 그대로 둠)
- 초안 6개 public/에 없음, design-previews 없음, 실제 IP·계정 ID 없음
- 1440·390px 가로 넘침 없음. 스크린샷 `docs/screenshots/` (작업 환경에서 Google Fonts가 막혀 기본 글꼴로 찍힘)

## 사용자가 할 일
- 배운 점, 선택한 이유 직접 작성 (프로젝트 front matter `servers.*.learn`에 넣으면 펼치기 칸에 나옴)
- 이미지: 노션에서 내보내 `content/notes/<slug>/`에 넣고 주석 자리를 `![설명](파일명.png)`로 교체
- 소개: 자격·수상·이력서는 확정된 것만 추가
- 배포: VM에서 `git pull` 후 `hugo`
