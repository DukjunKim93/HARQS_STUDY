#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test WAMP Client Abstract Base Class
"""

import json
import re
from abc import abstractmethod
from typing import List, Any

from QSUtils.Utils.Logger import LOGD
from QSUtils.command.base_command import BaseCommand
from QSUtils.command.command_constants import CommandResult, WampCommandType


class TestWampCommand(BaseCommand):
    """
    Abstract base class for handling commands that use the test-wamp-client utility.
    """

    def __init__(self, device, command_type: WampCommandType, wamp_component: str):
        """
        Initialize the test WAMP command.

        Args:
            device: ADBDevice instance for executing commands
            command_type: The WAMP command type (CALL or PUBLISH)
            wamp_component: The WAMP component to target (e.g., com.harman.dsp.GetAudioSetting)
        """
        super().__init__(device)
        self.command_type = command_type
        self.wamp_component = wamp_component

    def get_shell_command(self) -> str:
        """
        Returns the shell command string to be executed.
        """
        flag = "-c" if self.command_type == WampCommandType.CALL else "-n"
        return f"test-wamp-client {flag} {self.wamp_component} -a '{self.command_str}'"

    @property
    @abstractmethod
    def command_str(self) -> str:
        """The JSON command string to be passed as an argument to test-wamp-client."""
        pass

    @staticmethod
    def parse_wamp_publish_response(
        response_lines: List[str], expected_component: str, class_name: str
    ) -> CommandResult:
        """
        WAMP publish 응답을 파싱하고 컴포넌트를 검증합니다.

        Args:
            response_lines: 응답 라인 목록
            expected_component: 예상되는 WAMP 컴포넌트
            class_name: 호출 클래스 이름 (로깅용)

        Returns:
            CommandResult: 성공 시 빈 dict, 실패 시 에러 메시지
        """
        if not response_lines:
            error_msg = "No response from device"
            LOGD(f"{class_name}: {error_msg}")
            return CommandResult.failure(error_msg)

        try:
            # 'Sending notification:' 라인에서 WAMP 컴포넌트 추출하여 검증
            found_component = None
            published_event_found = False

            for line in response_lines:
                if "Sending notification:" in line:
                    # 'Sending notification: `com.harman.ucd.UpdateDeviceName`'에서 컴포넌트 추출
                    match = re.search(r"Sending notification:\s*`([^`]+)`", line)
                    if match:
                        found_component = match.group(1)

                if "Published event" in line:
                    published_event_found = True

            # WAMP 컴포넌트 검증
            if found_component is None:
                error_msg = "No 'Sending notification:' found in response"
                LOGD(f"{class_name}: {error_msg}")
                return CommandResult.failure(error_msg)

            if found_component != expected_component:
                error_msg = f"WAMP component mismatch. Expected: {expected_component}, Found: {found_component}"
                LOGD(f"{class_name}: {error_msg}")
                return CommandResult.failure(error_msg)

            # Published event 확인
            if not published_event_found:
                error_msg = "No 'Published event' found in response"
                LOGD(f"{class_name}: {error_msg}")
                return CommandResult.failure(error_msg)

            LOGD(f"{class_name}: WAMP publish component verified: {found_component}")
            LOGD(f"{class_name}: Published event confirmed")

            # publish는 별도의 데이터가 없으므로 빈 dict 반환
            return CommandResult.success({})

        except Exception as e:
            error_msg = f"Exception during parsing: {str(e)}"
            LOGD(f"{class_name}: {error_msg}")
            return CommandResult.failure(error_msg)

    @staticmethod
    def parse_wamp_response(
        response_lines: List[str], expected_component: str, class_name: str
    ) -> CommandResult:
        """
        WAMP 응답을 파싱하고 컴포넌트를 검증합니다.

        Args:
            response_lines: 응답 라인 목록
            expected_component: 예상되는 WAMP 컴포넌트
            class_name: 호출 클래스 이름 (로깅용)

        Returns:
            CommandResult: 성공 시 파싱된 dict, 실패 시 에러 메시지
        """
        if not response_lines:
            error_msg = "No response from device"
            LOGD(f"{class_name}: {error_msg}")
            return CommandResult.failure(error_msg)

        try:
            # 'Calling remote procedure:' 라인에서 WAMP 컴포넌트 추출하여 검증
            found_component = None
            for line in response_lines:
                if "Calling remote procedure:" in line:
                    # 'Calling remote procedure: `com.harman.system.getDevInfoDynamic`'에서 컴포넌트 추출
                    match = re.search(r"Calling remote procedure:\s*`([^`]+)`", line)
                    if match:
                        found_component = match.group(1)
                        break

            # WAMP 컴포넌트 검증
            if found_component is None:
                error_msg = "No 'Calling remote procedure:' found in response"
                LOGD(f"{class_name}: {error_msg}")
                return CommandResult.failure(error_msg)

            if found_component != expected_component:
                error_msg = f"WAMP component mismatch. Expected: {expected_component}, Found: {found_component}"
                LOGD(f"{class_name}: {error_msg}")
                return CommandResult.failure(error_msg)

            LOGD(f"{class_name}: WAMP component verified: {found_component}")

            # 'Received call result:' 라인 찾기
            json_start_index = -1
            for i, line in enumerate(response_lines):
                if "Received call result:" in line:
                    json_start_index = i + 1  # 다음 라인부터 JSON 시작
                    break

            if json_start_index == -1:
                error_msg = "No 'Received call result:' found in response"
                LOGD(f"{class_name}: {error_msg}")
                return CommandResult.failure(error_msg)

            # 'Received call result:' 이후의 모든 라인을 합침
            json_lines = response_lines[json_start_index:]
            json_str = "".join(json_lines)  # 줄바꿈 없이 합침

            LOGD(f"{class_name}: JSON lines: {json_lines}")
            LOGD(f"{class_name}: Combined JSON string: {json_str}")

            # JSON 파싱
            parsed_data = json.loads(json_str)
            LOGD(f"{class_name}: Parsed data: {parsed_data}")

            return CommandResult.success(parsed_data)

        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {str(e)}"
            LOGD(f"{class_name}: {error_msg}")
            return CommandResult.failure(error_msg)
        except Exception as e:
            error_msg = f"Exception during parsing: {str(e)}"
            LOGD(f"{class_name}: {error_msg}")
            return CommandResult.failure(error_msg)

    def handle_response(self, response_lines: List[str]) -> CommandResult[Any]:
        """
        Default implementation that handles common WAMP response parsing.
        Subclasses can override this method or use the template method pattern.

        Args:
            response_lines: The list of response lines from the command output.

        Returns:
            CommandResult[Any]: Parsed data from the response.
        """
        # command_type에 따라 다른 파싱 메서드 사용
        if self.command_type == WampCommandType.PUBLISH:
            result = self.parse_wamp_publish_response(
                response_lines, self.wamp_component, self.__class__.__name__
            )
        else:
            result = self.parse_wamp_response(
                response_lines, self.wamp_component, self.__class__.__name__
            )

        if not result.success:
            return result

        # 하위 클래스에서 구체적인 데이터 처리를 위한 템플릿 메서드 호출
        return self.process_parsed_data(result.data)

    def process_parsed_data(self, parsed_data: dict) -> CommandResult[Any]:
        """
        Template method for processing parsed WAMP response data.
        Subclasses should override this method to implement specific data processing logic.

        Args:
            parsed_data: The parsed JSON data from WAMP response

        Returns:
            CommandResult[Any]: Processed result data
        """
        # 기본 구현: 파싱된 데이터를 그대로 반환
        # 하위 클래스에서 반드시 오버라이드해야 함
        return CommandResult.success(parsed_data)
