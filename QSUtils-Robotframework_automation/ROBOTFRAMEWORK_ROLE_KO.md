# 이 저장소에서 Robot Framework의 역할 (KO)

이 문서는 **Robot Framework**가 이 저장소에서 어떤 역할을 하는지, 그리고 내부 구조와 어떻게 연결되는지를
쉽게 설명합니다.

## 1. Robot Framework는 커스텀 패키지인가요?

아닙니다. Robot Framework는 pip로 설치되는 표준 Python 패키지이며, 이 저장소의 의존성으로 선언되어 있습니다.

- `pyproject.toml`의 `project.optional-dependencies.robot`에 `robotframework`가 포함되어 있습니다.
- `requirements.txt`에도 `robotframework>=4.0`가 명시되어 있습니다.

즉, Robot Framework 자체는 외부 패키지이며 PyPI에서 설치됩니다.
【F:pyproject.toml†L30-L78】【F:requirements.txt†L1-L13】

## 2. 왜 Robot Framework를 쓰나요?

Robot Framework는 **키워드 기반 테스트 실행기**입니다. 이 저장소에서는 다음 목적에 사용됩니다.

- `tests/robot_script/` 아래의 `.robot` 테스트 스위트 실행
- BTS 디바이스 제어 라이브러리를 키워드 형태로 호출
- Q‑Symphony 장비 테스트/자동화를 읽기 쉬운 DSL로 작성

README에도 Robot Framework가 핵심 자동화 의존성으로 명시되어 있고, CLI 실행 예시가 포함되어 있습니다.
【F:README.md†L124-L187】

## 3. 저장소 구조와의 연결

### 3.1. Robot 테스트 스위트

Robot 테스트 파일은 아래 경로에 위치합니다.

- `tests/robot_script/*.robot`

예시로 `tv_power_control.robot`은 다음과 같이 디바이스 설정과 BTS 라이브러리를 로드합니다.

```robotframework
*** Settings ***
Variables   BTS_Device_Settings.py
Library     BTS.BTS_ATHub    ${ATHub01}
```

이렇게 설정된 키워드가 테스트 케이스에서 사용됩니다.
【F:tests/robot_script/tv_power_control.robot†L1-L23】

### 3.2. BTS 라이브러리 (키워드 구현체)

BTS 라이브러리는 `robot-scripts-package/` 설치를 통해 제공되는 **커스텀 코드**입니다.
문서에 따르면, 이 패키지를 설치하면 `BTS.BTS_ATHub`, `BTS.BTS_Sound` 같은 모듈이 로드 가능해집니다.

- 설치 명령: `pip install -e robot-scripts-package/`
- 해당 모듈이 Robot Framework 키워드 구현체 역할을 합니다.
【F:BTS_INSTALLATION.md†L1-L66】

## 4. 실행 흐름 (요약)

1. Robot Framework 실행기(`python -m robot.run`)가 `.robot` 파일을 로드
2. 테스트 스위트가 디바이스 설정 파일을 로드
3. BTS 라이브러리를 키워드로 로딩
4. 테스트 케이스에서 키워드를 실행

README의 실행 예시 섹션에서 실제 명령을 확인할 수 있습니다.
【F:README.md†L151-L187】

## 5. QSUtils와의 관계

Robot Framework는 QSUtils의 GUI/모니터링 코드와 **병렬적으로 동작하는 자동화 계층**입니다.
즉, QSMonitor 자체를 대체하는 것이 아니라:

- 디바이스 제어(ATHub/SDB/ADB)를 키워드화하여 자동화하고
- 음성/영상 테스트를 BTS 라이브러리로 수행하며
- 테스트 결과를 로깅/리포트 형태로 남길 수 있게 합니다.

정리하면, Robot Framework는 **자동화 실행기**, BTS 라이브러리는 **키워드 구현체**, QSUtils는 **전체 도구셋**을
제공하는 구조입니다.
