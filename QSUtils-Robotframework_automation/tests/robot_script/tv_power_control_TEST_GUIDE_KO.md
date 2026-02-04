# tv_power_control.robot 테스트 가이드 (KO)

## 개요
`tv_power_control.robot`은 ATHub IR 디바이스를 통해 TV 전원을 제어하는 테스트입니다. 전원 ON/OFF 디스크리트
명령과 `KEY_POWER` 토글 시퀀스를 반복 전송합니다.【F:tests/robot_script/tv_power_control.robot†L1-L23】

## 주요 의존성
- `BTS.BTS_ATHub` 라이브러리와 `BTS_Device_Settings.py`의 ATHub 설정이 필요합니다.
- ATHub 시리얼 디바이스가 연결되어 있어야 합니다 (예: `/dev/ttyUSB1`).【F:tests/robot_script/tv_power_control.robot†L1-L23】

## 실행 방법

```bash
python -m robot.run tests/robot_script/tv_power_control.robot
```

## 예상 결과
- **Power On TV**, **Power Off TV**는 반복 IR 명령을 전송하며 장비 설정이 정상이라면 PASS가 예상됩니다.
- **Power On Off Test**는 `KEY_POWER` 토글을 사용하며 TV가 IR 신호에 반응해야 통과합니다.

## 참고
IDE 설정, troubleshooting 등 자세한 내용은 루트의 `TV_POWER_CONTROL_TEST_GUIDE.md`를 참고하세요.
