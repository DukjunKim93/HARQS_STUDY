#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command handler for reading and parsing /data/acm/.preference_data.
"""

import json
import re
from typing import Dict, Optional, List

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.base_command import BaseCommand
from QSUtils.command.command_constants import PreferenceDataKeys, CommandResult


class PreferenceDataCommandHandler(BaseCommand[Dict[str, str]]):
    """
    Handles reading /data/acm/.preference_data and extracting specific values.
    """

    def __init__(self, device):
        """
        Initialize the preference data command handler.

        Args:
            device: ADBDevice instance for executing commands
        """
        super().__init__(device)

    def get_shell_command(self) -> str:
        """
        Returns the shell command to read the preference data file.
        """
        from QSUtils.command.command_constants import SystemCommands

        return SystemCommands.CAT_PREFERENCE_DATA

    def _parse_json_safely(self, json_string: str) -> Optional[dict]:
        """
        JSON 문자열을 안전하게 파싱합니다. 실패 시 보정을 시도합니다.

        Args:
            json_string: 파싱할 JSON 문자열

        Returns:
            Optional[dict]: 파싱된 딕셔너리 또는 None
        """
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            LOGD(f"PreferenceDataCommandHandler: Failed to parse JSON. Error: {e}")
            LOGD(f"PreferenceDataCommandHandler: Raw string: {json_string}")

            # Try to fix common JSON formatting issues and parse again
            try:
                # Replace unquoted property names with quoted ones
                # This handles cases like {key: "value"} -> {"key": "value"}
                fixed_json = re.sub(
                    r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_./-]*)(\s*:)",
                    r'\1"\2"\3',
                    json_string,
                )
                LOGD(
                    f"PreferenceDataCommandHandler: Attempting to parse fixed JSON: {fixed_json}"
                )
                preference_data = json.loads(fixed_json)
                LOGD(f"PreferenceDataCommandHandler: Successfully parsed fixed JSON")
                return preference_data
            except json.JSONDecodeError as e2:
                LOGD(
                    f"PreferenceDataCommandHandler: Failed to parse fixed JSON. Error: {e2}"
                )
                return None

    def _extract_value(self, data: dict, key: str, default: str = "N/A") -> str:
        """
        딕셔너리에서 키 값을 추출합니다. 키가 없으면 기본값을 반환합니다.

        Args:
            data: 데이터 딕셔너리
            key: 추출할 키
            default: 기본값

        Returns:
            str: 추출된 값 또는 기본값
        """
        if key in data:
            return data[key]
        else:
            LOGD(
                f"PreferenceDataCommandHandler: Key '{key}' not found in preference_data."
            )
            return default

    def _extract_grouptype_from_multiroom_info(self, multiroom_info_str: str) -> str:
        """
        multiroom_info 문자열에서 grouptype 값을 추출합니다.

        Args:
            multiroom_info_str: "grouptype=M_TV mainspkip=192.168.102.22 ..." 형식의 문자열

        Returns:
            str: 추출된 grouptype 값 또는 "N/A"
        """
        if not multiroom_info_str:
            return "N/A"

        # multiroom_info_str is like "grouptype=M_TV mainspkip=192.168.102.22 ..."
        parts = multiroom_info_str.split()
        for part in parts:
            if part.startswith(f"{PreferenceDataKeys.GROUPTYPE}="):
                return part.split("=", 1)[1]

        return "N/A"

    def handle_response(
        self, response_lines: List[str]
    ) -> CommandResult[Dict[str, str]]:
        """
        Parses the output of 'cat /data/acm/.preference_data'.

        Args:
            response_lines: A list containing the single line of JSON string output from the command.

        Returns:
            CommandResult[Dict[str, str]]: 성공 시 파싱된 값 딕셔너리, 실패 시 에러 메시지
        """
        if not response_lines or len(response_lines) == 0:
            LOGD("PreferenceDataCommandHandler: No response data received.")
            return CommandResult.failure("No response data received")

        # Join all lines to reconstruct the complete JSON string
        raw_json_string = "".join(response_lines).strip()

        preference_data = self._parse_json_safely(raw_json_string)
        if preference_data is None:
            return CommandResult.failure("Failed to parse preference data JSON")

        parsed_values = {}

        # Extract com.harman.acm_service.state
        parsed_values["acm_service_state"] = self._extract_value(
            preference_data, PreferenceDataKeys.ACM_SERVICE_STATE, "N/A"
        )

        # Extract grouptype from db/waapp/multiroom_info
        multiroom_info_str = self._extract_value(
            preference_data, PreferenceDataKeys.MULTIROOM_INFO, ""
        )
        parsed_values["multiroom_grouptype"] = (
            self._extract_grouptype_from_multiroom_info(multiroom_info_str)
        )

        # Extract db/waapp/multiroom_mode
        parsed_values["multiroom_mode"] = self._extract_value(
            preference_data, PreferenceDataKeys.MULTIROOM_MODE, "N/A"
        )

        LOGD(f"PreferenceDataCommandHandler: Parsed values: {parsed_values}")
        return CommandResult.success(parsed_values)
