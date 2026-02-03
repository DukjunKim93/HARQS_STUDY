#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handles the 'pp symphony' command.
"""

from typing import Dict

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_dsp_audio_setting import DspAudioSettingCommand
from QSUtils.command.command_constants import SymphonyConstants, CommandResult


class SymphonyStatusCommandHandler(DspAudioSettingCommand[Dict[str, str]]):
    """Handles the 'pp symphony' command."""

    def __init__(self, device):
        super().__init__(device)

    @property
    def command_str(self) -> str:
        return '{"pos_args":["pp symphony"]}'

    def _get_sound_mode_text(self, mode_value: int) -> str:
        """
        Sound mode 값을 텍스트로 변환

        Args:
            mode_value: 모드 값

        Returns:
            str: 변환된 텍스트
        """
        return SymphonyConstants.SOUND_MODES.get(mode_value, str(mode_value))

    def _get_qs_state_text(self, state_value: int) -> str:
        """
        QS 상태 값을 텍스트로 변환

        Args:
            state_value: 상태 값

        Returns:
            str: 변환된 텍스트
        """
        return SymphonyConstants.QS_STATES.get(state_value, "Unknown")

    def _get_mode_type_text(self, mode_type_value: int) -> str:
        """
        Mode type 값을 텍스트로 변환

        Args:
            mode_type_value: 모드 타입 값

        Returns:
            str: 변환된 텍스트
        """
        return SymphonyConstants.MODE_TYPES.get(mode_type_value, "Unknown")

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[Dict[str, str]]:
        """
        Process parsed WAMP response data to extract symphony status information.

        Args:
            parsed_data: The parsed JSON data from WAMP response

        Returns:
            CommandResult[Dict[str, str]]: 파싱된 심포니 상태 정보
        """
        # pos_args에서 3개 값 추출
        if "pos_args" in parsed_data and isinstance(parsed_data["pos_args"], list):
            if len(parsed_data["pos_args"]) >= 3:
                try:
                    arg1, arg2, arg3 = (
                        parsed_data["pos_args"][0],
                        parsed_data["pos_args"][1],
                        parsed_data["pos_args"][2],
                    )

                    # QS on/off (args[0])
                    qs_state = self._get_qs_state_text(arg1)

                    # Sound mode (args[1])
                    sound_mode = self._get_sound_mode_text(arg2)

                    # Mode type (args[2])
                    mode_type = self._get_mode_type_text(arg3)

                    response_data = {
                        "qs_state": qs_state,
                        "sound_mode": sound_mode,
                        "mode_type": mode_type,
                    }

                    LOGD(f"SymphonyStatusCommandHandler: Final result: {response_data}")
                    return CommandResult.success(response_data)
                except (IndexError, ValueError) as e:
                    return CommandResult.failure(
                        f"Failed to process symphony status values: {parsed_data['pos_args']}"
                    )
            else:
                return CommandResult.failure("pos_args does not contain 3 values")
        else:
            return CommandResult.failure("pos_args not found or not a list in response")
