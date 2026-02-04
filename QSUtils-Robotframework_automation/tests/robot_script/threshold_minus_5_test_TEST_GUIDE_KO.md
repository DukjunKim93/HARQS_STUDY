# threshold_minus_5_test.robot 테스트 가이드 (KO)

## 개요
`threshold_minus_5_test.robot`은 오디오를 녹음한 뒤 dBFS 측정값이 특정 threshold 이상인지 확인하는 테스트입니다.
여러 길이의 녹음 테스트와 3초 단일 테스트가 포함되며, 내부 로직에서 -5 dBFS 기준과 함께 -17 dBFS 비교가
사용됩니다.【F:tests/robot_script/threshold_minus_5_test.robot†L1-L107】

## 주요 의존성
- `BTS.BTS_Sound` (`SoundSensor`) 기반 녹음 및 dBFS 분석.
- `BTS_Device_Settings.py`에 `Sound01` 설정 필요.【F:tests/robot_script/threshold_minus_5_test.robot†L7-L33】

## 실행 방법

```bash
python -m robot.run tests/robot_script/threshold_minus_5_test.robot
```

## 예상 결과
- **Audio Detection With Threshold Minus 5**: 여러 녹음 길이에 대한 dBFS 로그를 출력합니다.
- **Single Test With Threshold Minus 5**: 3초 녹음 기준의 PASS/FAIL을 출력합니다.
- 실패 시 입력 신호가 너무 작거나 디바이스 설정이 잘못되었을 가능성이 높습니다.
