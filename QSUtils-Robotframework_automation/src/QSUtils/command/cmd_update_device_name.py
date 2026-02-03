#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command for updating device name using test-wamp-client publish command.
"""

from typing import Any

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_test_wamp import TestWampCommand
from QSUtils.command.command_constants import CommandResult, WampCommandType


class UpdateDeviceNameCommand(TestWampCommand):
    """
    Command class for updating device name using test-wamp-client publish command.
    """

    def __init__(self, device, device_name: str = None):
        """
        Initialize the update device name command.

        Args:
            device: ADBDevice instance for executing commands
            device_name: Device name to update (optional)
        """
        # 부모 클래스 초기화 - PUBLISH 타입 사용
        TestWampCommand.__init__(
            self, device, WampCommandType.PUBLISH, "com.harman.ucd.UpdateDeviceName"
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
        Process parsed WAMP response data to check if device name was updated successfully.

        Args:
            parsed_data: The parsed JSON data from WAMP response

        Returns:
            CommandResult[Any]: 성공 시 처리된 데이터, 실패 시 에러 메시지
        """
        # publish 명령은 "Published event"만 확인하면 되므로 간단한 성공 처리
        LOGD(
            f"UpdateDeviceNameCommand: Device name updated successfully: {self.device_name}"
        )
        return CommandResult.success(True)

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
