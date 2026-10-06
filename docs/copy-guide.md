# 문구 고치는 곳 안내

화면에 보이는 글자가 어느 파일에서 오는지 정리한 표. 고친 뒤 `python3 scripts/check_copy.py`로 점검한다.

| 화면에 보이는 것 | 고치는 파일 |
|---|---|
| 홈 맨 위 큰 제목, 그 옆 소개 두 줄 | `hugo.toml`의 `intro`, `introSub` |
| 메뉴 이름(홈/프로젝트/기록/소개) | `hugo.toml`의 `[[menu.main]]` |
| 버튼·표 제목·안내 문구·바닥글 등 고정 문구 전부 | `i18n/ko.toml` |
| 프로젝트 카드·상세의 제목, 요약, 역할, 상태, 기간 | `content/projects/<이름>/index.md` 맨 위 설정 |
| 프로젝트 상세의 30초 요약(왜 / 내가 한 일 / 확인한 결과) | 같은 파일의 `brief:` |
| 프로젝트 진행 단계 목록, 다음 작업 | 같은 파일의 `steps:`, `next:` |
| 프로젝트 상세 본문(개요 등) | 같은 파일의 `---` 아래 |
| 기록 페이지 상단 소개 | `content/notes/_index.md` |
| 기록 글 본문(진행 과정, 트러블슈팅) | `content/notes/<기록>/index.md` |
| 기록 글의 "직접 정리한 배운 점" | `content/notes/<기록>/learned.md` |
| 배운 점 모아보기 상단 소개 | `content/learned/_index.md` |
| 소개 페이지 첫 문단, 역량 표 | `content/about.md` 맨 위 설정의 `intro`, `skills:` |

## 고칠 때 기준
- 노션에서 옮긴 기록 글·배운 점은 내가 쓴 원문이다. 오타만 고치고 말투는 그대로 둔다.
- 사이트 문구(위 표의 `hugo.toml`, `i18n/ko.toml`, 프로젝트 설정, 소개)는 AI가 쓴 초안이라 내 말투로 바꾼다.
- 성과·수치·결과는 확인된 것만 쓴다.
