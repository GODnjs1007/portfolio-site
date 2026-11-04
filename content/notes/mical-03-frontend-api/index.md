---
title: "MiCAL 3단계 · 화면과 API 연결"
date: 2026-11-04
projects: ["web-project"]
step: 3
summary: "(진행 중) 프론트 팀이 만든 새 프로토타입을 서버에 올리고, 2단계에서 DB에 넣은 실제 일정(742건)이 프로토타입 캘린더에 뜨게 연결한다. 프론트 팀 코드는 최소로만 건드린다."
tags: ["JavaScript", "API 연결", "Nginx", "트러블슈팅", "진행 중"]
troubleshooting:
  - "주간 보기에서 일정이 세로 글씨로 찌그러짐"
draft: false
---

## 목표

프론트 팀이 만든 새 프로토타입을 서버에 올리고, 2단계에서 DB에 넣은 실제 일정(742건)이 프로토타입 캘린더에 뜨게 연결한다. 프론트 팀 코드는 최소로만 건드린다. (11/10 진행 회의 2 준비 사항 중 "프론트와 연결")

## A. 새 프로토타입 배포

- 프론트 팀원이 만든 새 프로토타입(정적 HTML·CSS·JS 11개)을 `frontend/`에 올림 (PR #4)
  - 월간·주간 보기, 분류 필터, 일정 상세, 개인 일정 등록, 프로필·테마, 공지사항 화면
  - 일정 데이터는 비어 있고(`events = []`), 개인 일정은 브라우저 localStorage에만 저장하는 상태
  - localStorage: 브라우저 안에만 저장되는 저장소. 다른 기기나 다른 사람과 공유 안 됨
- 기존 A~D 색상 시안은 `frontend/archive/`로 옮김 (프로토타입 설명서 `PROTOTYPE.md`에 적힌 대로)
  - `git mv`로 옮겨서 파일 이력이 그대로 이어짐
- 루트 주소(`calendar.ihaewon.com`)로 들어오면 `prototype.html`로 바로 가게 `index.html`을 이동용으로 만듦

```html
<meta http-equiv="refresh" content="0; url=prototype.html">
```

- nginx는 주소에 파일 이름이 없으면 `index.html`을 보여줌
- meta refresh: 페이지가 열리자마자 다른 주소로 이동시키는 HTML 설정
- 반영은 VM에서 `git pull`만 하면 됨 (nginx가 `frontend/` 폴더를 그대로 읽음)

## B. 일정 API 연결

- 프로토타입 캘린더에 실제 DB 일정(`/api/events/`)이 뜨게 연결 (PR #4)
- 연결 코드는 `prototype-api.js` 파일 하나로 따로 둠 → 프론트 팀 파일은 2줄만 수정
  - `prototype.html`: 스크립트 태그 1줄 추가 (데이터 파일 다음, 캘린더 코드 앞)
  - `prototype.js`: 서버 일정을 받으면 다시 그리는 줄 1줄 추가
- 동작 순서

```txt
페이지 열림
→ prototype-api.js가 /api/events/ 요청
→ nginx가 Django로 전달 → PostgreSQL에서 일정 742건 조회 → JSON으로 응답
→ 백엔드 형식을 프로토타입 형식으로 바꿔서 CalendarModel.events에 넣음
→ 'mical:events-updated' 이벤트 보냄 → prototype.js가 다시 그림
```

```javascript
fetch('/api/events/')                       // 서버에 일정 요청
  .then(res => res.json())                  // JSON → 배열
  .then(list => {
    M.events.push(...list.flatMap(convert)); // 형식 바꿔서 넣기
    window.dispatchEvent(new Event('mical:events-updated'));  // 다시 그려달라고 알림
  })
```

```javascript
// prototype.js에 추가한 1줄
window.addEventListener('mical:events-updated', render);
```

- fetch: 화면에서 서버에 요청 보내는 함수
- CustomEvent(이벤트 보내기): 파일끼리 직접 함수를 부르지 않고 "일정 바뀌었다"고 신호만 보내는 방식. 프론트 코드를 거의 안 건드릴 수 있음
- defer: HTML을 다 읽은 뒤 스크립트를 적힌 순서대로 실행하는 설정
- 백엔드 → 프로토타입 형식 변환

| 백엔드 | 프로토타입 |
| --- | --- |
| `start_at` "2026-11-05T14:00:00+09:00" | `date` "2026-11-05", `start` 14 (시각을 숫자로) |
| `end_at` | 같은 날이면 `end`, 다른 날이면 `until` |
| 학사일정 (학교) | 학교 공통 일정 |
| 학사일정 (소웨·경영) | 학과 일정 |
| 장학금 · 공모전 · 비교과 | 행사 · 커뮤니티 |
| `url` | 설명란에 "원문: 주소" (링크 버튼은 아직 없음) |

- 7일이 넘는 기간 일정(예: 비교과 신청 기간)은 매일 칸을 채우지 않게 `[시작]`, `[마감]` 두 개로 나눠서 넣음
- 서버가 없거나 요청이 실패하면 아무것도 안 넣고 빈 캘린더로 둠 → 프론트 팀은 파일만 열어도 화면 확인 가능
- 테스트: 가짜 데이터를 만든 임시 서버로 월간·주간 화면을 확인한 뒤 올림
- 참고: 프로토타입은 월간 보기에서 오늘 이전 일정을 숨기게 만들어져 있음 (버그 아님)

## 트러블슈팅

### 1. 주간 보기에서 일정이 세로 글씨로 찌그러짐

- 증상 : 실제 데이터를 붙이고 주간 보기를 열었더니, 같은 시간대 일정들이 글자 하나씩 세로로 나올 정도로 좁아짐
- 확인한 것
  - 비교과(전공탐색박람회 등)는 같은 날 같은 시간에 10개 넘게 걸려 있음
  - 프로토타입은 겹치는 일정 수만큼 칸을 똑같이 나눔 → 10개면 하루 칸을 10등분
  - 가짜 데이터(일정 몇 개)로 테스트할 땐 안 보였음
- 원인
  - 프로토타입이 일정이 많은 경우를 고려하지 않음 (빈 데이터로 만들어짐)
  - 테스트를 실제처럼 많은 데이터로 하지 않음
- 해결 (PR #5)
  - 시간 일정: 같은 시간에 겹치는 건 최대 2개만 그리고 나머지는 "+N개 더" 버튼
  - 종일 일정: 최대 2개 + "+N개 더"
  - "+N개 더"를 누르면 그날 일정 목록 창이 뜨게 함 (월간 보기에 있던 창 재사용)
  - 버튼을 누를 때 일정 만들기 드래그가 같이 시작되던 것도 막음

```javascript
const WEEK_MAX = 2;   // 한 시간대에 그릴 최대 개수
for (const e of sorted)
  (kept.filter(k => k.start < e.end && k.end > e.start).length < WEEK_MAX ? kept : hidden).push(e);
// 겹치는 게 2개 미만이면 그리고, 아니면 숨김 목록으로
```

- 재발 방지
  - 화면 테스트는 실제와 비슷한 양(같은 시간 10개 이상, 종일 5개 이상)으로 하기
  - 프론트 팀에 "일정이 많을 때 화면"을 디자인 기준에 넣어달라고 공유

## 남은 작업

- [ ] 분류 매칭 확정 (장학금·공모전·비교과를 "행사·커뮤니티"로 묶을지, 따로 둘지)
- [ ] 상세 화면에 원문 링크 버튼 (프론트)
- [ ] 회원가입·로그인 화면 연결 (회원가입 때 런어스 URL 받기)
- [ ] 개인 일정을 localStorage 대신 서버(`/api/events/`)에 저장
