#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Executor
명령어 실행을 전담하는 클래스
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable

from QSUtils.command.error_handler import CommandErrorHandler


class CommandExecutor(ABC):
    """
    명령어 실행을 위한 추상 기본 클래스
    """

    @abstractmethod
    def execute(self, shell_command: str) -> Optional[str]:
        """
        쉘 명령어를 동기적으로 실행합니다.

        Args:
            shell_command: 실행할 쉘 명령어

        Returns:
            Optional[str]: 명령어 실행 결과 출력
        """
        pass

    @abstractmethod
    def execute_async(
        self, shell_command: str, callback: Callable[[Optional[str]], None]
    ) -> None:
        """
        쉘 명령어를 비동기적으로 실행합니다.

        Args:
            shell_command: 실행할 쉘 명령어
            callback: 실행 결과를 처리할 콜백 함수
        """
        pass


class ADBCommandExecutor(CommandExecutor):
    """
    ADB 디바이스를 통한 명령어 실행 구현
    """

    def __init__(self, device):
        """
        ADBCommandExecutor 초기화

        Args:
            device: ADBDevice 인스턴스
        """
        self.device = device

    def execute(self, shell_command: str) -> Optional[str]:
        """
        ADB를 통해 쉘 명령어를 동기적으로 실행합니다.

        Args:
            shell_command: 실행할 쉘 명령어

        Returns:
            Optional[str]: 명령어 실행 결과 출력
        """
        try:
            return self.device.execute_adb_shell(shell_command)
        except Exception as e:
            CommandErrorHandler.log_error("ADBCommandExecutor", e)
            return None

    def execute_async(
        self, shell_command: str, callback: Callable[[Optional[str]], None]
    ) -> None:
        """
        ADB를 통해 쉘 명령어를 비동기적으로 실행합니다.

        Args:
            shell_command: 실행할 쉘 명령어
            callback: 실행 결과를 처리할 콜백 함수
        """
        try:
            self.device.execute_adb_shell_async(shell_command, callback)
        except Exception as e:
            CommandErrorHandler.log_error("ADBCommandExecutor", e)
            callback(None)
