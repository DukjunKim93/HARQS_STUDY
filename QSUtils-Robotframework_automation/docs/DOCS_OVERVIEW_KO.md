# docs/ 디렉토리 문서 상세 설명 (KO)

이 문서는 `docs/` 아래에 있는 각 Markdown 파일의 목적과 핵심 내용을 한국어로 요약/설명합니다.

## 1. OVERVIEW.md — Unified Dump & JFrog Integration 개요

**역할:**
- QSMonitor 덤프 시스템의 전체 개요 및 흐름을 설명합니다.
- 단일 진입점(`UnifiedDumpCoordinator`)을 통해 덤프 요청을 통합 처리하고, 필요 시 JFrog 업로드까지
  이어지는 흐름을 정리합니다.

**핵심 포인트:**
- 덤프 요청 트리거(수동/크래시/테스트 실패)를 하나의 파이프라인으로 처리합니다.
- Issue 디렉토리 구조(타임스탬프 기반)와 `manifest.json`의 역할을 설명합니다.
- 이벤트 기반 구조, 멀티 디바이스 병렬 처리, 상태바 표시, JFrog 업로드 설정 항목을 한눈에 정리합니다.
- 전체 워크플로 단계(Trigger → Coordination → Extraction → Completion → Upload → Notification)를
  단계별로 요약합니다.【F:docs/OVERVIEW.md†L1-L40】

## 2. ARCHITECTURE.md — 구성 요소와 책임

**역할:**
- 덤프/업로드 시스템을 구성하는 핵심 컴포넌트와 책임 범위를 정의합니다.

**핵심 포인트:**
- `UnifiedDumpCoordinator`는 전역 스코프에서 덤프와 업로드를 오케스트레이션합니다.
- `DumpProcessManager`는 장치별 스코프에서 실제 덤프 추출을 실행합니다.
- Event Bus(전역/디바이스), Status Bar, JFrogManager/JFrogUploader, JFrogConfig 구성 요소의 역할이
  분리되어 있습니다.
- Issue 개념(타임스탬프 기반 디렉토리 구조)과 `manifest.json`의 필드를 상세히 정리합니다.【F:docs/ARCHITECTURE.md†L1-L62】

## 3. JFROG_INTEGRATION.md — 업로드 모드와 설정

**역할:**
- 덤프 결과를 JFrog Artifactory로 업로드하는 방법과 모드, 설정 UI를 설명합니다.

**핵심 포인트:**
- **Headless 모드**와 **Dialog 모드**의 차이점과 트리거 조건을 구분합니다.
- `jf` CLI 설치, 인증, 권한 등 사전 요구사항을 명시합니다.
- 설정 다이얼로그 항목(서버 URL, 레포지토리, 경로 프리픽스 등)과 설정 저장 위치를 설명합니다.
- 업로드 라이프사이클(검증 → 이벤트 → 업로드 → 완료 → manifest 기록)을 단계별로 정리합니다.【F:docs/JFROG_INTEGRATION.md†L1-L74】

## 4. EVENT_SYSTEM.md — 이벤트 흐름과 페이로드

**역할:**
- QSMonitor 덤프 시스템의 이벤트 기반 통신 구조를 설명합니다.

**핵심 포인트:**
- Common Events와 Global Events의 스코프 차이를 정리합니다.
- `UNIFIED_DUMP_REQUESTED`, `DUMP_COMPLETED`, `GLOBAL_DUMP_COMPLETED`, `JFROG_UPLOAD_STARTED` 등
  주요 이벤트와 페이로드 구조를 설명합니다.
- 덤프 시작부터 업로드 완료까지의 이벤트 흐름 다이어그램을 제공합니다.
- 동시성 처리(큐, `_max_concurrency`) 방식도 요약합니다.【F:docs/EVENT_SYSTEM.md†L1-L47】

## 5. PATH_STRATEGY.md — 덤프 경로 전략

**역할:**
- 덤프 파일의 저장 경로를 결정하는 전략(Strategy Pattern)을 설명합니다.

**핵심 포인트:**
- `unified`, `individual`, `hybrid` 세 가지 전략과 각각의 경로 구조를 비교합니다.
- 기본값은 `unified`이며, 설정 키(`dump.path_strategy`)로 변경 가능합니다.
- `DumpProcessManager`의 `_override_working_dir`를 통해 경로 재정의가 가능한 점을 설명합니다.【F:docs/PATH_STRATEGY.md†L1-L33】

## 6. STATUS_BAR.md — 상태바 시스템

**역할:**
- 장치별 상태바(연결 상태, 세션 상태, 덤프 진행 상황 등) 표시 방식을 설명합니다.

**핵심 포인트:**
- `BaseDeviceWindow`와 `DeviceWindow`의 역할 구분 및 확장 구조를 설명합니다.
- 덤프/AutoReboot/세션/연결 상태를 우선순위 기반으로 표시하는 로직을 정리합니다.
- 이벤트 기반으로 상태바가 업데이트되며, 멀티 디바이스 환경에서도 충돌을 방지합니다.
- JFrog 업로드와의 연동, 커스터마이징 훅, 다크 테마 지원, 성능 고려 사항을 포함합니다.【F:docs/STATUS_BAR.md†L1-L55】
