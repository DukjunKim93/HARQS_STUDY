#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command for saving device name using test-wamp-client.
"""

from typing import Any

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_test_wamp import TestWampCommand
from QSUtils.command.command_constants import CommandResult, WampCommandType


class SaveDevNameCommand(TestWampCommand):
    """
    Command class for saving device name using test-wamp-client.
    """

    def __init__(self, device, device_name: str = None):
        """
        Initialize the save device name command.

        Args:
            device: ADBDevice instance for executing commands
            device_name: Device name to save (optional)
        """
        # 부모 클래스 초기화
        TestWampCommand.__init__(
            self, device, WampCommandType.CALL, "com.harman.ucd.SaveDevName"
        )

        # 파라미터 검증
        if device_name is None:
            raise ValueError("Device name is required")

        self.device_name = device_name

    @property
    def command_str(self) -> str:
        """
        Returns the JSON command string to be executed.
        """
        # JSON 인자 배열에 device_name 추가
        return f'{{"pos_args":["{self.device_name}"]}}'

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[Any]:
        """
        Process parsed WAMP response data to check if device name was saved successfully.

        Args:
            parsed_data: The parsed JSON data from WAMP response

        Returns:
            CommandResult[Any]: 성공 시 처리된 데이터, 실패 시 에러 메시지
        """
        # pos_args에서 첫 번째 값 추출
        if "pos_args" in parsed_data and isinstance(parsed_data["pos_args"], list):
            if len(parsed_data["pos_args"]) > 0:
                success_value = parsed_data["pos_args"][0]
                if success_value == "Success":
                    LOGD(
                        f"SaveDevNameCommand: Device name saved successfully: {self.device_name}"
                    )
                    return CommandResult.success(True)
                else:
                    return CommandResult.failure(
                        f"Failed to save device name. Response: {success_value}"
                    )
            else:
                return CommandResult.failure("pos_args is empty in response")
        else:
            return CommandResult.failure("pos_args not found or not a list in response")

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
                callback(result.success)

        # BaseCommand의 비동기 실행 메서드 호출
        super().execute_async(base_command_callback)
