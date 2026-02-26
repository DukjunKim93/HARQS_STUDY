# sound_test.robot 테스트 가이드 (KO)

## 개요
`sound_test.robot`은 `Sound01` 디바이스 설정 확인, 녹음 가능 여부, TV 음소거 상태 확인을 위한 테스트입니다.
구성 확인 → 녹음 파일 생성 → 음소거 감지의 3개 테스트 케이스로 구성됩니다.【F:tests/robot_script/sound_test.robot†L1-L53】

## 주요 의존성
- `BTS.BTS_Sound` (`SoundSensor`) 기반 녹음/음소거 감지 기능.
- `BTS_Device_Settings.py`에 `Sound01` 설정이 필요합니다.【F:tests/robot_script/sound_test.robot†L11-L24】

## 실행 방법

```bash
python -m robot.run tests/robot_script/sound_test.robot
```

## 예상 결과
- **Verify Sound01 Device Configuration**: 디바이스 이름이 정상적으로 출력되어야 합니다.
- **Test Sound Recording From Sound01**: WAV 파일이 생성되고 크기가 0보다 커야 합니다.
- **Verify TV Is Not Muted**: TV 오디오가 있으면 PASS (mute 감지 false)로 통과합니다.
