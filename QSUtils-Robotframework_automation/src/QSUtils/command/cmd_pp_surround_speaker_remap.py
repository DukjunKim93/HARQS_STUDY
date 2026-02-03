#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handles the 'pp surround speaker remap' command.
"""

from typing import List

from QSUtils.command.cmd_dsp_audio_setting import DspAudioSettingCommand
from QSUtils.command.command_constants import CommandResult


class SurroundSpeakerRemapCommandHandler(DspAudioSettingCommand[List[int]]):
    """Handles the 'pp surround speaker remap' command."""

    def __init__(self, device):
        super().__init__(device)

    @property
    def command_str(self) -> str:
        return '{"pos_args":["pp surround speaker remap"]}'

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[List[int]]:
        """
        Process parsed WAMP response data to extract surround speaker remap values.

        Returns:
            CommandResult[List[int]]: 성공 시 서라운드 스피커 리맵 값 리스트, 실패 시 에러 메시지
        """
        # pos_args에서 5개 값 추출
        if "pos_args" in parsed_data and isinstance(parsed_data["pos_args"], list):
            if len(parsed_data["pos_args"]) >= 5:
                try:
                    surround_values = [int(val) for val in parsed_data["pos_args"][:5]]
                    return CommandResult.success(surround_values)
                except (ValueError, TypeError) as e:
                    return CommandResult.failure(
                        f"Failed to convert surround speaker remap values to int: {parsed_data['pos_args'][:5]}"
                    )
            else:
                return CommandResult.failure("pos_args does not contain 5 values")
        else:
            return CommandResult.failure("pos_args not found or not a list in response")
