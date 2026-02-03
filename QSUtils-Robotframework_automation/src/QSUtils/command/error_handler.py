#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Error Handler
통합 에러 처리를 위한 핸들러 클래스
"""

import logging
from typing import Optional

from QSUtils.command.command_constants import CommandResult


class CommandErrorHandler:
    """통합 에러 처리 핸들러"""

    @staticmethod
    def log_error(handler_name: str, error: Exception, level: str = "ERROR") -> None:
        """
        일관된 에러 로깅

        Args:
            handler_name: 에러가 발생한 핸들러 이름
            error: 발생한 예외
            level: 로그 레벨 (ERROR, WARNING, DEBUG)
        """
        logger = logging.getLogger(handler_name)
        error_msg = f"{handler_name}: {str(error)}"

        if level == "ERROR":
            logger.error(error_msg)
        elif level == "WARNING":
            logger.warning(error_msg)
        elif level == "DEBUG":
            logger.debug(error_msg)
        else:
            logger.info(error_msg)

    @staticmethod
    def log_error_message(
        handler_name: str, error_message: str, level: str = "ERROR"
    ) -> None:
        """
        에러 메시지 직접 로깅

        Args:
            handler_name: 에러가 발생한 핸들러 이름
            error_message: 에러 메시지
            level: 로그 레벨 (ERROR, WARNING, DEBUG)
        """
        logger = logging.getLogger(handler_name)
        error_msg = f"{handler_name}: {error_message}"

        if level == "ERROR":
            logger.error(error_msg)
        elif level == "WARNING":
            logger.warning(error_msg)
        elif level == "DEBUG":
            logger.debug(error_msg)
        else:
            logger.info(error_msg)

    @staticmethod
    def create_error_result(error: Exception, handler_name: str) -> CommandResult:
        """
        표준화된 에러 결과 생성

        Args:
            error: 발생한 예외
            handler_name: 에러가 발생한 핸들러 이름

        Returns:
            CommandResult: 실패 결과
        """
        error_msg = f"{handler_name}: {str(error)}"
        CommandErrorHandler.log_error(handler_name, error)
        return CommandResult.failure(error_msg)

    @staticmethod
    def create_error_result_from_message(
        error_message: str, handler_name: str
    ) -> CommandResult:
        """
        에러 메시지로부터 실패 결과 생성

        Args:
            error_message: 에러 메시지
            handler_name: 에러가 발생한 핸들러 이름

        Returns:
            CommandResult: 실패 결과
        """
        CommandErrorHandler.log_error_message(handler_name, error_message)
        return CommandResult.failure(error_message)

    @staticmethod
    def validate_device_connection(
        device, handler_name: str
    ) -> Optional[CommandResult]:
        """
        디바이스 연결 상태 검증

        Args:
            device: ADBDevice 인스턴스
            handler_name: 핸들러 이름

        Returns:
            Optional[CommandResult]: 검증 실패 시 CommandResult, 성공 시 None
        """
        if not device:
            error_msg = "Device is None"
            CommandErrorHandler.log_error_message(handler_name, error_msg)
            return CommandResult.failure(error_msg)

        if not hasattr(device, "is_connected") or not device.is_connected:
            error_msg = "Device not connected"
            CommandErrorHandler.log_error_message(handler_name, error_msg)
            return CommandResult.failure(error_msg)

        return None

    @staticmethod
    def validate_shell_command(
        shell_command: str, handler_name: str
    ) -> Optional[CommandResult]:
        """
        쉘 명령어 검증

        Args:
            shell_command: 쉘 명령어
            handler_name: 핸들러 이름

        Returns:
            Optional[CommandResult]: 검증 실패 시 CommandResult, 성공 시 None
        """
        if not shell_command or not shell_command.strip():
            error_msg = "Shell command is empty"
            CommandErrorHandler.log_error_message(handler_name, error_msg)
            return CommandResult.failure(error_msg)

        return None

    @staticmethod
    def handle_command_execution_error(
        error: Exception, handler_name: str, context: str = "command execution"
    ) -> CommandResult:
        """
        명령어 실행 에러 처리

        Args:
            error: 발생한 예외
            handler_name: 핸들러 이름
            context: 에러 발생 컨텍스트

        Returns:
            CommandResult: 실패 결과
        """
        error_msg = f"Error during {context}: {str(error)}"
        CommandErrorHandler.log_error(handler_name, error, "ERROR")
        return CommandResult.failure(error_msg)
