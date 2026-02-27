# Crash 발생 시 Dump 추출과 Auto Reboot 제어 흐름 (한국어)

## 1) 현재 구조에서의 전체 흐름

Speaker Device(Audio Device)에서 Power on/off 과정 중 crash가 감지되면, 코드 상에서는 아래 순서로 흘러갑니다.

1. **Crash 감지**
   - `CrashMonitorService`가 주기적으로 coredump 징후를 확인합니다.
   - crash가 감지되면 `CRASH_DETECTED` 이벤트를 발행하고 dump 추출을 요청합니다.
2. **Dump 요청/시작**
   - dump coordinator/manager 계층이 `DUMP_STARTED` 이벤트를 발행하면서 dump 추출 프로세스를 시작합니다.
3. **AutoRebootGroup 이벤트 수신**
   - `AutoRebootGroup`는 `DUMP_STARTED`, `DUMP_COMPLETED`, `DUMP_ERROR`를 구독하고 있습니다.
   - 이 시점부터 Auto reboot의 타이머 진행 여부가 실제 동작을 결정합니다.
4. **Dump 완료/에러 처리**
   - `DUMP_COMPLETED`면 옵션에 따라 reboot 요청 또는 Auto reboot 정지.
   - `DUMP_ERROR`면 상태 타이머 정리 후 재시도 가능한 상태로 복귀.

---

## 2) 문제 원인 (왜 dump 중에도 Auto reboot가 진행되었나)

기존 코드에서는 `DUMP_STARTED`를 받았을 때:
- crash/qs 카운트 업데이트
- coredump 상태 텍스트 타이머 시작

까지만 하고, **실제 Auto reboot를 진행시키는 메인 타이머(`auto_reboot_timer`)와 QS-On 10초 타이머(`reboot_on_qs_timer`)를 멈추지 않았습니다.**

즉, dump가 돌아가는 중에도 내부 tick이 계속 증가해서 재부팅 요청이 나갈 수 있는 구조였습니다.

---

## 3) 이번 수정 내용

`AutoRebootGroup._on_dump_started()`에서 dump 시작 이벤트를 받으면 다음을 즉시 수행하도록 변경했습니다.

- `auto_reboot_timer`가 동작 중이면 정지
- `reboot_on_qs_timer`가 동작 중이면 정지
- 로그로 "dump 추출 중 Auto reboot 타이머 일시정지"를 명확히 남김

결과적으로 **dump 추출 동안 Auto reboot Test는 진행되지 않고 멈춘 상태**가 됩니다.

---

## 4) 간단한 예시 시나리오

예: Auto reboot interval = 100s, 현재 92s 진행 중

- t=92s: Power on/off 중 crash 발생
- `DUMP_STARTED` 수신
- 기존: 타이머 계속 돌아서 t=100s에 reboot 요청 가능 (문제)
- 수정 후: t=92s에서 auto reboot 관련 타이머 모두 정지
- dump 완료 전까지 reboot 요청 없음

즉, dump 확보가 끝날 때까지 테스트 흐름이 보존됩니다.

---

## 5) 관련 코드 포인트

- Auto reboot 이벤트 핸들러 등록/처리: `AutoRebootGroup`
- dump 시작 시 타이머 정지 처리: `AutoRebootGroup._on_dump_started()`
- 검증 테스트: `tests/test_auto_reboot_qs_on_timer.py`

