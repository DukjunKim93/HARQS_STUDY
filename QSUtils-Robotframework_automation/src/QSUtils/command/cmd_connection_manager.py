#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connection Manager Command Class for WiFi configuration.
"""

from typing import List, Any, Callable

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_test_wamp import TestWampCommand
from QSUtils.command.command_constants import (
    ConnectionManagerActions,
    CommandResult,
    WampCommandType,
)
from QSUtils.command.command_validator import ConnectionManagerCommandValidator


class ConnectionManagerCommand(TestWampCommand):
    """
    Command class for configuring WiFi connection using test-wamp-client.
    """

    def __init__(
        self, device, action: str = "setup", ssid: str = None, password: str = None
    ):
        """
        Initialize the connection manager command.

        Args:
            device: ADBDevice instance for executing commands
            action: The action to perform ("setup", "get-network-info")
            ssid: WiFi SSID (required for "setup" action)
            password: WiFi password (required for "setup" action)
        """
        # 부모 클래스 초기화
        if action == "setup":
            super().__init__(
                device, WampCommandType.CALL, "com.harman.connection-manager.conn-wlan0"
            )
        else:
            super().__init__(
                device,
                WampCommandType.CALL,
                "com.harman.connection-manager.get-network-info",
            )

        # 특화된 Validator 사용
        self.validator = ConnectionManagerCommandValidator(
            device, self.__class__.__name__
        )

        # 파라미터 검증
        validation_result = self.validator.validate_parameters(
            action=action, ssid=ssid, password=password
        )
        if validation_result is not None:
            raise ValueError(validation_result.error)

        # Validate action using enum
        try:
            self.action_enum = ConnectionManagerActions(action)
        except ValueError:
            raise ValueError(
                f"Unknown action: {action}. Valid actions: {[e.value for e in ConnectionManagerActions]}"
            )

        if self.action_enum == ConnectionManagerActions.SETUP:
            self.ssid = ssid
            self.password = password
        elif self.action_enum == ConnectionManagerActions.GET_NETWORK_INFO:
            self.ssid = None
            self.password = None

    @property
    def command_str(self) -> str:
        """
        Returns the JSON command string based on the action.
        """
        if self.action_enum == ConnectionManagerActions.SETUP:
            hex_pass = self._ascii_to_hex(self.password)
            return (
                f'{{"pos_args":["setup"], "nam_args": {{"ssid": "{self.ssid}", '
                f'"password":"{hex_pass}","enc":"False"}}}}'
            )
        elif self.action_enum == ConnectionManagerActions.GET_NETWORK_INFO:
            # get-network-info command does not require arguments
            return '{"pos_args":[""], "nam_args": {}}'
        return ""

    def _ascii_to_hex(self, text: str) -> str:
        """Converts ASCII string to hexadecimal string."""
        return "".join(f"{ord(c):02X}" for c in text)

    def _handle_setup_response(self, output: str) -> CommandResult:
        """Setup 액션의 응답을 처리합니다."""
        # Check for common success indicators in the output
        if any(indicator in output.lower() for indicator in ["success", "ok", "done"]):
            return CommandResult.success(True)
        else:
            # Return the output as an error message if no success indicator is found
            error_msg = output.strip() if output.strip() else "WiFi connection failed"
            return CommandResult.failure(error_msg)

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[Any]:
        """
        Process parsed WAMP response data for get-network-info action.

        Args:
            parsed_data: The parsed JSON data from WAMP response

        Returns:
            CommandResult[Any]: Network info from nam_args field
        """
        # The actual network info is in "nam_args".
        if "nam_args" in parsed_data and isinstance(parsed_data["nam_args"], dict):
            LOGD(
                f"ConnectionManagerCommand: Final 'nam_args' content: {parsed_data['nam_args']}"
            )
            return CommandResult.success(parsed_data["nam_args"])
        else:
            return CommandResult.failure("nam_args not found or not a dict in response")

    def handle_response(self, response_lines: List[str]) -> CommandResult[Any]:
        """
        Handles the response from the connection manager command.

        Args:
            response_lines: The list of response lines from the command output.

        Returns:
            CommandResult[Any]: 성공 시 처리된 데이터, 실패 시 에러 메시지
        """
        if not response_lines:
            error_msg = "No response from device"
            if self.action_enum == ConnectionManagerActions.SETUP:
                return CommandResult.failure("WiFi setup failed: " + error_msg)
            else:
                return CommandResult.failure(error_msg)

        output = "\n".join(response_lines)

        if self.action_enum == ConnectionManagerActions.SETUP:
            # Setup 액션은 WAMP 응답 파싱이 필요 없음
            return self._handle_setup_response(output)
        elif self.action_enum == ConnectionManagerActions.GET_NETWORK_INFO:
            # Get-network-info 액션은 부모 클래스의 WAMP 응답 파싱 사용
            return super().handle_response(response_lines)
        else:
            return CommandResult.failure("Unknown action for handle_response")

    def execute_async(self, callback: Callable[[Any], None]):
        """
        Executes the command asynchronously using BaseCommand's async execution.
        The callback will be called with the result data.

        Args:
            callback: A function to call with the result of the command.
        """

        # BaseCommand의 비동기 실행을 사용하도록 콜백 래핑
        def base_command_callback(result: CommandResult):
            if callback:
                callback(result.data if result.success else None)

        # BaseCommand의 비동기 실행 메서드 호출
        super().execute_async(base_command_callback)
