#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handles the 'pp symphony group' command.
"""

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_dsp_audio_setting import DspAudioSettingCommand
from QSUtils.command.command_constants import SymphonyConstants, CommandResult


class SymphonyGroupCommandHandler(DspAudioSettingCommand[str]):
    """Handles the 'pp symphony group' command."""

    def __init__(self, device):
        super().__init__(device)

    @property
    def command_str(self) -> str:
        return '{"pos_args":["pp symphony group"]}'

    def _get_mode_text(self, mode_value: int) -> str:
        """Mode 값을 텍스트로 변환"""
        return SymphonyConstants.GROUP_MODES.get(mode_value, "Unknown")

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[str]:
        """
        Process parsed WAMP response data to extract symphony group mode.

        Returns:
            CommandResult[str]: 성공 시 심포니 그룹 모드 텍스트, 실패 시 에러 메시지
        """
        # pos_args에서 첫 번째 값 추출
        if "pos_args" in parsed_data and isinstance(parsed_data["pos_args"], list):
            if len(parsed_data["pos_args"]) > 0:
                mode_value = parsed_data["pos_args"][0]
                mode_text = self._get_mode_text(mode_value)
                LOGD(f"SymphonyGroupCommandHandler: Mode text: {mode_text}")
                return CommandResult.success(mode_text)
            else:
                return CommandResult.failure("pos_args is empty in response")
        else:
            return CommandResult.failure("pos_args not found or not a list in response")
