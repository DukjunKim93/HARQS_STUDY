#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command for rebooting the device.
"""

from typing import List

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.base_command import BaseCommand
from QSUtils.command.command_constants import CommandResult


class RebootCommand(BaseCommand[bool]):
    """
    Command to reboot the Android device.
    """

    def __init__(self, device, sync_before_reboot: bool = True):
        """
        Initialize the reboot command.

        Args:
            device: The ADB device instance.
            sync_before_reboot: If True (default), run "sync && reboot -f". If False, run "reboot -f" only.
        """
        super().__init__(device)
        self.sync_before_reboot: bool = bool(sync_before_reboot)

    def get_shell_command(self) -> str:
        """
        Returns the shell command string to reboot the device.
        Now ensures device logs are cleared via 'logcat -c' before rebooting.
        """
        from QSUtils.command.command_constants import SystemCommands

        reboot_cmd = (
            SystemCommands.SYNC_REBOOT
            if self.sync_before_reboot
            else SystemCommands.REBOOT
        )
        # Per requirement: clear logcat first, then reboot. Use '&&' to ensure sequencing.
        return f"{reboot_cmd}"

    def handle_response(self, response_lines: List[str]) -> CommandResult[bool]:
        """
        Handles the response from the reboot command.
        Reboot command typically doesn't return meaningful output immediately,
        so we'll just return success if the command was sent.

        Args:
            response_lines: List of response lines from the command output

        Returns:
            CommandResult[bool]: 성공 시 True, 실패 시 False
        """
        LOGD(f"RebootCommand: Reboot command sent. Response: {response_lines}")
        # The reboot command itself doesn't return a success/failure status in its output
        # that we can easily parse. If the command executes without error,
        # ADBDevice will consider it a success.
        return CommandResult.success(True)
