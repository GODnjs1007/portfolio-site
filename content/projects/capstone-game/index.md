---
title: "Frozen Stiff · 융합캡스톤디자인 게임"
summary: "팀 게임 프로젝트 Frozen Stiff에서 게임 로직 밖의 인프라를 맡았습니다. 멀티플레이 접속 솔루션 검증, 플레이 기록 수집 서버, 빌드·배포 자동화가 범위입니다."
role: "팀원 · 게임 밖 인프라"
status: "진행 중"
category: "서비스"
stack: ["Godot 4.6", "GodotSteam", "Steamworks", "FastAPI", "Python"]
period: "2026 2학기"
weight: 21
brief:
  why: "게임 로직은 팀원들이 맡고, 저는 접속·기록 수집·빌드처럼 게임 밖에서 서비스를 받쳐주는 인프라를 맡았습니다."
  did:
    - "GodotSteam 설치 경로 확인 (GitHub → Codeberg 이전으로 Asset Library 연동이 끊긴 것 파악)"
    - "엔진 4.6.2에 맞는 GodotSteam 버전 선택 (하위호환 기준 g452)"
    - "Steam 테스트 앱ID 480으로 초기화·로그인·로비 생성 검증"
    - "플레이 기록 수집 서버(FastAPI): 이벤트 저장·목록·다운로드 API, 토큰 인증, run_id 경로 조작 차단"
  verified:
    - "Steam 초기화 true, 연결 성공, 공개 로비 생성 성공 출력 확인"
    - "단일 프로세스 기준 정상 동작. MultiplayerPeer는 4.6 정식 태그 전이라 조건부 지원으로 정리"
    - "Godot 4.6.2 HTTPRequest로 이벤트 10개 전송 → 저장·목록·다운로드 세 요청 모두 200, 10줄 그대로 내려받기"
steps:
  - { name: "GodotSteam 검증", status: "완료", note: "capstone-01-godotsteam" }
  - { name: "플레이 기록 수집 서버", status: "완료", note: "capstone-02-telemetry" }
  - { name: "빌드·배포 자동화", status: "예정" }
next: "다음은 빌드·배포 자동화입니다."
draft: false
---

## 개요

팀 3명(기획 총괄, 팀원 B, 팀원 A) 중 팀원 A로 게임 밖 인프라를 맡고 있습니다. 엔진은 Godot 4.6.2입니다. 코드는 공개하지 않고 진행 과정만 기록합니다.

<!-- 작성 틀: 선택한 이유 / 배운 점 은 직접 작성 -->
