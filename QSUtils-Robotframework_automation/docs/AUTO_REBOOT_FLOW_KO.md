# QSMonitor Auto Reboot 동작 시퀀스 및 개선 사항

## 1) 현재 코드 기준 Auto Reboot 시퀀스 상세 설명

아래는 **Auto Reboot 탭에서 Start 버튼을 눌렀을 때** 실제 코드 기준 흐름입니다.

1. `AutoRebootGroup.on_autoreboot_start_clicked()`에서 Start/Stop 상태를 보고 `_start_auto_reboot()`를 호출합니다.
2. `_start_auto_reboot()`에서:
   - Dump 모드를 `HEADLESS`로 설정
   - Auto Reboot 설정 저장
   - `auto_reboot_running=True`, `auto_reboot_elapsed_sec=0` 초기화
   - 1초 주기의 `auto_reboot_timer` 시작
   - 통계(Count/Success/Crash/QS Failed, total duration) 초기화
3. `auto_reboot_timer`는 매초 `_on_auto_reboot_tick()`을 호출합니다.
   - interval 카운터(`auto_reboot_elapsed_sec`)와 전체 소요시간(`total_run_seconds`)을 갱신
   - interval 도달 시 `_on_auto_reboot_timer_expired()` 호출
4. `_on_auto_reboot_timer_expired()`는 `request_reboot()`를 호출합니다.
5. `request_reboot()`에서 옵션에 따라 분기:
   - `Check QS before reboot`가 꺼져 있으면 즉시 `REBOOT_REQUESTED` 이벤트 발행
   - 켜져 있으면 DefaultMonitor의 QS 성공 여부 확인 후
     - 성공: `REBOOT_REQUESTED`
     - 실패: `_request_dump_for_failed_qs()`로 coredump 시퀀스 진입
6. 실제 재부팅 명령 처리 후 Base 계층에서 `REBOOT_COMPLETED` 이벤트를 발행하고,
   AutoRebootGroup의 `_on_reboot_completed()`가 이를 받아 reboot count를 증가시키고 타이머 관련 상태를 갱신합니다.

> 요약하면, 기존 구조는 `auto_reboot_timer` 기반 interval 루프 + 이벤트(`REBOOT_REQUESTED/REBOOT_COMPLETED`) 기반 재부팅 실행 구조입니다.

---

## 2) 이번 요청 반영 내용 (부팅 완료 전 interval 진행 문제 개선)

요청사항:
- 재부팅 후 화면에 `Connected`가 뜨기 전(완전 부팅 전)에는 interval이 다시 흐르지 않게 하고,
- 완전히 다시 올라온 뒤부터 interval을 재시작.
- 단, Status 우측의 **총 소요시간(total duration)은 계속 진행**.

구현 방식:

1. `AutoRebootGroup`에 `self._waiting_for_device_reconnect` 플래그를 추가했습니다.
2. `request_reboot()`가 호출되는 시점에 이 플래그를 `True`로 설정해,
   재부팅 요청 이후 구간을 “부팅 복귀 대기 구간”으로 표시합니다.
3. `_on_auto_reboot_tick()`에서:
   - `total_run_seconds`는 기존대로 계속 증가
   - `auto_reboot_elapsed_sec`(interval 카운트)는 `waiting_for_device_reconnect=True`일 때 증가하지 않도록 변경
   - interval 만료 판정도 같은 조건으로 보호
4. `DEVICE_CONNECTION_CHANGED` 이벤트 핸들러 `_on_device_connection_changed()`를 추가해,
   `connected=True`가 들어오면:
   - `waiting_for_device_reconnect=False`
   - `auto_reboot_elapsed_sec=0`으로 재설정
   - 그 시점부터 interval 카운트 재개
5. 상태 문구는 복귀 대기 중에 `Waiting for complete boot...`로 표시되도록 반영했습니다.

---

## 3) 요청사항 4번 반영 확인 (총 소요시간은 멈추지 않기)

`_on_auto_reboot_tick()`에서 `total_run_seconds`는 항상 증가하도록 유지했습니다.
즉,
- interval 진행(bar/남은초)은 부팅 복귀 전까지 정지
- Status 우측 total duration은 계속 증가

요청하신 동작과 일치합니다.

---

## 4) 테스트 포인트

`tests/test_auto_reboot_qs_on_timer.py`에 아래 시나리오를 추가했습니다.

- 복귀 대기 상태(`_waiting_for_device_reconnect=True`)에서 tick 발생 시:
  - `total_run_seconds`는 증가
  - `auto_reboot_elapsed_sec`는 증가하지 않음
- 이후 `DEVICE_CONNECTION_CHANGED(connected=True)` 이벤트를 주면:
  - 대기 플래그 해제
  - interval 카운트가 다시 증가 시작

