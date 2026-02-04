# 시스템 아키텍처 & 흐름 (Korean)

이 저장소는 **QSUtils**라는 Python 기반 도구 모음을 제공하며, 장치 모니터링 GUI, ADB 기반 장치 관리,
Robot Framework 자동화 라이브러리, 그리고 통합 덤프 + JFrog 업로드 파이프라인을 하나로 묶어
자동화 테스트 및 진단을 지원합니다. 전체 목표는 테스트 자동화 환경에서 신뢰성 있는 덤프 수집과
업로드를 제공하면서 UI 반응성을 유지하는 것입니다.

## 1. 큰 그림

QSUtils는 아래 4개 레이어로 구성됩니다.

1. **애플리케이션 (UI/UX)**
   - **QSMonitor**: 장치 중심 모니터링 UI 및 상태바 제공
   - **QSLogger**: 로그 뷰어 및 분석 UI

2. **핵심 서비스**
   - **통합 덤프 시스템**: 장치 덤프 수집과 업로드를 중앙에서 조정
   - **이벤트 시스템**: 전역/장치 스코프 이벤트 버스로 UI와 백그라운드 작업 분리
   - **커맨드 실행 프레임워크**: 플러그형 명령 생성/실행 구조

3. **디바이스 & 통합 레이어**
   - **ADBDevice**: ADB 통신, 디바이스 관리, 로그 파싱
   - **Network Components**: 네트워크/WiFi 설정 및 관리
   - **JFrog 연동**: 업로드 매니저, 설정 다이얼로그, 백그라운드 업로더

4. **자동화 & 테스트**
   - **Robot Framework 라이브러리**: `QSUtils.RobotScripts` 패키지에 테스트 키워드 제공
   - **자동화 테스트**: Pytest 기반 덤프/커맨드/JFrog 업로드 검증

## 2. 주요 디렉토리

- `src/QSUtils/QSMonitor/`: 모니터링 앱(UI, 기능, 덤프 시스템)
- `src/QSUtils/ADBDevice/`: ADB 통신, 장치 관리, 로그 파싱
- `src/QSUtils/command/`: 장치 커맨드 실행 프레임워크
- `src/QSUtils/JFrogUtils/`: JFrog 업로드 로직과 설정 UI
- `src/QSUtils/RobotScripts/`: Robot Framework 라이브러리/템플릿
- `tests/`: Pytest 및 Robot Framework 예시
- `docs/`: 덤프/이벤트/JFrog/상태바 등 상세 문서

## 3. 통합 덤프 & 업로드 흐름

통합 덤프 시스템은 진단 덤프를 수집하고 (필요 시) JFrog로 업로드하는 과정을 표준화합니다.

**고수준 흐름**

1. **트리거**
   - 이벤트로 덤프 요청 (수동, 크래시, 테스트 실패 등)
2. **조정**
   - `UnifiedDumpCoordinator`가 *Issue* 디렉토리를 만들고 장치 작업을 큐잉
3. **추출**
   - 각 장치에서 `DumpProcessManager`가 로그/데이터를 추출
4. **완료**
   - 모든 장치 처리 후 `GLOBAL_DUMP_COMPLETED` 이벤트 발생
5. **업로드(옵션)**
   - `JFrogManager`가 설정 검증 후 업로드 실행 (헤드리스/다이얼로그)
6. **매니페스트 업데이트**
   - `manifest.json`에 장치별 결과와 업로드 상태 기록

```
Trigger Event
     │
     ▼
UnifiedDumpCoordinator
     │ (queue + issue dir)
     ▼
DumpProcessManager (per device)
     │ (DUMP_COMPLETED)
     ▼
GLOBAL_DUMP_COMPLETED
     │
     └─► JFrogManager (optional upload)
```

## 4. 이벤트 기반 구조

QSUtils는 두 가지 이벤트 스코프를 사용합니다.

- **Common Events**: 장치/로컬 이벤트 (상태바, 덤프 진행, 연결 상태)
- **Global Events**: 앱 전역 조정 이벤트 (덤프 완료, JFrog 업로드 라이프사이클)

이 구조 덕분에 UI는 가볍고, 백그라운드 작업은 메인 스레드를 블록하지 않습니다.

## 5. Robot Framework 자동화

Robot Framework 라이브러리 형태로 자동화 지원을 제공합니다.

- `QSUtils.RobotScripts.BTS.*`가 모바일/엑셀/비디오/장치 설정 관련 키워드를 제공
- `src/QSUtils/RobotScripts/` 및 `tests/robot_script/`에 예시/템플릿 포함

## 6. 대표 사용 시나리오

### A. 수동 모니터링 + 덤프
1. `qsmonitor` 실행
2. 장치 연결 후 상태 모니터링
3. UI에서 수동 덤프 트리거
4. 로컬 확인 또는 JFrog 다이얼로그 업로드

### B. 자동화 테스트 + 헤드리스 업로드
1. Robot Framework 테스트 실행
2. 실패/크래시 시 덤프 자동 트리거
3. 업로드는 백그라운드로 진행
4. 결과는 issue 매니페스트에 기록

## 7. 확장 포인트

- **새 커맨드 추가**: `src/QSUtils/command/`에 `cmd_*.py` 추가
- **모니터링 기능 확장**: `QSMonitor/features/`에 모듈 추가
- **덤프 경로 전략 변경**: `DumpPathStrategy` 확장
- **Robot 키워드 추가**: `QSUtils/RobotScripts/`에 신규 라이브러리 추가

## 8. 참고 문서

- `docs/OVERVIEW.md`: 통합 덤프/JFrog 개요
- `docs/ARCHITECTURE.md`: 컴포넌트 상세
- `docs/EVENT_SYSTEM.md`: 이벤트 흐름/페이로드
- `docs/JFROG_INTEGRATION.md`: 업로드 모드/설정
- `docs/STATUS_BAR.md`: 상태바 동작/우선순위
- `docs/PATH_STRATEGY.md`: 덤프 경로 전략
