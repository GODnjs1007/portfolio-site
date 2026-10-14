---
title: "캡스톤 1단계 · GodotSteam 검증"
date: 2026-10-14
projects: ["capstone-game"]
step: 1
summary: "Godot 4.6 환경에서 GodotSteam(Steam 연동 GDExtension)이 실제로 동작하는지, Steam 로그인·로비 생성까지 되는지 확인해 검증 보고서를 쓴다."
tags: ["트러블슈팅"]
troubleshooting:
  - "GodotSteam이 Asset Library에 안 뜸"
  - "macOS \"앱이 손상되었기 때문에 열 수 없습니다\""
  - "로비 생성 콜백(lobby_created)이 안 옴"
draft: false
---

## 목표

Godot 4.6 환경에서 GodotSteam(Steam 연동 GDExtension)이 실제로 동작하는지, Steam 로그인·로비 생성까지 되는지 확인해 검증 보고서를 쓴다.

## A. GodotSteam 설치 찾기

Godot 내장 Asset Library에서 "GodotSteam" 검색이 0건으로 나왔다.

- **원인**: GodotSteam이 2026-09-04에 GitHub에서 Codeberg([codeberg.org/godotsteam/godotsteam](https://codeberg.org/godotsteam/godotsteam))로 이전하면서, GitHub 저장소가 archived 되고 Asset Library 연동이 깨졌음
- **대응**: Asset Library를 거치지 않고 Codeberg Releases 페이지에서 직접 다운로드

## B. 버전 선택

Release에는 macos-g452(「4.5.2 이상」 호환), macos-g472(「4.7.2 이상」 호환) 두 종류만 있었고, 내 프로젝트 엔진(4.6.2)에 정확히 맞는 버전이 없었다.

- **g452로 결정**: GDExtension은 당기보다 낮은 최소호환버전으로 만든 것은 상위 엔진에서도 로딩된다(하위호환). g472는 요건이 4.6.2보다 높아서 로딩에 실패한다

## C. macOS Gatekeeper 차단 돌파

GodotSteam 에디터 앱과 Steam 설치 파일을 다운로드했을 때 "앱이 손상됨" 에러가 반복됐다.

- xattr -cr, sudo spctl --master-disable 시도했지만 실패
- 최종 해결: Homebrew cask 설치(`brew install --cask steam --force`) — 이전에 깨진 /Applications/Steam.app가 있어서 `--force` 필요했음

## D. Steam 초기화·로비 생성 검증

스팀 테스트 앱ID 480(Spacewar)을 steam_appid.txt에 기록하고, Steam 초기화 → 연결 확인 → 공개 로비(최대 4명) 생성 순서로 확인하는 GDScript를 작성했다.

- `_process`에서 `Steam.run_callbacks()`를 매 프레임 돌려줘야 한다. 안 그러면 `lobby_created` 같은 비동기 콜백이 전혀 오지 않음

## 검증 기록 (실제 테스트 결과)

- **개발환경**: Godot v4.5.2.4.5.2-stable.custom_build (GodotSteam 번들 에디터), Steam 테스트 앱ID 480
- **출력**: `Steam 초기화 결과: true` / `✅ Steam 연결 성공!` / `로그인 계정: <Steam 계정>` / `✅ 로비 생성 성공! 로비 ID: <로비 ID>`
- **결론**: GodotSteam은 Godot 4.6에서 단일 프로세스 기준으로는 정상 동작함. MultiplayerPeer(멀티플레이 연결 전용 모듈)는 조건부 지원 — 별도 저장소의 최신 릴리스가 Godot 4.5.1까지만 공식 태그됐고, 이후 커밋 14개가 더 쌓여 4.6 호환은 아직 정식 태그 전 상태임

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
