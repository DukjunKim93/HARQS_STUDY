#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB Utility functions for device management.
Provides common ADB operations used across the application.
"""

import subprocess
from typing import List, Optional

from QSUtils.Utils.Logger import LOGD


class ADBUtils:
    """Utility class for common ADB operations."""

    @staticmethod
    def execute_adb_command(args: List[str], timeout: int = 10) -> Optional[str]:
        """
        Execute a general ADB command and return the output.

        Args:
            args: ADB command arguments (without 'adb' prefix)
            timeout: Command timeout in seconds

        Returns:
            Command stdout as string if successful, None otherwise
        """
        try:
            cmd = ["adb"] + args
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                LOGD(
                    f"ADBUtils: Command failed: {' '.join(cmd)}, return code: {result.returncode}"
                )
                LOGD(f"ADBUtils: Error output: {result.stderr.strip()}")
                return None

        except subprocess.TimeoutExpired as e:
            LOGD(f"ADBUtils: Command timeout: {' '.join(args)}, error: {e}")
            return None
        except Exception as e:
            LOGD(f"ADBUtils: Command exception: {' '.join(args)}, error: {e}")
            return None

    @staticmethod
    def list_connected_devices(timeout: int = 3) -> List[str]:
        """
        Get list of currently connected ADB devices.

        Args:
            timeout: Command timeout in seconds

        Returns:
            List of device serial numbers that are in 'device' state
        """
        output = ADBUtils.execute_adb_command(["devices"], timeout)
        if not output:
            return []

        serials = []
        for line in output.splitlines()[1:]:  # Skip header line
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                serials.append(parts[0])

        return serials

    @staticmethod
    def is_device_connected(serial: str, timeout: int = 3) -> bool:
        """
        Check if a specific device is connected and authorized.

        Args:
            serial: Device serial number to check
            timeout: Command timeout in seconds

        Returns:
            True if device is connected and in 'device' state, False otherwise
        """
        connected_devices = ADBUtils.list_connected_devices(timeout)
        return serial in connected_devices

    @staticmethod
    def execute_shell_command(
        serial: str, shell_command: str, timeout: int = 30
    ) -> Optional[str]:
        """
        Execute a shell command on a specific device.

        Args:
            serial: Device serial number
            shell_command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Command output as string if successful, None otherwise
        """
        args = ["-s", serial, "shell", shell_command]
        return ADBUtils.execute_adb_command(args, timeout)

    @staticmethod
    def get_device_state(serial: str, timeout: int = 3) -> Optional[str]:
        """
        Get the state of a specific device.

        Args:
            serial: Device serial number
            timeout: Command timeout in seconds

        Returns:
            Device state ('device', 'unauthorized', 'offline', etc.) or None if error
        """
        output = ADBUtils.execute_adb_command(["devices"], timeout)
        if not output:
            return None

        for line in output.splitlines()[1:]:  # Skip header line
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 2 and parts[0] == serial:
                return parts[1]

        return None

    @staticmethod
    def is_android_device_vendor(vendor_id: str) -> bool:
        """
        Check if a USB vendor ID corresponds to an Android device manufacturer.

        Args:
            vendor_id: USB vendor ID string

        Returns:
            True if vendor ID is known to manufacture Android devices
        """
        android_vendor_ids = [
            "18d1",  # Google
            "04e8",  # Samsung
            "1004",  # LG
            "22b8",  # Motorola
            "0bb4",  # HTC
            "0fce",  # Sony
            "0e8d",  # MediaTek
            "1949",  # Amazon
            "2207",  # Intel
            "2a45",  # Microsoft
            "18d1",  # Google (again for completeness)
        ]

        return vendor_id.lower() in android_vendor_ids
