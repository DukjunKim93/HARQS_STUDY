# QSMonitor 중심 세미나 자료 (한글)

> 대상: QSUtils 프로젝트 동료 개발자/QA
> 
> 형식: **PPT 10~15페이지 구성으로 바로 옮길 수 있는 발표용 Markdown**

---

## 페이지 1. 세미나 목적 & 배경

### 발표 목적
- QSUtils 전체 구조를 빠르게 공유
- 특히 **QSMonitor를 메인 제품 관점**에서 이해
- Command / DumpManager의 실무적 역할을 연결해서 설명

### 프로젝트 배경 (Q-Symphony 문맥)
- 이 프로젝트는 TV + 스피커(Q-Symphony) 통합 동작을 모니터링/검증하는 개발 도구 성격을 가짐
- 실시간 모니터링, 장치 제어(ADB), 로그 수집/분석, 자동화 테스트 연계를 목표로 함
- 장기적으로 자동화 가능한 검증 시나리오를 계속 확장하는 구조를 지향함

---

## 페이지 2. QSUtils 폴더 전체 지도 (src 기준)

`src/QSUtils` 하위는 아래처럼 역할이 분리되어 있음.

- `QSMonitor`: 메인 모니터링 앱
- `QSLogger`: 로그 뷰어 앱
- `ADBDevice`: 장치 연결/ADB 통신
- `command`: 자동화 테스트/모니터링 명령 체계
- `DumpManager`: 덤프 추출 프로세스 및 상태 관리
- `JFrogUtils`: 덤프 업로드 연계
- `UIFramework`: 공통 UI/윈도우/컨텍스트 베이스
- `RobotScripts`: Robot Framework 연계 리소스
- `Utils`, `components`: 공통 유틸/컴포넌트

즉, **QSMonitor(UI) + command(실행) + DumpManager(장애 분석) + JFrog(아카이빙)**가 운영 흐름의 핵심 축임.

---

## 페이지 3. QSMonitor 실행 진입점

QSMonitor 실행 흐름은 매우 단순하고 명확함.

1. `qsmonitor.py`의 `main()`이 앱 진입점
2. `QSMonitorConfig`를 생성
3. `AppLauncher.launch_app(QSMonitorApplication, app_config)` 호출
4. `QSMonitorApplication`이 `BaseMonitorApplication`을 상속해 `MainWindow`를 붙여 실행

핵심 포인트:
- 앱 부트스트랩은 얇고,
- 실제 로직은 `MainWindow`, `DeviceWindow`, `DeviceWidget`, 서비스 계층으로 위임됨

---

## 페이지 4. QSMonitor 시스템 아키텍처 (트리/레이어)

`QSMonitor` 내부 구조는 크게 5개 레이어로 설명 가능.

1. **core/**: 이벤트 타입/전역 이벤트/설정
2. **ui/**: MainWindow, DeviceWindow, 탭 UI
3. **features/**: Default/Network/SpeakerGrid/AutoReboot 기능 단위
4. **services/**: CrashMonitor, UnifiedDumpCoordinator 등 백그라운드 서비스
5. **UIFramework(base/widgets) 연계**: 공통 베이스 클래스 상속 기반 동작

발표 시 강조:
- QSMonitor 폴더만 보면 단순해 보이지만,
- 실제로는 UIFramework와 결합해 강력한 공통 패턴(상속 + 이벤트)을 활용함

---

## 페이지 5. 상속 구조 (중요)

### 앱/윈도우 상속
- `QSMonitorApplication` ← `BaseMonitorApplication`
- `MainWindow` ← `BaseMainWindow`
- `DeviceWindow` ← `BaseDeviceWindow`
- `DeviceWidget` ← `BaseDeviceWidget`

### Feature 상속
- `DefaultMonitorFeature`, `NetworkMonitorFeature`, `SpeakerGridFeature` ← `BaseFeature`
- 각 Feature는 내부적으로 DataProcessor + Widget 조합으로 동작

의미:
- 공통기능(디바이스 연결 상태, 세션 제어, 덤프 버튼, 상태바 등)은 베이스에서 해결
- QSMonitor는 “무엇을 추가할지”에 집중 (AutoReboot 상태 표시, 탭 구성 등)

---

## 페이지 6. 디바이스 단위 동작 원리 (DeviceWidget 중심)

`DeviceWidget`은 디바이스 탭의 실제 실행 허브 역할을 함.

- `CommandHandler` 생성 후 `DeviceContext`에 등록
- `GeneralTab` + `AutoRebootTab` 구성
- `CrashMonitorService`를 생성/등록
- 세션 시작 시 Crash 모니터링 시작, 세션 종료 시 중지
- 연결/해제 이벤트에 따라 세션 자동 제어

즉, 디바이스당 **(UI + 명령 실행 + 크래시 감시 + 덤프 트리거)**가 한 컨텍스트로 묶여 움직임.

---

## 페이지 7. 이벤트 기반 구조 (QSMonitor 운영 핵심)

`BaseMainWindow` 초기화 시 전역 이벤트 버스를 연결하고 `UnifiedDumpCoordinator`를 시작함.

- `JFROG_UPLOAD_STARTED`, `JFROG_UPLOAD_COMPLETED` 같은 전역 이벤트 핸들러 등록
- 디바이스 윈도우는 전역/로컬 이벤트를 구독하여 상태바와 화면을 반영
- `DeviceWindow`는 AutoReboot 상태 이벤트와 JFrog 업로드 시작 이벤트를 받아 우선순위 기반 상태 표시 수행

핵심 메시지:
- “함수 호출 체인”보다 “이벤트 전파”가 중심이라 모듈 결합도가 낮고 확장에 유리함

---

## 페이지 8. Command 폴더 분석 (자동화 테스트 명령 엔진)

`command/`는 **ADB 기반 명령 실행 프레임워크**로 보는 것이 가장 정확함.

### 구조 요약
- `base_command.py`: 명령 추상화(검증/실행/응답 처리/재시도/비동기)
- `command_executor.py`: 실행 추상층 (`CommandExecutor`, `ADBCommandExecutor`)
- `command_factory.py`: 명령 타입 → 클래스 매핑, Task 생성
- `CommandTask.py`: 비동기 실행(타임아웃, 재시도, 상태/시그널)
- `cmd_*.py`: 도메인별 실제 명령 구현체

### 예시 명령
- `cmd_reboot.py`: 재부팅 명령
- `cmd_network_interface.py`: 네트워크 인터페이스 정보 파싱

실무 포인트:
- 새 자동화 요구가 생기면 `cmd_xxx.py`를 추가하고 팩토리에 연결하면 확장 가능

---

## 페이지 9. DumpManager 분석 (장애 분석/증적 수집 핵심)

`DumpProcessManager`는 QProcess 기반으로 덤프 추출을 관리함.

### 주요 책임
- 상태 머신 관리 (`IDLE`, `STARTING`, `EXTRACTING`, `VERIFYING`, `COMPLETED`, ...)
- 모드 관리 (`DIALOG`, `HEADLESS`)
- 타임아웃/취소/오류 처리
- 진행 상황 다이얼로그/완료 다이얼로그 제어
- `DUMP_COMPLETED`, `DUMP_ERROR` 이벤트 발행

### 트리거 유형
- `MANUAL`, `CRASH_MONITOR`, `QS_FAILED`

의미:
- 단순 로그 저장이 아니라, **장애 시점 데이터 수집 파이프라인**을 표준화한 컴포넌트

---

## 페이지 10. QSMonitor + DumpManager + JFrog 통합 흐름

발표용 시퀀스 (간략):

1. 문제 감지(수동 클릭/크래시/QS 실패)
2. `UnifiedDumpCoordinator`가 이슈 단위 디렉토리/대상 장치 큐 구성
3. 장치별 `DumpProcessManager`가 덤프 추출
4. 모든 장치 완료 후 `GLOBAL_DUMP_COMPLETED`
5. 정책/설정에 따라 JFrog 업로드
6. 결과를 manifest에 기록하고 UI 상태 반영

핵심은 “장치 단위 실행 + 전역 집계” 2계층 구조라는 점.

---

## 페이지 11. 동료 공유용 코드 읽기 포인트 (실전 가이드)

### 1순위 파일
- `src/QSUtils/QSMonitor/qsmonitor.py`
- `src/QSUtils/QSMonitor/QSMonitorApplication.py`
- `src/QSUtils/QSMonitor/ui/MainWindow.py`
- `src/QSUtils/QSMonitor/ui/DeviceWindow.py`
- `src/QSUtils/QSMonitor/ui/DeviceWidget.py`

### 2순위 파일
- `src/QSUtils/command/base_command.py`
- `src/QSUtils/command/command_factory.py`
- `src/QSUtils/command/CommandTask.py`
- `src/QSUtils/DumpManager/DumpProcessManager.py`
- `src/QSUtils/QSMonitor/services/UnifiedDumpCoordinator.py`

발표 팁:
- “UI는 Base 상속”, “명령은 Command 패턴”, “분석은 Dump 파이프라인” 3문장으로 시작하면 이해가 빠름.

---

## 페이지 12. 현재 코드 기준 자동화 확장 아이디어

현재 구조에서 바로 가능한 확장:

1. **명령 추가 자동화**
   - `cmd_*.py` 신규 추가 + Factory 등록으로 기능 확장
2. **이벤트 기반 알림 강화**
   - dump/upload 이벤트를 외부 알림(메신저/대시보드)으로 브리지
3. **이슈 리포트 표준화**
   - manifest + 로그 + 핵심 메트릭을 묶어 반자동 리포트 생성
4. **시나리오 자동화 연계**
   - RobotScripts와 QSMonitor 이벤트를 연결해 실패 시 자동 덤프/업로드 일원화

즉, 현재 코드만으로도 “모니터링 → 문제 감지 → 증적 수집 → 공유” 자동화 루프를 충분히 고도화할 수 있음.

---

## 페이지 13. 마무리 (세미나 결론)

- QSUtils는 Q-Symphony 검증을 위한 실무형 도구셋이며,
- QSMonitor는 그 중심에서 디바이스 상태/로그/오류 대응을 담당함
- Command 폴더는 실행 엔진, DumpManager는 장애 증적 엔진 역할
- 구조가 상속 + 이벤트 + 명령 패턴으로 잘 분리되어 있어 협업/확장성이 높음

> 권장 다음 액션:
> - 팀 내 공통 운영 시나리오 3개(정상/네트워크 불안정/크래시)를 정해
> - QSMonitor + Dump + 업로드 흐름을 표준 운영 절차로 문서화하면 온보딩 속도가 크게 개선됩니다.
