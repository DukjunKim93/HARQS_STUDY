#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handles the 'pp symphony volume add' command.
"""

from QSUtils.command.cmd_dsp_audio_setting import DspAudioSettingCommand
from QSUtils.command.command_constants import CommandResult


class SymphonyVolumeAddCommandHandler(DspAudioSettingCommand[int]):
    """Handles the 'pp symphony volume add' command."""

    def __init__(self, device):
        super().__init__(device)

    @property
    def command_str(self) -> str:
        return '{"pos_args":["pp symphony volume add"]}'

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[int]:
        """
        Process parsed WAMP response data to extract symphony volume add value.

        Returns:
            CommandResult[int]: 성공 시 심포니 볼륨 추가 값, 실패 시 에러 메시지
        """
        # pos_args에서 첫 번째 값 추출
        if "pos_args" in parsed_data and isinstance(parsed_data["pos_args"], list):
            if len(parsed_data["pos_args"]) > 0:
                try:
                    volume_add_value = int(parsed_data["pos_args"][0])
                    return CommandResult.success(volume_add_value)
                except (ValueError, TypeError) as e:
                    return CommandResult.failure(
                        f"Failed to convert symphony volume add value to int: {parsed_data['pos_args'][0]}"
                    )
            else:
                return CommandResult.failure("pos_args is empty in response")
        else:
            return CommandResult.failure("pos_args not found or not a list in response")
