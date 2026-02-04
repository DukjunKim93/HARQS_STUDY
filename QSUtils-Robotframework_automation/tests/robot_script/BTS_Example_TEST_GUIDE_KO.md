# BTS_Example.robot 테스트 가이드 (KO)

## 개요
`BTS_Example.robot`은 BTS 라이브러리 사용법과 Robot Framework 문법을 한 번에 보여주는 예제/치트시트
테스트 스위트입니다. ATHub, DebugShell, SDB, Sound, WebCam, Video, PatternGenerator, OCR/Image 비교 등 다양한
디바이스 시나리오와 함께 반복문/조건문/변수 등의 문법 예제가 포함되어 있습니다.【F:tests/robot_script/BTS_Example.robot†L1-L382】

## 주요 의존성
`BTS_Device_Settings.py`/`.ini`, `BTS_Variable.py`에 정의된 여러 디바이스 설정이 필요하며, 아래 BTS 라이브러리를
사용합니다.

- `BTS.BTS_ATHub`, `BTS.BTS_DebugShell`, `BTS.BTS_Sdb`, `BTS.BTS_Sound`, `BTS.BTS_WebCam`,
  `BTS.BTS_Video`, `BTS.BTS_KeySender`, `BTS.BTS_PatternGenerator` 등.【F:tests/robot_script/BTS_Example.robot†L7-L33】

## 실행 방법

```bash
python -m robot.run tests/robot_script/BTS_Example.robot
```

## 예상 결과
- 예제/참고용 스위트이므로 모든 테스트가 항상 PASS를 보장하지 않습니다.
- 실제 하드웨어(ATHub, SDB, WebCam, Sound, Pattern Generator 등)가 연결되어 있어야 성공합니다.
- 필요한 장비가 준비되면 개별 테스트 케이스 단위로 실행하는 것을 권장합니다.

## 참고
- 공통 키워드로 `CommonKeyword.robot`을 사용하며, 설정 파일(`BTS_Device_Settings.ini`/`.py`) 기반으로
  디바이스 정보를 로드합니다.
- OCR/Image 예제를 실행하려면 `BTS_ReferenceList_IMG.py`/`BTS_ReferenceList_OCR.py` 준비가 필요합니다.【F:tests/robot_script/BTS_Example.robot†L12-L36】
