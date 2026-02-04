# BTS_Template.robot 테스트 가이드 (KO)

## 개요
`BTS_Template.robot`은 BTS 기반 Robot Framework 테스트를 작성하기 위한 최소 템플릿입니다. 일반적인
라이브러리/디바이스 설정, Suite/Test Setup 구조를 보여주며 기본 테스트 케이스는
`Example Hello BTS` 한 개만 포함합니다.【F:tests/robot_script/BTS_Template.robot†L1-L62】

## 주요 의존성
- `BTS_Variable.py` 및 `BTS_Device_Settings.ini`/`.py`에서 디바이스 설정을 로드합니다.
- BTS 라이브러리는 주석 처리되어 있으며, 필요한 것만 활성화해서 사용하도록 되어 있습니다.【F:tests/robot_script/BTS_Template.robot†L16-L46】

## 실행 방법

```bash
python -m robot.run tests/robot_script/BTS_Template.robot
```

## 예상 결과
- 기본 상태에서는 “Hello BTS” 로그만 출력하며, 하드웨어 없이도 PASS가 예상됩니다.
- BTS 라이브러리를 활성화하거나 디바이스 의존 단계가 추가되면 해당 장비 구성이 필요합니다.
