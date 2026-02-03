#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Command Abstract Base Class
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Callable, Any

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.command_constants import CommandResult
from QSUtils.command.command_executor import ADBCommandExecutor
from QSUtils.command.command_validator import CommandValidator
from QSUtils.command.error_handler import CommandErrorHandler
from QSUtils.command.retry_policy import RetryPolicy, RetryStrategy

# 타입 변수 정의
T = TypeVar("T")


class BaseCommand(ABC, Generic[T]):
    """
    Abstract base class for handling device commands.
    제네릭 타입 T를 사용하여 각 명령어의 반환 타입을 명시합니다.

    Type Parameters:
        T: 명령어 실행 결과의 데이터 타입
    """

    # New standardized lifecycle methods per refactor
    def validate(self) -> Optional[CommandResult[T]]:
        """Validate parameters and preconditions before execution.
        Returns CommandResult on failure, or None if valid."""
        try:
            return self.validator.validate_all(self.get_shell_command())
        except Exception as e:
            return CommandErrorHandler.handle_command_execution_error(
                e, self.__class__.__name__, "validation"
            )

    def run(self, context: Optional[dict] = None) -> CommandResult[T]:
        """Standard execute entry point used by the new Command pattern.
        Delegates to existing execute() for backward compatibility."""
        return self.execute()

    def rollback(self, context: Optional[dict] = None) -> None:
        """Optional rollback hook. Default is no-op."""
        return None

    def __init__(self, device: Any):
        """
        Initialize the base command.

        Args:
            device: ADBDevice instance for executing commands
        """
        self.device = device
        self.executor = ADBCommandExecutor(device)
        self.validator = CommandValidator(device, self.__class__.__name__)

    @abstractmethod
    def get_shell_command(self) -> str:
        """
        Returns the shell command string to be executed.
        The ADBDevice will handle the ADB-specific parts.

        Returns:
            str: 실행할 쉘 명령어
        """
        pass

    @abstractmethod
    def handle_response(self, response_lines: List[str]) -> CommandResult[T]:
        """
        Handles the response from the command execution.

        Args:
            response_lines: List of response lines from the command output

        Returns:
            CommandResult[T]: 파싱된 결과 데이터 (제네릭 타입)
        """
        pass

    def _process_output(self, output: Optional[str]) -> CommandResult[T]:
        """
        Process command output and handle response.

        Args:
            output: Command output string

        Returns:
            CommandResult[T]: 처리된 결과 또는 실패 시 CommandResult.failure
        """
        # 현재 handler ID를 미리 계산하여 비동기 실행 중에도 일관성 유지
        current_handler_id = id(self)

        if output is not None:
            response_lines = output.strip().split("\n") if output else []
            LOGD(f"{self.__class__.__name__}: Response lines: {response_lines}")

            try:
                result = self.handle_response(response_lines)
                LOGD(f"{self.__class__.__name__}: Handler result: {result}")

                # handler ID 추가 (비동기 콜백 경쟁 방지용)
                # 모든 결과에 대해 handler ID 설정하여 일관성 유지
                if hasattr(result, "success"):
                    result._handler_id = current_handler_id
                    LOGD(
                        f"{self.__class__.__name__}: Set handler_id {current_handler_id} for result"
                    )

                return result
            except Exception as e:
                error_result = CommandErrorHandler.handle_command_execution_error(
                    e, self.__class__.__name__, "response processing"
                )
                # 실패 결과에도 handler ID 추가
                error_result._handler_id = current_handler_id
                LOGD(
                    f"{self.__class__.__name__}: Set handler_id {current_handler_id} for error result"
                )
                return error_result
        else:
            error_msg = "No output from shell command"
            LOGD(f"{self.__class__.__name__}: {error_msg}")
            error_result = CommandResult.failure(error_msg)
            error_result._handler_id = current_handler_id
            LOGD(
                f"{self.__class__.__name__}: Set handler_id {current_handler_id} for no output error"
            )
            return error_result

    def execute(self) -> CommandResult[T]:
        """
        Execute the command using the associated ADBDevice.

        Returns:
            CommandResult[T]: 명령어 실행 결과
        """
        # 재시도 정책 설정 (디바이스 연결 관련 에러에 대해 최대 3회 재시도, 지수 백오프)
        retry_policy = RetryPolicy(
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            backoff_factor=2.0,
        )

        # 재시도 정책에 따라 작업 실행
        success, exception, result = retry_policy.execute_with_retry(
            self._execute_single_attempt, command_name=self.__class__.__name__
        )

        if success:
            return result
        else:
            # 재시도 실패 시 에러 처리
            return CommandErrorHandler.handle_command_execution_error(
                exception, self.__class__.__name__, "synchronous execution"
            )

    def _execute_single_attempt(self) -> CommandResult[T]:
        """
        단일 실행 시도 메서드

        Returns:
            CommandResult[T]: 명령어 실행 결과
        """
        try:
            shell_command = self.get_shell_command()
            LOGD(f"{self.__class__.__name__}: Shell command: {shell_command}")

            # 사전 검증
            validation_result = self.validator.validate_all(shell_command)
            if validation_result is not None:
                return validation_result

            # 명령어 실행
            output = self.executor.execute(shell_command)
            result = self._process_output(output)

            return result

        except Exception as e:
            # 디바이스 연결 관련 에러인지 확인
            if not self.is_device_connected():
                error_msg = "Device not connected"
                LOGD(f"{self.__class__.__name__}: {error_msg}")
                return CommandResult.failure(error_msg)
            else:
                raise e

    def execute_async(self, callback: Callable[[CommandResult[T]], None]) -> None:
        """
        비동기적으로 명령어를 실행합니다.

        Args:
            callback: 실행 결과를 처리할 콜백 함수
                     CommandResult[T] 타입의 결과를 받음
        """
        try:
            shell_command = self.get_shell_command()
            LOGD(f"{self.__class__.__name__}: Async shell command: {shell_command}")

            # 사전 검증
            validation_result = self.validator.validate_all(shell_command)
            if validation_result is not None:
                callback(validation_result)
                return

            def adb_callback(output: Optional[str]):
                """ADB 실행 결과를 처리하는 내부 콜백"""
                try:
                    result = self._process_output(output)
                    callback(result)
                except Exception as e:
                    error_result = CommandErrorHandler.handle_command_execution_error(
                        e, self.__class__.__name__, "async callback processing"
                    )
                    callback(error_result)

            try:
                # CommandExecutor의 비동기 실행 메서드 호출
                self.executor.execute_async(shell_command, adb_callback)
            except Exception as e:
                error_result = CommandErrorHandler.handle_command_execution_error(
                    e, self.__class__.__name__, "async execution setup"
                )
                callback(error_result)

        except Exception as e:
            error_result = CommandErrorHandler.handle_command_execution_error(
                e, self.__class__.__name__, "async execution validation"
            )
            callback(error_result)

    def get_command_name(self) -> str:
        """
        명령어 클래스 이름을 반환합니다.

        Returns:
            str: 명령어 클래스 이름
        """
        return self.__class__.__name__

    def is_device_connected(self) -> bool:
        """
        디바이스 연결 상태를 확인합니다.

        Returns:
            bool: 디바이스 연결 여부
        """
        return hasattr(self.device, "is_connected") and self.device.is_connected

    def validate_preconditions(self) -> Optional[CommandResult[T]]:
        """
        명령어 실행 전 사전 조건을 검증합니다.

        Returns:
            Optional[CommandResult[T]]: 검증 실패 시 CommandResult, 성공 시 None
        """
        # 디바이스 연결 상태 검증
        if not self.is_device_connected():
            error_msg = "Device not connected"
            LOGD(f"{self.__class__.__name__}: {error_msg}")
            return CommandResult.failure(error_msg)

        return None

    def get_execution_context(self) -> dict:
        """
        명령어 실행 컨텍스트 정보를 반환합니다.

        Returns:
            dict: 실행 컨텍스트 정보
        """
        return {
            "command_name": self.get_command_name(),
            "device_connected": self.is_device_connected(),
            "device_serial": getattr(self.device, "serial", "Unknown"),
        }
