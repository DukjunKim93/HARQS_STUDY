#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB Device Controller for managing individual Android devices.
Provides unified device monitoring and command execution functionality.
"""

import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Any, Callable

from PySide6.QtCore import QObject, Signal, QTimer, QThread

# Windows compatibility: Conditional import of pyudev
try:
    import pyudev

    PYUDEV_AVAILABLE = True
except ImportError:
    PYUDEV_AVAILABLE = False

    # Create dummy pyudev classes for Windows compatibility
    class pyudev:
        class Context:
            pass

        class Monitor:
            @staticmethod
            def from_netlink(context):
                raise ImportError("pyudev not available on Windows")

            def filter_by(self, subsystem):
                raise ImportError("pyudev not available on Windows")

            def poll(self, timeout=None):
                raise ImportError("pyudev not available on Windows")


from QSUtils.ADBDevice.ADBUtils import ADBUtils
from QSUtils.Utils.Logger import LOGD
from QSUtils.command.base_command import BaseCommand


class ADBDevice(QObject):
    """
    Manages a single ADB device with unified monitoring and command execution.
    Replaces the separate ADBDevice and ADBDeviceMonitor for a single device.
    """

    # Signals for device connection status
    deviceConnected = Signal()  # Emitted when this specific device is connected
    deviceDisconnected = Signal()  # Emitted when this specific device is disconnected

    # Signal for command execution results
    commandExecuted = Signal(str, object)  # command_name, result

    # Internal signal to marshal callables onto this object's Qt thread
    _invokeOnThisThread = Signal(object)

    def __init__(self, serial: str, parent=None):
        """
        Initialize the ADB device controller.

        Args:
            serial: Device serial number
            parent: Parent Qt object
        """
        super().__init__(parent)
        self.serial = serial
        self._is_connected = False
        self._monitoring_thread = None
        self._stop_event = threading.Event()
        self._fallback_timer = None

        # 비동기 실행을 위한 ThreadPoolExecutor
        self._executor = ThreadPoolExecutor(
            max_workers=1
        )  # 단일 스레드로 순차 실행 보장
        self._lock = threading.Lock()

        # 오프라인 상태 전용 보조 폴링 타이머 (pyudev가 있어도 동작)
        self._offline_timer = None

        # Connect internal invoke signal to handler (ensures execution on this object's Qt thread)
        self._invokeOnThisThread.connect(self._invoke_handler)

        # Initialize udev context and monitor for this specific device
        self._setup_device_monitoring()

        # Check initial connection status
        self._is_connected = self._is_device_connected_by_adb()

    def __del__(self):
        """Destructor for cleanup."""
        try:
            self.stop_monitoring()
        except Exception:
            pass  # Ignore exceptions during cleanup

    @property
    def is_connected(self) -> bool:
        """Check if the device is currently connected."""
        return self._is_connected

    # Ensure functions that touch Qt objects/timers run on THIS QObject's Qt thread
    def _run_on_qt_thread(self, func):
        try:
            # If we are already on the same Qt thread as this object, run directly
            if QThread.currentThread() == self.thread():
                func()
            else:
                # Queue to this object's thread to preserve parent-child affinity
                self._invokeOnThisThread.emit(func)
        except Exception as e:
            LOGD(f"ADBDevice: Failed to schedule function on Qt thread: {e}")

    def _invoke_handler(self, func):
        """Executes the given callable on this object's Qt thread."""
        try:
            func()
        except Exception as e:
            LOGD(f"ADBDevice: Exception in invoked handler: {e}")

    def _setup_device_monitoring(self):
        """Setup device monitoring using pyudev with fallback to polling."""
        try:
            self._context = pyudev.Context()
            self._monitor = pyudev.Monitor.from_netlink(self._context)
            self._monitor.filter_by(subsystem="usb")

            # Start monitoring device connections via pyudev
            self._start_pyudev_monitoring()
        except Exception as e:
            LOGD(
                f"ADBDevice: pyudev setup failed for {self.serial}, falling back to polling: {e}"
            )
            self._start_fallback_polling()

    def _start_pyudev_monitoring(self):
        """Start monitoring USB device connections via pyudev in a separate thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._pyudev_monitor_loop, daemon=True
        )
        self._monitoring_thread.start()

    def _pyudev_monitor_loop(self):
        """Main loop for monitoring pyudev events in a separate thread."""
        try:
            while not self._stop_event.is_set():
                device = self._monitor.poll(timeout=1)
                if device is None:
                    continue  # Timeout, check if we should stop

                # Check if this is an Android device event for our specific device
                if self._is_android_device_event_pyudev(device):
                    # Add a small delay to ensure ADB has processed the device change
                    time.sleep(0.5)

                    # Check the actual ADB device list
                    self._check_device_changes()

                    # 이벤트 이후 짧은 백오프 재시도로 ADB 준비 지연 흡수
                    for delay in (1.0, 2.5):
                        if self._stop_event.is_set():
                            break
                        time.sleep(delay)
                        self._check_device_changes()

        except Exception as e:
            LOGD(f"ADBDevice: pyudev monitoring failed for {self.serial}: {e}")
            self._start_fallback_polling()

    def _is_android_device_event_pyudev(self, device):
        """Check if the pyudev device object indicates an Android device event."""
        try:
            # Check if this is a USB device
            if device.subsystem != "usb":
                return False

            # For USB device events, check if it's an add/remove action
            if device.action == "add":
                vendor_id = device.get("ID_VENDOR_ID", "")
                if ADBUtils.is_android_device_vendor(vendor_id):
                    return True

                # Check for ADB interface
                if "adb" in device.get("ID_MODEL", "").lower():
                    return True

                # Check for debug appliance flag
                if device.get("ID_DEBUG_APPLIANCE") == "android":
                    return True

                # Check for ADB interface class/protocol
                if device.get("ID_USB_INTERFACES", "") and "ff4201" in device.get(
                    "ID_USB_INTERFACES", ""
                ):
                    return True
            elif device.action == "remove":
                # For remove events, assume it might be our device and check device list
                return True

            return False

        except Exception as e:
            LOGD(f"ADBDevice: Error checking Android device event: {e}")
            return False

    def _check_device_changes(self):
        """Check for device changes and emit appropriate signals."""
        current_connected = self._is_device_connected_by_adb()

        if current_connected and not self._is_connected:
            # Device connected
            self._is_connected = True
            LOGD(f"ADBDevice: Device {self.serial} connected")
            self.deviceConnected.emit()
        elif not current_connected and self._is_connected:
            # Device disconnected
            self._is_connected = False
            LOGD(f"ADBDevice: Device {self.serial} disconnected")
            self.deviceDisconnected.emit()

        # 오프라인/미연결 상태면 보조 폴링 가동, 연결되면 중지
        if current_connected:
            self._stop_offline_polling()
        else:
            self._ensure_offline_polling()

    def _start_fallback_polling(self):
        """Start fallback polling if pyudev is not available."""

        def _start():
            if self._fallback_timer:
                return
            LOGD(f"ADBDevice: Starting fallback polling for {self.serial}")
            self._fallback_timer = QTimer(self)
            self._fallback_timer.timeout.connect(self._check_device_changes)
            self._fallback_timer.start(2000)  # Check every 2 seconds

        self._run_on_qt_thread(_start)

    def _is_device_connected_by_adb(self) -> bool:
        """Check if this specific device is connected using ADB."""
        return ADBUtils.is_device_connected(self.serial)

    # 오프라인 상태 전용 보조 폴링 관리
    def _ensure_offline_polling(self):
        def _start():
            if self._offline_timer:
                return
            LOGD(f"ADBDevice: Starting offline polling for {self.serial}")
            self._offline_timer = QTimer(self)
            self._offline_timer.timeout.connect(self._check_device_changes)
            self._offline_timer.start(5000)  # 5 seconds

        self._run_on_qt_thread(_start)

    def _stop_offline_polling(self):
        def _stop():
            if self._offline_timer:
                LOGD(f"ADBDevice: Stopping offline polling for {self.serial}")
                self._offline_timer.stop()
                self._offline_timer = None

        self._run_on_qt_thread(_stop)

    def execute_command(self, command: BaseCommand) -> Optional[Any]:
        """
        Execute a command on this device.

        Args:
            command: Command instance to execute

        Returns:
            Command execution result or None if failed
        """
        if not self._is_connected:
            LOGD(
                f"ADBDevice: Cannot execute command, device {self.serial} not connected"
            )
            return None

        try:
            # Use the command's built-in execute method
            result = command.execute()

            # Emit signal with command result
            self.commandExecuted.emit(command.__class__.__name__, result)

            return result

        except Exception as e:
            LOGD(f"ADBDevice: Command execution failed for {self.serial}: {e}")
            self.commandExecuted.emit(command.__class__.__name__, None)
            return None

    def execute_adb_shell(self, shell_command: str) -> Optional[str]:
        """
        Execute a raw ADB shell command on this device.

        Args:
            shell_command: Shell command to execute

        Returns:
            Command output or None if failed
        """
        if not self._is_connected:
            LOGD(
                f"ADBDevice: Cannot execute shell command, device {self.serial} not connected"
            )
            return None

        LOGD(f"ADBDevice: Executing shell command on {self.serial}: {shell_command}")
        output = ADBUtils.execute_shell_command(self.serial, shell_command)

        if output is not None:
            LOGD(f"ADBDevice: Command output: {repr(output)}")
        else:
            LOGD(f"ADBDevice: Command failed for {self.serial}")

        return output

    def execute_adb_shell_async(
        self, shell_command: str, callback: Callable[[Optional[str]], None]
    ):
        """
        Execute ADB shell command asynchronously.

        Args:
            shell_command: Shell command to execute
            callback: Result callback function
        """
        if not self._is_connected:
            LOGD(
                f"ADBDevice: Cannot execute async shell command, device {self.serial} not connected"
            )
            # Ensure callback is invoked on this QObject's Qt thread
            try:
                self._run_on_qt_thread(lambda: callback(None))
            except Exception:
                try:
                    callback(None)
                except Exception:
                    pass
            return

        def run_command():
            try:
                LOGD(
                    f"ADBDevice: Async executing shell command on {self.serial}: {shell_command}"
                )
                result = subprocess.run(
                    ["adb", "-s", self.serial, "shell", shell_command],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                LOGD(f"ADBDevice: Async command return code: {result.returncode}")
                LOGD(f"ADBDevice: Async command stdout: {repr(result.stdout)}")
                LOGD(f"ADBDevice: Async command stderr: {repr(result.stderr)}")

                if result.returncode == 0:
                    output = result.stdout.strip()
                    LOGD(f"ADBDevice: Async final output: {repr(output)}")
                    try:
                        self._run_on_qt_thread(lambda out=output: callback(out))
                    except Exception:
                        try:
                            callback(output)
                        except Exception:
                            pass
                else:
                    LOGD(
                        f"ADBDevice: Async command failed with return code {result.returncode}"
                    )
                    try:
                        self._run_on_qt_thread(lambda: callback(None))
                    except Exception:
                        try:
                            callback(None)
                        except Exception:
                            pass

            except subprocess.TimeoutExpired as e:
                LOGD(f"ADBDevice: Async command timeout for {self.serial}: {e}")
                try:
                    self._run_on_qt_thread(lambda: callback(None))
                except Exception:
                    try:
                        callback(None)
                    except Exception:
                        pass
            except Exception as e:
                LOGD(f"ADBDevice: Async command exception for {self.serial}: {e}")
                try:
                    self._run_on_qt_thread(lambda: callback(None))
                except Exception:
                    try:
                        callback(None)
                    except Exception:
                        pass

        # Use ThreadPoolExecutor for async execution
        self._executor.submit(run_command)

    def stop_monitoring(self):
        """Stop monitoring the device."""
        LOGD(f"ADBDevice: Stopping monitoring for {self.serial}")

        # Stop pyudev monitoring thread
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._stop_event.set()
            self._monitoring_thread.join(timeout=2)

        # Stop timers on the Qt thread to avoid cross-thread issues
        def _stop_timers():
            if self._fallback_timer:
                self._fallback_timer.stop()
                self._fallback_timer = None
            if self._offline_timer:
                self._offline_timer.stop()
                self._offline_timer = None

        self._run_on_qt_thread(_stop_timers)

        # Shutdown ThreadPoolExecutor
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)

    def read_sw_version_file(self) -> Optional[str]:
        """
        Read the /sw_version.txt file from the device.

        Returns:
            File content as string or None if failed
        """
        if not self._is_connected:
            LOGD(
                f"ADBDevice: Cannot read sw_version.txt, device {self.serial} not connected"
            )
            return None

        LOGD(f"ADBDevice: Reading /sw_version.txt from {self.serial}")
        output = ADBUtils.execute_shell_command(self.serial, "cat /sw_version.txt")

        if output is not None:
            LOGD(f"ADBDevice: Successfully read /sw_version.txt from {self.serial}")
        else:
            LOGD(f"ADBDevice: Failed to read /sw_version.txt from {self.serial}")

        return output

    def cleanup_resources(self):
        """Clean up all resources associated with this device."""
        LOGD(f"ADBDevice: Cleaning up resources for {self.serial}")

        # Stop monitoring first
        self.stop_monitoring()

        # 여기에 추가적인 리소스 정리 로직을 구현할 수 있습니다.
