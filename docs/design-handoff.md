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

## 지도 바로가기 상자 (alsoOn)

- 카드는 한 칸에만 놓이고(`category` 또는 `runsOn`), 다른 칸에도 보여야 하면 front matter `alsoOn: { host, label, title }`로 바로가기 상자를 만든다.
- 예: 논문 ② 카드는 연구 칸에 두고, 홈랩 밑에 `vm 102` 바로가기 상자로 같은 페이지를 연결 (`layouts/_partials/node-ref.html`).

## 홈: 설계 도면 (2026-11-01, `home-blueprint` 브랜치)

- 피그마 시안 3개(A 진한 첫 화면 / B 잡지형 / C 설계 도면) 중 C를 골랐다. 시안: https://www.figma.com/design/TrbTWjRQoO7l8EljxyfyQf
- 홈 전체를 테두리 있는 도면 한 장(`.sheet`)으로 묶었다. 순서: 위 눈금(A~F) → 첫 화면(제목 + 오른쪽 표제란) → 일하는 방식 띠 → 프로젝트 지도 → 쓰는 도구(부품표).
- 새 부분 템플릿: `layouts/_partials/title-block.html`, `principles.html`, `bom.html`. 내용은 모두 `content/about.md`의 `profile`에서 가져온다. 소개 페이지의 `profile-card.html`은 그대로.
- 표제란의 '최종 수정'은 `site.Lastmod`(가장 최근 글 날짜)로 자동 표시된다.
- 공식 frontend-design 스킬 기준으로 일반적인 AI 디자인 습관은 뺐다: 순서가 아닌 강점에 01/02 번호, 영문 대문자 꼬리표, 부품표 항목 번호.
- 확인: `hugo` 빌드 오류 없음, 1440px·390px 가로 넘침 없음. 모바일 소개 영역 높이 약 1,540px → 약 680px.
- 2차(같은 날): 사이트 색을 청사진 계열로 바꿨다(`:root`의 `--ink` 남청, `--accent` 빨간펜, `--bp*` 청사진 파랑). 홈 첫 화면은 청사진 모눈, 지도 칸은 모눈종이, 쓰는 도구는 청사진 패널 + 브랜드 색 로고 타일.
- 로고 색은 `data/brand.toml`(Simple Icons 공식 색). 새 아이콘을 추가하면 여기에 색도 한 줄 넣는다. 템플릿은 `site.Data`를 쓴다(구버전 Hugo 호환. 0.156+에서는 deprecated 경고만 뜸).
- 3차: 지도의 프로젝트별 색 띠(`tone`)를 없애고 VM 번호표로 바꿨다. 프로젝트 카드에 `서버 → vm 104`, VM 상자에 `↔ 팀 여울목`이 붙고, 누르면 지도 안의 짝 카드로 이동해 빨간 테두리로 강조된다(`:target`). 문구는 `alsoOn.via`(없으면 "서버"). `tone`은 front matter에 남아 있지만 더 이상 쓰지 않는다.
- 4차: 짝 표시 보강. 같은 VM을 쓰는 프로젝트 카드와 VM 상자 오른쪽 위에 같은 번호 동그라미(도면 상세 참조 표시)를 찍고, VM 번호마다 정해진 색(`layouts/_partials/vm-color.html`, 6색)으로 동그라미·번호표 테두리를 칠한다. 한쪽에 마우스나 키보드 포커스가 가면 짝도 같은 색 테두리로 강조된다(`map.html` 끝의 `<style>`, `:has`). 사용 종료 VM은 회색 점선 동그라미.
- 소개 페이지 기술 칸도 홈과 같은 청사진 패널·브랜드 색 타일로 바꿨다(공용 `stack-panels.html`).
- 홈 맨 위 A~F 눈금은 가리키는 곳이 없는 장식이라 지웠다.
- 5차(덜어내기): 지도에 요소가 몰려 산만해서 번호 동그라미와 모눈종이 바탕을 지웠다. 짝 색은 번호표 칩 하나에만 채운다(흰 글자 대비 4.5:1 이상으로 6색 조정). 관계 칩은 회색, 기술 패널·타일은 각지게. 모눈은 첫 화면에만 남긴다.
- 6차: 홈 순서를 첫 화면 → 프로젝트 지도 → 직접 쓴 배운 점 → 쓰는 도구로 바꿨다. '직접 쓴 배운 점'(`learned-home.html`)은 일하는 방식 두 문장을 머리말로 두고, 공개 프로젝트마다 가장 최근 learned.md를 하나씩(최대 4개) 보여준다. 노션에서 배운 점을 추가하면 자동으로 바뀐다. 기존 `principles.html`은 삭제.
- 7차: 홈 배운 점 카드는 21편을 모두 HTML에 넣고, 새로고침마다 작은 스크립트가 무작위로 4편을 고른다(한 프로젝트 최대 2편, `data-show`/`data-per`). 스크립트가 안 돌면 프로젝트마다 최근 1편. 프로젝트 상세에는 제목 아래 '배운 점 n편 바로가기'와 오른쪽 맨 위 '직접 쓴 배운 점' 상자를 추가했다(배운 점이 있는 프로젝트만).
