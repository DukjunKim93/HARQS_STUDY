#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command for getting device information including device name.
"""

from typing import Any

from QSUtils.Utils import LOGD
from QSUtils.command.cmd_test_wamp import TestWampCommand
from QSUtils.command.command_constants import CommandResult, WampCommandType


class GetDeviceInfoCommand(TestWampCommand):
    """
    Command class for getting device information using test-wamp-client.
    """

    def __init__(self, device):
        """
        Initialize the get device info command.

        Args:
            device: ADBDevice instance for executing commands
        """
        # 부모 클래스 초기화
        TestWampCommand.__init__(
            self, device, WampCommandType.CALL, "com.harman.system.getDevInfoDynamic"
        )

    @property
    def command_str(self) -> str:
        """
        Returns the JSON command string to be executed.
        """
        return '{"pos_args":[]}'

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[Any]:
        """
        Process parsed WAMP response data to extract device info.

        Args:
            parsed_data: The parsed JSON data from WAMP response

        Returns:
            CommandResult[Any]: Device info from nam_args field
        """
        # The actual device info is in "nam_args".
        if "nam_args" in parsed_data and isinstance(parsed_data["nam_args"], dict):
            LOGD(
                f"GetDeviceInfoCommand: Final 'nam_args' content: {parsed_data['nam_args']}"
            )
            return CommandResult.success(parsed_data["nam_args"])
        else:
            return CommandResult.failure("nam_args not found or not a dict in response")

    def execute_async(self, callback):
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
