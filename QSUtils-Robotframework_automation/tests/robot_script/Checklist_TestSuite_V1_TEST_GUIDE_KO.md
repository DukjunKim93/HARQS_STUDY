# Checklist_TestSuite Version 1.0.robot 테스트 가이드 (KO)

## 개요
`Checklist_TestSuite Version 1.0.robot`은 TV와 사운드바 연결 검증을 위한 대형 E2E 테스트 스위트입니다.
ATHub, DebugShell, SDB, Sound, WebCam, KeySender, Navigation, RedRat 등 다양한 BTS 라이브러리와
AppiumLibrary를 사용하여 전원 제어, 영상 기록, 내비게이션 시나리오 등을 검증합니다.【F:tests/robot_script/Checklist_TestSuite Version 1.0.robot†L1-L46】

## 주요 의존성
`BTS_Device_Settings.py`/`.ini`, `BTS_Variable.py`에 정의된 디바이스 설정과 함께 아래 라이브러리가 필요합니다.

- `BTS.BTS_ATHub`, `BTS.BTS_DebugShell`, `BTS.BTS_Sdb`, `BTS.BTS_Sound`, `BTS.BTS_WebCam`,
  `BTS.BTS_KeySender`, `BTS.BTS_Navigation`, `BTS.BTS_RedRat`, `BTS.BTS_Common`
- 모바일 자동화를 위한 `AppiumLibrary` 사용.【F:tests/robot_script/Checklist_TestSuite Version 1.0.robot†L20-L46】

## 실행 방법

```bash
python -m robot.run "tests/robot_script/Checklist_TestSuite Version 1.0.robot"
```

## 예상 결과
- 하드웨어 의존도가 높아 실제 장비(ATHub/DebugShell/SDB/WebCam/Sound/RedRat)와 TV/사운드바 환경이
  구성되지 않으면 다수의 테스트가 실패할 수 있습니다.
- 모든 장비 준비 후 종합 검증용으로 사용하는 것을 권장합니다.

## 참고
- `CommonKeyword.robot`을 로드하며, Suite Setup/Teardown 키워드를 사용합니다.
- 이미지 기반 검증이 필요한 경우 `BTS_ReferenceList_IMG.py`를 준비해야 합니다.【F:tests/robot_script/Checklist_TestSuite Version 1.0.robot†L12-L53】
