# BTS 라이브러리 개요 (KO)

이 문서는 이 저장소에서 사용하는 **BTS(Broadcast Testing System)** 라이브러리가 무엇인지, 그리고 Robot
Framework 테스트와 어떻게 연결되는지 설명합니다.

## 1. 이 저장소에서 BTS란?

BTS는 `robot-scripts-package/` 디렉토리에서 설치되는 **커스텀 디바이스 제어 라이브러리**입니다.
`BTS.BTS_ATHub`, `BTS.BTS_Sound`, `BTS.BTS_Sdb` 같은 모듈을 제공하며, `tests/robot_script/`의 Robot Framework
테스트에서 키워드 구현체로 사용됩니다.

설치 가이드에서도 BTS를 메인 테스트 프레임워크 패키지로 설명하고 있습니다.
【F:BTS_INSTALLATION.md†L1-L27】

## 2. BTS 설치 방식

BTS는 아래 명령으로 로컬 패키지를 editable 모드로 설치합니다.

```bash
pip install -e robot-scripts-package/
```

이 설치를 통해 Robot Framework가 `BTS.*` 모듈을 로드할 수 있게 됩니다.
【F:BTS_INSTALLATION.md†L31-L46】

## 3. BTS가 제공하는 모듈 예시

설치 가이드에 포함된 패키지 구조는 다음과 같은 모듈을 보여줍니다.

- **BTS_ATHub**: IR 허브 디바이스 제어
- **BTS_Sound**: 오디오 녹음/분석
- **BTS_Sdb**: SDB (Samsung Debug Bridge) 제어
- **BTS_Video / BTS_WebCam**: 영상/웹캠 제어

이 구조는 `robot-scripts-package/`의 BTS 디렉토리 설명에 포함되어 있습니다.
【F:BTS_INSTALLATION.md†L13-L27】

## 4. Robot Framework에서 BTS 사용 방식

Robot Framework 테스트 스위트는 BTS 라이브러리를 키워드 제공자로 로드합니다.

```robotframework
*** Settings ***
Library    BTS.BTS_ATHub    ${ATHub01}
```

이후 테스트 케이스에서 `athub_connect`, `athub_sendIR` 같은 키워드를 실행합니다.
【F:tests/robot_script/tv_power_control.robot†L1-L23】

## 5. 디바이스 설정

BTS 키워드는 `BTS_Device_Settings.py`/`.ini`에 정의된 디바이스 설정을 사용합니다. 예를 들어 ATHub는
`port`, `connection_info1` 값이 실제 시리얼 장치 경로와 일치해야 합니다.
【F:tests/robot_script/BTS_Device_Settings.py†L1-L10】

## 6. 의존성

BTS 라이브러리는 오디오/비디오 처리 등을 위해 추가적인 Python 및 시스템 의존성을 요구합니다. 설치 가이드에
의존성 목록과 Linux 환경에서의 오디오 관련 수정 사항이 정리되어 있습니다.
【F:BTS_INSTALLATION.md†L49-L114】

## 7. 정리

이 저장소에서 **BTS는 실제 디바이스 제어 키워드를 제공하는 커스텀 라이브러리**입니다. Robot Framework는
테스트 실행기/DSL 역할을 하고, BTS는 하드웨어 제어를 담당합니다.
