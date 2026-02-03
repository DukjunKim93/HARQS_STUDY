#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Interface Command Class
"""

import logging
import re
from typing import List, Any, Dict

from QSUtils.command.base_command import BaseCommand
from QSUtils.command.command_constants import CommandResult, SystemCommands
from QSUtils.command.command_validator import NetworkInterfaceCommandValidator


class NetworkInterfaceCommand(BaseCommand):
    """
    Command class for getting network interface information.
    """

    def __init__(self, device, interface: str = "p2p0"):
        """
        Initialize the network interface command.

        Args:
            device: ADBDevice instance for executing commands
            interface: Network interface name (default: "p2p0")
        """
        super().__init__(device)
        self.interface = interface
        self.logger = logging.getLogger(__name__)

        # 특화된 Validator 사용
        self.validator = NetworkInterfaceCommandValidator(
            device, self.__class__.__name__
        )

        # 파라미터 검증
        validation_result = self.validator.validate_parameters(interface=interface)
        if validation_result is not None:
            raise ValueError(validation_result.error)

    def get_shell_command(self) -> str:
        """
        Returns the shell command string to be executed.
        Uses 'ifconfig' command to get interface information for better compatibility.
        """
        return SystemCommands.IFCONFIG_TEMPLATE.format(interface=self.interface)

    def _log_debug_info(self, output: str, lines: List[str]):
        """디버그 정보를 로깅하는 헬퍼 메서드"""
        self.logger.debug(f"NetworkInterfaceCommand: Raw output: {output}")
        self.logger.debug(f"NetworkInterfaceCommand: Parsed lines: {lines}")

    def _parse_status_line(self, status_line: str) -> Dict:
        """Parse network interface status line information."""
        status_info = {"status": "N/A", "flags": [], "mtu": "N/A", "metric": "N/A"}

        status_pattern = r"\b(UP)\b.*?\b(BROADCAST)\b.*?\b(RUNNING)\b.*?\b(MULTICAST)\b.*?\bMTU:(\d+)\b.*?\bMetric:(\d+)\b"
        match = re.search(status_pattern, status_line)

        if match:
            status_info["status"] = match.group(1)  # UP
            status_info["flags"] = [match.group(3)]  # Only include RUNNING
            status_info["mtu"] = match.group(5)
            status_info["metric"] = match.group(6)
        else:
            flexible_pattern = r"\b(UP)\b.*?\bMTU:(\d+)\b.*?\bMetric:(\d+)\b"
            flex_match = re.search(flexible_pattern, status_line)
            if flex_match:
                status_info["status"] = flex_match.group(1)
                status_info["mtu"] = flex_match.group(2)
                status_info["metric"] = flex_match.group(3)
                status_info["flags"] = []
                if "RUNNING" in status_line:
                    status_info["flags"].append("RUNNING")

        return status_info

    def _parse_ip_addresses(self, output: str) -> Dict:
        """Parse IPv4 and IPv6 addresses from network interface output."""
        ip_info = {"ipv4": "N/A", "ipv6": "N/A"}

        ipv4_pattern = r"inet\s+addr:(\d+\.\d+\.\d+\.\d+)"
        ipv4_match = re.search(ipv4_pattern, output)
        if ipv4_match:
            ip_info["ipv4"] = ipv4_match.group(1)

        ipv6_pattern = r"inet6\s+addr:\s*([0-9a-fA-F:]+/\d+)"
        ipv6_match = re.search(ipv6_pattern, output)
        if ipv6_match:
            ip_info["ipv6"] = ipv6_match.group(1).split("/")[0]
        else:
            ipv6_fallback_pattern = r"inet6\s+([0-9a-fA-F:]+/\d+)"
            ipv6_fallback_match = re.search(ipv6_fallback_pattern, output)
            if ipv6_fallback_match:
                ip_info["ipv6"] = ipv6_fallback_match.group(1).split("/")[0]

        return ip_info

    def parse_interface_info(self, output: str) -> dict:
        """
        Parse the IPv4, IPv6 addresses and interface status information from the ifconfig command output.

        Args:
            output: The command output string

        Returns:
            A dictionary containing interface information
        """
        result = {
            "ipv4": "N/A",
            "ipv6": "N/A",
            "status": "N/A",
            "flags": [],
            "mtu": "N/A",
            "metric": "N/A",
        }

        lines = output.strip().split("\n") if output else []
        self._log_debug_info(output, lines)

        if not lines:
            return result

        status_line = None
        for line in lines:
            if "UP" in line and "MTU:" in line:
                status_line = line.strip()
                break

        if status_line:
            result.update(self._parse_status_line(status_line))

        result.update(self._parse_ip_addresses(output))

        self.logger.debug(f"NetworkInterfaceCommand: Final result: {result}")
        return result

    def handle_response(
        self, response_lines: List[str]
    ) -> CommandResult[Dict[str, Any]]:
        """
        Handle the response from the network interface command.

        Args:
            response_lines: List of response lines from the command output

        Returns:
            CommandResult[Dict[str, Any]] containing the parsed interface information
        """
        if response_lines and len(response_lines) > 0:
            output = "\n".join(response_lines)
            interface_info = self.parse_interface_info(output)
            return CommandResult.success(interface_info)
        else:
            return CommandResult.failure("No response from network interface command")
