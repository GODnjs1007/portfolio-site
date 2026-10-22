---
title: "캡스톤 1단계 · GodotSteam 검증"
date: 2026-10-14
projects: ["capstone-game"]
step: 1
summary: "Godot 4.6 환경에서 GodotSteam(Steam 연동 GDExtension)이 실제로 동작하는지, Steam 로그인·로비 생성까지 되는지 확인해 검증 보고서를 쓴다."
tags: ["구축", "트러블슈팅"]
troubleshooting:
  - "GodotSteam이 Asset Library에 안 뜸"
  - "macOS \"앱이 손상되었기 때문에 열 수 없습니다\""
  - "로비 생성 콜백(lobby_created)이 안 옴"
draft: false
---

## 목표

Godot 4.6 환경에서 GodotSteam(Steam 연동 GDExtension)이 실제로 동작하는지, Steam 로그인·로비 생성까지 되는지 확인해 검증 보고서를 쓴다.

## 진행 과정

### A. GodotSteam 설치 찾기

- Asset Library에서 GodotSteam 검색이 안 돼서 Codeberg Releases 페이지([codeberg.org/godotsteam/godotsteam](https://codeberg.org/godotsteam/godotsteam))에서 빌드 파일을 직접 받음 (트러블슈팅 1번)
  - Asset Library: Godot 에디터 안에서 애드온을 검색·설치하는 기능. 각 애드온의 저장소 주소를 등록해두고 거기서 받아옴
  - 저장소: 코드와 배포 파일을 모아두는 곳 (GitHub, Codeberg)
  - archived: 관리 종료, 읽기 전용 상태
  - Releases: 완성본 파일을 버전별로 올려두는 곳

### B. 버전 선택

- Godot 4.6.2에 맞는 빌드로 g452 선택. Releases에는 macos-g452(4.5.2 이상 호환), macos-g472(4.7.2 이상 호환) 두 종류만 있었음
  - GDExtension: Godot 엔진에 기능을 붙이는 확장 모듈. `compatibility_minimum` 값으로 "이 엔진 버전 이상이면 돌아간다"는 최소 기준을 갖고 빌드됨
  - 하위호환: 최소 기준이 엔진 버전보다 낮으면 로딩됨. 높으면 로딩 실패
- g452(4.5.2 기준)는 4.6.2에서 돌고, g472(4.7.2 기준)는 안 돎

### C. macOS Gatekeeper 차단 돌파

- 직접 받은 Steam 설치 파일을 macOS가 막아서 Homebrew로 설치함: `brew install --cask steam --force` (트러블슈팅 2번)
  - Gatekeeper: 애플이 서명(확인)하지 않은 프로그램을 막는 macOS 보안 기능
  - 격리 속성: 인터넷에서 받은 파일에 붙는 표시. 붙어 있으면 더 엄격하게 검사받음
  - Homebrew: 맥에서 터미널 명령으로 프로그램을 설치하는 도구. 검증된 경로로 설치해서 차단을 피함
  - `--cask`: 창이 있는 앱(Steam 같은)을 설치하는 옵션

### D. Steam 초기화·로비 생성 검증

- 테스트용 앱ID 480을 `steam_appid.txt`에 적고, 아래 스크립트로 Steam 로그인부터 로비 생성까지 확인함
  - 앱ID 480: 밸브가 개발자 테스트용으로 공개한 앱(Spacewar)

```gdscript
extends Node

func _ready():
	var init_result = Steam.steamInit()
	print("Steam 초기화 결과: ", init_result)

	if Steam.isSteamRunning():
		print("Steam 연결 성공! 로그인 계정: ", Steam.getPersonaName())
	else:
		print("Steam 연결 실패")
		return

	Steam.lobby_created.connect(_on_lobby_created)
	Steam.createLobby(Steam.LOBBY_TYPE_PUBLIC, 4)

func _on_lobby_created(connect_result, lobby_id):
	if connect_result == 1:
		print("로비 생성 성공! 로비 ID: ", lobby_id)
	else:
		print("로비 생성 실패, 코드: ", connect_result)

func _process(delta):
	Steam.run_callbacks()
```

- 스크립트에 쓴 함수
  - `Steam.steamInit()`: Steam 클라이언트와 연결 시작
  - `Steam.isSteamRunning()` / `Steam.getPersonaName()`: 로그인 여부·계정명 확인
  - `Steam.createLobby()`: 멀티플레이용 로비(방) 생성 요청
  - `lobby_created`: 로비 생성이 끝나면 오는 콜백(비동기 알림)
  - `Steam.run_callbacks()`: Steam 쪽에서 일어난 일을 게임에 넘겨줌. 매 프레임 불러야 해서 `_process()`에 넣음 (트러블슈팅 3번)
- 결과: `Steam 초기화 결과: true` / `로그인 계정: <Steam 계정>` / `로비 생성 성공! 로비 ID: <로비 ID>`
- 단일 프로세스 기준으로 GodotSteam은 Godot 4.6에서 정상 동작
  - MultiplayerPeer: 멀티플레이 연결 전용 모듈. 공식 태그가 Godot 4.5.1까지라 4.6은 조건부 지원

## 트러블슈팅

### 1. GodotSteam이 Asset Library에 안 뜸

- **증상**: Godot 에디터 내장 Asset Library에서 "GodotSteam" 검색 결과 0건
- **확인한 것**: 인터넷 연결은 정상, 다른 애드온은 검색됨
- **원인**: GodotSteam이 2026-09-04에 GitHub에서 Codeberg로 저장소를 이전하면서 GitHub 저장소가 archived 처리됨 → Asset Library 색인이 끊김
- **해결**: Asset Library를 거치지 않고 [codeberg.org/godotsteam/godotsteam](https://codeberg.org/godotsteam/godotsteam) Releases 페이지에서 직접 다운로드
- **재발 방지**: 특정 애드온이 Asset Library에 안 보이면, 그 프로젝트의 공식 저장소가 이전·보관(archive) 상태인지부터 확인

### 2. macOS "앱이 손상되었기 때문에 열 수 없습니다"

- **증상**: GodotSteam 에디터 앱, Steam 설치 파일을 열 때마다 동일한 Gatekeeper 차단 에러 반복
- **확인한 것**: 우클릭 → 열기, 시스템 설정 → 보안에서 "그래도 열기" 허용 옵션까지 시도했지만 일부는 통과 안 됨
- **원인**: 미서명(또는 서명이 검증되지 않은) 바이너리를 Gatekeeper가 차단
- **해결**:
  1. `xattr -cr <경로>` 로 격리 속성 제거 시도
  2. `sudo spctl --master-disable` 시도 (최신 macOS는 시스템 설정에서 "모든 곳(Anywhere)" 허용을 별도로 확인해줘야 함)
  3. 최종적으로 Homebrew cask로 재설치: `brew install --cask steam --force` (기존에 깨진 /Applications/Steam.app가 남아있어 `--force` 필요) → 성공
- **재발 방지**: brew로 설치 가능한 앱은 직접 다운로드보다 brew cask를 먼저 시도

### 3. 로비 생성 콜백(lobby_created)이 안 옴

- **증상**: `Steam.createLobby()` 호출 후 `Steam.steamInit()`과 로그인은 성공했는데 `lobby_created` 콜백이 전혀 발생하지 않음
- **확인한 것**: 코드 자체의 로직 오류는 없어 보임 (콜백 연결 코드 정상)
- **원인**: GodotSteam은 Steamworks의 비동기 이벤트를 받으려면 매 프레임 `Steam.run_callbacks()`를 호출해줘야 하는데, 이 호출이 스크립트에 없었음
- **해결**: `_process(delta)` 함수를 추가하고 그 안에서 `Steam.run_callbacks()` 호출 → 즉시 로비 생성 성공 확인
- **재발 방지**: Steamworks(또는 GodotSteam) 콜백 기반 기능을 쓸 때는 항상 pump 로직(`run_callbacks` 같은)이 매 프레임 돌고 있는지 먼저 확인
