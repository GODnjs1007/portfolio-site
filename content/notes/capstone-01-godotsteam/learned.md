---
title: "배운 점"
---

### A. GodSteam 설치 찾기

- 목적 : GodSteam을 프로젝트에 설치하려하는데 Godot 에디터 안에서 검색이 되지 않음
  - 왜 안 되는지 원인 찾고 우회해서 설치
- 설명
  1. Godot 에디터 내장 애셋 라이브러리
     - Asset Library : 에디터 안에서 애드온 검색 및 설치하는 기능
       - 애드온 파일은 없고 저장소 주소만 등록
  2. 검색이 되지 않은 이유
     - GodSteam이 저장소를 GitHub → Codeberg로 옮김
     - 옛 깃허브 저장소 archived → 등록 주소가 끊김
       - 저장소 : 코드와 배포 파일을 모아두는 곳
       - archived : 관리 종료, 읽기 전용
  3. 우회 설치
     - Codeberg Releases에서 빌드 파일 직접 다운
       - releases : 완성본 파일을 버전별로 올려두는 곳

### B. 버전 선택

- 목적 : Godot 4.6.2에 맞는 GodotSteam 빌드 고르기
  - 4.6.2 딱 맞는 버전이 없음
- 설명
  1. 최소 기준
     - GDExtension : Godot에 기능을 붙이는 확장 모듈
     - compatibility\_minimum : 이 엔진 버전 이상이면 돌아간다는 최소 기준
  2. 하위호환
     - 최소 기준 \< 엔진 버전 → 로딩됨
     - 최소 기준 > 엔진 버전 → 로딩 실패
  3. 결정 : g452
     - g452(4.5.2 이상) → 4.6.2에서 돎
     - g472(4.7.2 이상) → 4.6.2에서 안 돎

### C. macOS Gatekeeper 차단 돌파

- 목적 : Steam 설치
  - 직접 받은 설치 파일을 macOS가 계속 막음
- 설명
  1. 막힌 이유
     - Gatekeeper : 애플이 서명 안 한 프로그램을 막는 macOS 보안 기능
     - 격리 속성 : 인터넷에서 받은 파일에 붙는 표시. 더 엄격하게 검사받음
  2. Homebrew로 설치
     - brew install --cask steam --force
       - Homebrew : 터미널 명령으로 프로그램 설치하는 도구
       - -cask : 창 있는 앱 설치 옵션
       - -force : 기존에 깨진 Steam.app 덮어쓰기

### D. Steam 초기화·로비 생성 검증

- 목적 : Steam 로그인과 로비 생성까지 실제로 되는지 코드로 확인
- 설명
  1. 테스트 준비
     - 앱ID 480을 steam\_appid.txt에 적음
       - 앱ID 480 : 밸브가 테스트용으로 공개한 앱(Spacewar)
  2. 스크립트 흐름 : 초기화 → 로그인 확인 → 로비 생성 요청 → 완료 콜백 받기
     - steamInit() : Steam과 연결 시작
     - createLobby() : 로비(방) 생성 요청
     - lobby\_created : 로비가 만들어지면 오는 알림 (콜백)
     - run\_callbacks() : Steam 알림을 게임에 넘겨줌. 매 프레임 불러야 해서 \_process()에 넣음
  3. 결과
     - 초기화 true, 로그인 성공, 로비 생성 성공
     - 혼자 실행 기준으로 Godot 4.6에서 정상 동작
       - MultiplayerPeer : 멀티플레이 연결 전용 모듈. 4.5.1까지만 공식 지원이라 4.6은 조건부
