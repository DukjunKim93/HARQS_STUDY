#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coredump Monitor Command for QSMonitor application.
Monitors /data/var/lib/systemd/systemd-coredump/ directory for coredump files.
"""

from typing import List

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.base_command import BaseCommand
from QSUtils.command.command_constants import CommandResult


class CoredumpMonitorCommandHandler(BaseCommand):
    """
    Command handler for monitoring coredump files on Android device.
    """

    def __init__(self, device):
        """
        Initialize the coredump monitor command handler.

        Args:
            device: ADBDevice instance for executing commands
        """
        super().__init__(device)
        self.coredump_path = "/data/var/lib/systemd/systemd-coredump/"

    def get_shell_command(self) -> str:
        """
        Returns the shell command to list coredump files.
        """
        from QSUtils.command.command_constants import SystemCommands

        return SystemCommands.LS_TEMPLATE.format(path=self.coredump_path)

    def handle_response(self, response_lines: List[str]) -> CommandResult[List[str]]:
        """
        Handles the response from the coredump directory listing command.

        Args:
            response_lines: List of response lines from the command output

        Returns:
            CommandResult[List[str]]: 성공 시 coredump 파일 리스트, 실패 시 에러 메시지
        """
        if not response_lines:
            LOGD("CoredumpMonitorCommandHandler: No response data received.")
            return CommandResult.success([])  # 빈 디렉토리는 정상 상태

        coredump_files = []

        for line in response_lines:
            line = line.strip()
            if line and not line.startswith("ls:"):  # ls 에러 메시지 필터링
                # coredump 파일 패턴 확인 (보통 core.패턴 또는 .core 패턴)
                if (
                    line.startswith("core.")
                    or line.endswith(".core")
                    or "core" in line.lower()
                ):
                    coredump_files.append(line)
                    LOGD(f"CoredumpMonitorCommandHandler: Found coredump file: {line}")

        LOGD(
            f"CoredumpMonitorCommandHandler: Total coredump files found: {len(coredump_files)}"
        )
        return CommandResult.success(coredump_files)
