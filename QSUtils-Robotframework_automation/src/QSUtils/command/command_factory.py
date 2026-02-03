#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Factory
통합 명령어 팩토리 클래스
"""

from typing import Type, Dict, Any, Callable, Optional

from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.command.CommandTask import CommandTask
from QSUtils.command.base_command import BaseCommand
from QSUtils.command.cmd_coredump_monitor import CoredumpMonitorCommandHandler
from QSUtils.command.cmd_dsp_audio_setting import DspAudioSettingCommand
from QSUtils.command.cmd_get_preference_data import PreferenceDataCommandHandler
from QSUtils.command.cmd_network_interface import NetworkInterfaceCommand
from QSUtils.command.cmd_pp_speaker_remap import SpeakerRemapCommandHandler
from QSUtils.command.cmd_pp_surround_speaker_remap import (
    SurroundSpeakerRemapCommandHandler,
)
from QSUtils.command.cmd_pp_symphony import SymphonyStatusCommandHandler
from QSUtils.command.cmd_pp_symphony_group import SymphonyGroupCommandHandler
from QSUtils.command.cmd_pp_symphony_volume_add import SymphonyVolumeAddCommandHandler
from QSUtils.command.cmd_reboot import RebootCommand
from QSUtils.command.cmd_test_wamp import TestWampCommand


class CommandFactory:
    """통합 명령어 팩토리"""

    # 명령어 타입과 클래스 매핑 (ConnectionManagerCommand는 지연 임포트로 처리)
    _command_map: Dict[str, Type[BaseCommand]] = {
        "coredump_monitor": CoredumpMonitorCommandHandler,
        "get_preference_data": PreferenceDataCommandHandler,
        "network_interface": NetworkInterfaceCommand,
        "speaker_remap": SpeakerRemapCommandHandler,
        "surround_speaker_remap": SurroundSpeakerRemapCommandHandler,
        "symphony_status": SymphonyStatusCommandHandler,
        "symphony_group": SymphonyGroupCommandHandler,
        "symphony_volume_add": SymphonyVolumeAddCommandHandler,
        "reboot": RebootCommand,
    }

    # WAMP 기반 명령어 타입
    _wamp_command_map: Dict[str, Type[TestWampCommand]] = {
        "dsp_audio_setting": DspAudioSettingCommand,
    }

    @classmethod
    def create_command(
        cls, command_type: str, device: ADBDevice, **kwargs
    ) -> BaseCommand:
        """
        명령어 타입에 따른 인스턴스 생성

        Args:
            command_type: 명령어 타입 문자열
            device: ADBDevice 인스턴스
            **kwargs: 명령어별 추가 파라미터

        Returns:
            BaseCommand: 생성된 명령어 인스턴스

        Raises:
            ValueError: 지원되지 않는 명령어 타입인 경우
        """
        # ConnectionManagerCommand는 지연 임포트로 순환 참조 방지
        if command_type == "connection_manager":
            from QSUtils.command.cmd_connection_manager import ConnectionManagerCommand

            action = kwargs.get("action", "setup")
            ssid = kwargs.get("ssid")
            password = kwargs.get("password")
            return ConnectionManagerCommand(device, action, ssid, password)

        command_class = cls._command_map.get(command_type)
        if not command_class:
            raise ValueError(
                f"Unknown command type: {command_type}. Supported types: {list(cls._command_map.keys())}"
            )

        try:
            # 다른 명령어들은 기본 생성자 호출
            return command_class(device, **kwargs)

        except Exception as e:
            raise ValueError(f"Failed to create command {command_type}: {str(e)}")

    @classmethod
    def create_wamp_command(
        cls, command_type: str, device: ADBDevice, wamp_component: str, **kwargs
    ) -> TestWampCommand:
        """
        WAMP 기반 명령어 생성

        Args:
            command_type: WAMP 명령어 타입
            device: ADBDevice 인스턴스
            wamp_component: WAMP 컴포넌트 이름
            **kwargs: 추가 파라미터

        Returns:
            TestWampCommand: 생성된 WAMP 명령어 인스턴스

        Raises:
            ValueError: 지원되지 않는 WAMP 명령어 타입인 경우
        """
        command_class = cls._wamp_command_map.get(command_type)
        if not command_class:
            raise ValueError(
                f"Unknown WAMP command type: {command_type}. Supported types: {list(cls._wamp_command_map.keys())}"
            )

        try:
            return command_class(device, wamp_component, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create WAMP command {command_type}: {str(e)}")

    @classmethod
    def create_task(
        cls,
        command: BaseCommand,
        callback: Callable[[BaseCommand, Optional[Any]], None],
    ) -> CommandTask:
        """
        CommandTask 생성

        Args:
            command: 실행할 명령어 인스턴스
            callback: 결과 처리 콜백 함수

        Returns:
            CommandTask: 생성된 CommandTask 인스턴스
        """
        return CommandTask(command, callback)

    @classmethod
    def create_task_with_timeout(
        cls,
        command: BaseCommand,
        callback: Callable[[BaseCommand, Optional[Any]], None],
        timeout: int = 30,
        max_retries: int = 0,
        task_id: str = None,
    ) -> CommandTask:
        """
        타임아웃 및 재시도 설정이 있는 CommandTask 생성

        Args:
            command: 실행할 명령어 인스턴스
            callback: 결과 처리 콜백 함수
            timeout: 타임아웃 시간 (초)
            max_retries: 최대 재시도 횟수
            task_id: 작업 식별자

        Returns:
            CommandTask: 생성된 CommandTask 인스턴스
        """
        return CommandTask(command, callback, timeout, max_retries, task_id)

    @classmethod
    def create_advanced_task(
        cls,
        command: BaseCommand,
        callback: Callable[[BaseCommand, Optional[Any]], None],
        timeout: int = 30,
        max_retries: int = 0,
        task_id: str = None,
    ) -> CommandTask:
        """
        고급 기능이 포함된 CommandTask 생성 (타임아웃, 재시도, 진행 상황 추적)

        Args:
            command: 실행할 명령어 인스턴스
            callback: 결과 처리 콜백 함수
            timeout: 타임아웃 시간 (초)
            max_retries: 최대 재시도 횟수
            task_id: 작업 식별자

        Returns:
            CommandTask: 생성된 CommandTask 인스턴스
        """
        return CommandTask(command, callback, timeout, max_retries, task_id)

    @classmethod
    def get_supported_command_types(cls) -> list:
        """
        지원되는 명령어 타입 목록 반환

        Returns:
            list: 지원되는 명령어 타입 리스트
        """
        supported_types = list(cls._command_map.keys())
        supported_types.append("connection_manager")  # 지연 임포트로 처리하는 타입 추가
        return supported_types

    @classmethod
    def get_supported_wamp_command_types(cls) -> list:
        """
        지원되는 WAMP 명령어 타입 목록 반환

        Returns:
            list: 지원되는 WAMP 명령어 타입 리스트
        """
        return list(cls._wamp_command_map.keys())

    @classmethod
    def is_command_type_supported(cls, command_type: str) -> bool:
        """
        명령어 타입 지원 여부 확인

        Args:
            command_type: 확인할 명령어 타입

        Returns:
            bool: 지원 여부
        """
        return command_type in cls._command_map or command_type == "connection_manager"

    @classmethod
    def is_wamp_command_type_supported(cls, command_type: str) -> bool:
        """
        WAMP 명령어 타입 지원 여부 확인

        Args:
            command_type: 확인할 WAMP 명령어 타입

        Returns:
            bool: 지원 여부
        """
        return command_type in cls._wamp_command_map


class AsyncTaskFactory:
    """비동기 작업 생성을 위한 팩토리 클래스 (기존 호환성 유지)"""

    @staticmethod
    def create_task(
        command: BaseCommand, callback: Callable[[BaseCommand, Optional[Any]], None]
    ) -> CommandTask:
        """
        CommandTask 인스턴스를 생성합니다.

        Args:
            command: 실행할 명령어 인스턴스
            callback: 결과 처리 콜백 함수

        Returns:
            CommandTask: 생성된 CommandTask 인스턴스
        """
        return CommandFactory.create_task(command, callback)
