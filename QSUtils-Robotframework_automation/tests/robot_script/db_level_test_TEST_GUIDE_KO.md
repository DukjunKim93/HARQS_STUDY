# db_level_test.robot 테스트 가이드 (KO)

## 개요
`db_level_test.robot`은 설정된 사운드 디바이스에서 오디오를 녹음하고 dBFS 정보를 상세히 출력하는 테스트입니다.
여러 녹음 길이에 대한 dBFS 출력과 다양한 threshold 값 비교 테스트를 포함합니다.【F:tests/robot_script/db_level_test.robot†L1-L86】

## 주요 의존성
- `BTS.BTS_Sound` (`SoundSensor`로 사용) 기반 녹음/분석 기능.
- `BTS_Device_Settings.py`에 `Sound01` 설정이 필요합니다.【F:tests/robot_script/db_level_test.robot†L9-L33】

## 실행 방법

```bash
python -m robot.run tests/robot_script/db_level_test.robot
```

## 예상 결과
- **Display Audio dB Levels**: 녹음 길이별 dBFS 값을 출력하고 결과를 로그로 확인합니다.
- **Compare Different Thresholds**: 여러 threshold 값에서 오디오 감지 결과를 비교합니다.
- 실패 시, 주로 사운드 디바이스 미연결 또는 `Sound01` 설정 오류가 원인입니다.
