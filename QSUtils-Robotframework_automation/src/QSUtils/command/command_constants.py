#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Constants and Enums
공통으로 사용되는 상수와 Enum 값을 정의하는 모듈
"""

from enum import Enum
from typing import Dict, List, TypeVar, Generic, Optional, Any

# 타입 변수 정의
T = TypeVar("T")


class SymphonyConstants:
    """Symphony 관련 명령어에서 사용되는 상수"""

    SOUND_MODES: Dict[int, str] = {
        0: "Adaptive",
        1: "Game",
        2: "Surround",
        3: "Standard",
        4: "Music",
    }

    GROUP_MODES: Dict[int, str] = {0: "Q-Symphony", 1: "Group", 2: "Stereo"}

    QS_STATES: Dict[int, str] = {0: "Off", 1: "On"}

    MODE_TYPES: Dict[int, str] = {0: "Symphony Lite", 1: "Symphony"}


class ConnectionManagerActions(Enum):
    """Connection Manager 명령어 액션 타입"""

    SETUP = "setup"
    GET_NETWORK_INFO = "get-network-info"


class WampCommandType(Enum):
    """WAMP 명령어 타입"""

    CALL = "call"
    PUBLISH = "publish"


class PreferenceDataKeys:
    """Preference Data 키 상수"""

    ACM_SERVICE_STATE = "com.harman.acm_service.state"
    MULTIROOM_INFO = "db/waapp/multiroom_info"
    MULTIROOM_MODE = "db/waapp/multiroom_mode"
    GROUPTYPE = "grouptype"


class SystemCommands:
    """시스템 명령어 상수"""

    LOGCAT = "logcat -b all -v time"
    IFCONFIG_TEMPLATE = "ifconfig {interface}"
    LS_TEMPLATE = "ls {path}"
    CAT_PREFERENCE_DATA = "cat /data/acm/.preference_data"
    SYNC_REBOOT = "sync && reboot -f"
    REBOOT = "reboot -f"
    TEST_WAMP_CLIENT_TEMPLATE = "test-wamp-client -c {component} -a '{command}'"


class TimeoutConstants:
    """타임아웃 상수 (밀리초)"""

    DEFAULT_TIMEOUT = 30  # 기본 타임아웃 (초)
    PROCESS_START_TIMEOUT = 5000  # 프로세스 시작 타임아웃 (5초)
    PROCESS_TERMINATE_TIMEOUT = 3000  # 프로세스 종료 타임아웃 (3초)
    PROCESS_KILL_TIMEOUT = 1000  # 프로세스 강제 종료 타임아웃 (1초)


class CommandResult(Generic[T]):
    """
    명령어 실행 결과를 표준화하는 제네릭 클래스
    타입 안전성을 보장하기 위해 Generic[T]를 사용합니다.
    """

    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        error: Optional[str] = None,
        handler_id: Optional[int] = None,
    ):
        """
        CommandResult 초기화

        Args:
            success: 성공 여부
            data: 성공 시 반환 데이터 (제네릭 타입 T)
            error: 실패 시 에러 메시지
            handler_id: command handler의 고유 ID (비동기 콜백 경쟁 방지용)
        """
        self.success: bool = success
        self.data: Optional[T] = data
        self.error: Optional[str] = error
        self._handler_id: Optional[int] = handler_id

    def __bool__(self) -> bool:
        """bool 컨텍스트에서 사용 시 성공 여부 반환"""
        return self.success

    def __str__(self) -> str:
        """문자열 표현"""
        if self.success:
            return f"CommandResult(success=True, data={self.data})"
        else:
            return f"CommandResult(success=False, error={self.error})"

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return f"CommandResult(success={self.success}, data={self.data!r}, error={self.error!r})"

    @property
    def is_success(self) -> bool:
        """성공 여부 속성"""
        return self.success

    @property
    def is_failure(self) -> bool:
        """실패 여부 속성"""
        return not self.success

    def get_data_or_default(self, default: T) -> T:
        """
        데이터가 있으면 반환, 없으면 기본값 반환

        Args:
            default: 기본값

        Returns:
            T: 데이터 또는 기본값
        """
        return self.data if self.data is not None else default

    def get_error_message(self) -> Optional[str]:
        """
        에러 메시지 반환

        Returns:
            Optional[str]: 에러 메시지 또는 None
        """
        return self.error

    @classmethod
    def success(cls, data: Optional[T] = None) -> "CommandResult[T]":
        """
        성공 결과 생성

        Args:
            data: 성공 시 반환 데이터

        Returns:
            CommandResult[T]: 성공 결과 인스턴스
        """
        return cls(True, data=data)

    @classmethod
    def failure(cls, error: str) -> "CommandResult[T]":
        """
        실패 결과 생성

        Args:
            error: 에러 메시지

        Returns:
            CommandResult[T]: 실패 결과 인스턴스
        """
        return cls(False, error=error)

    @classmethod
    def from_exception(cls, exception: Exception) -> "CommandResult[T]":
        """
        예외로부터 실패 결과 생성

        Args:
            exception: 예외 객체

        Returns:
            CommandResult[T]: 실패 결과 인스턴스
        """
        return cls.failure(str(exception))

    def map(self, transform_func) -> "CommandResult":
        """
        성공한 경우 데이터를 변환하는 함수 적용

        Args:
            transform_func: 데이터 변환 함수

        Returns:
            CommandResult: 변환된 결과
        """
        if self.success and self.data is not None:
            try:
                transformed_data = transform_func(self.data)
                return CommandResult.success(transformed_data)
            except Exception as e:
                return CommandResult.failure(f"Data transformation failed: {str(e)}")
        return self

    def flat_map(self, transform_func) -> "CommandResult":
        """
        성공한 경우 데이터를 다른 CommandResult로 변환하는 함수 적용

        Args:
            transform_func: CommandResult 변환 함수

        Returns:
            CommandResult: 변환된 결과
        """
        if self.success and self.data is not None:
            try:
                return transform_func(self.data)
            except Exception as e:
                return CommandResult.failure(f"Data transformation failed: {str(e)}")
        return self


# 타입 별칭 정의
NetworkInfoResult = CommandResult[Dict[str, Any]]
PreferenceDataResult = CommandResult[Dict[str, str]]
SymphonyStatusResult = CommandResult[Dict[str, str]]
SymphonyGroupResult = CommandResult[str]
SpeakerRemapResult = CommandResult[int]
SurroundSpeakerRemapResult = CommandResult[List[int]]
SymphonyVolumeAddResult = CommandResult[int]
CoredumpListResult = CommandResult[List[str]]
RebootResult = CommandResult[bool]
ConnectionManagerResult = CommandResult[Any]
