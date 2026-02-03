#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSP Audio Setting Abstract Base Class
"""

from abc import abstractmethod
from typing import TypeVar, Generic

from QSUtils.command.cmd_test_wamp import TestWampCommand
from QSUtils.command.command_constants import CommandResult, WampCommandType

# 타입 변수 정의
T = TypeVar("T")


class DspAudioSettingCommand(TestWampCommand, Generic[T]):
    """
    Abstract base class for handling a specific DSP audio setting command and its response.
    """

    def __init__(self, device):
        """
        Initialize the DSP audio setting command.

        Args:
            device: ADBDevice instance for executing commands
        """
        TestWampCommand.__init__(
            self, device, WampCommandType.CALL, "com.harman.dsp.GetAudioSetting"
        )
        # Debug mode flag is now handled by the global logger, no need for this instance variable
        # self.debug_enabled = False

    @property
    @abstractmethod
    def command_str(self) -> str:
        """The JSON command string to be executed."""
        pass

    @abstractmethod
    def process_parsed_data(self, parsed_data: dict) -> CommandResult[T]:
        """
        Process parsed WAMP response data for DSP audio setting commands.

        Args:
            parsed_data: The parsed JSON data from WAMP response

        Returns:
            CommandResult[T]: Parsed data from the response. The type of data depends on the specific command.
            e.g., an integer for speaker remap, a list of integers for surround remap,
            or a string for status commands.
        """
        pass
