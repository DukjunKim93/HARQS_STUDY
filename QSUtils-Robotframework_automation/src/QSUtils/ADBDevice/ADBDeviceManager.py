#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB Device Hub for centralized management of all ADB devices.
Provides unified device monitoring and list management functionality.
Replaces and enhances ADBDeviceManager and ADBDeviceMonitor.
"""

from typing import List, Dict, Optional

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


from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.ADBDevice.ADBUtils import ADBUtils
from QSUtils.Utils.Logger import LOGD


def _run_on_qt_thread_for(obj: QObject, func):
    """Run func on the thread that owns 'obj'. If already on that thread, run now; else, queue to obj's thread.
    This avoids cross-thread QObject child creation errors by ensuring execution on the correct affinity thread.
    """
    try:
        if QThread.currentThread() == obj.thread():
            func()
        else:
            # Use receiver overload to dispatch to obj's thread
            QTimer.singleShot(0, obj, func)
    except Exception as e:
        LOGD(
            f"ADBDeviceManager: Failed to schedule function on target object's thread: {e}"
        )


class ADBDeviceManager(QObject):
    """
    Centralized manager for managing all ADB devices.
    Provides device list management and individual device monitoring.
    """

    # Signals for device list changes
    deviceListUpdated = Signal(list)  # Emitted when the overall device list changes

    def __init__(self, parent=None):
        """
        Initialize the ADB device hub.

        Args:
            parent: Parent Qt object
        """
        super().__init__(parent)
        self._device_controllers: Dict[str, ADBDevice] = {}
        self._last_device_list: List[str] = []

        # Unified monitoring setup
        self._monitoring_thread = None
        self._stop_event = None
        self._fallback_timer = None

        # pyudev 동작 중 이벤트 누락 대비 세이프티 폴링 타이머
        self._safety_poll_timer = None

        # Initialize device monitoring
        self._setup_unified_monitoring()

        # Initial device list check
        self._check_and_update_device_list()

    def __del__(self):
        """Destructor for cleanup."""
        try:
            self.stop_monitoring()
        except Exception:
            pass  # Ignore exceptions during cleanup

    def _setup_unified_monitoring(self):
        """Setup unified device monitoring using pyudev with fallback to polling."""
        try:
            self._context = pyudev.Context()
            self._monitor = pyudev.Monitor.from_netlink(self._context)
            self._monitor.filter_by(subsystem="usb")

            # Start unified monitoring
            self._start_pyudev_monitoring()
            LOGD("ADBDeviceManager: Started pyudev-based monitoring")

            # 이벤트 누락 대비 저빈도 세이프티 폴링(10초) - ensure on Qt thread
            def _start_safety():
                if not self._safety_poll_timer:
                    self._safety_poll_timer = QTimer(self)
                    self._safety_poll_timer.timeout.connect(
                        self._check_and_update_device_list
                    )
                    self._safety_poll_timer.start(10000)

            _run_on_qt_thread_for(self, _start_safety)
        except Exception as e:
            LOGD(f"ADBDeviceManager: pyudev setup failed, falling back to polling: {e}")
            self._start_fallback_polling()

    def _start_pyudev_monitoring(self):
        """Start unified USB device monitoring via pyudev."""
        import threading

        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        self._stop_event = threading.Event()
        self._monitoring_thread = threading.Thread(
            target=self._unified_monitor_loop, daemon=True
        )
        self._monitoring_thread.start()

    def _unified_monitor_loop(self):
        """Main loop for unified device monitoring."""
        try:
            while not self._stop_event.is_set():
                device = self._monitor.poll(timeout=1)
                if device is None:
                    continue

                # Check if this is an Android device event
                if self._is_android_device_event_pyudev(device):
                    # Add delay to ensure ADB has processed the device change
                    import time

                    time.sleep(0.5)

                    # Check device list changes
                    self._check_and_update_device_list()

        except Exception as e:
            LOGD(f"ADBDeviceManager: pyudev monitoring failed: {e}")
            self._start_fallback_polling()

    def _is_android_device_event_pyudev(self, device):
        """Check if the pyudev device object indicates an Android device event."""
        try:
            if device.subsystem != "usb":
                return False

            if device.action == "add":
                vendor_id = device.get("ID_VENDOR_ID", "")
                if ADBUtils.is_android_device_vendor(vendor_id):
                    return True
                if "adb" in device.get("ID_MODEL", "").lower():
                    return True
                if device.get("ID_DEBUG_APPLIANCE") == "android":
                    return True
                if device.get("ID_USB_INTERFACES", "") and "ff4201" in device.get(
                    "ID_USB_INTERFACES", ""
                ):
                    return True
            elif device.action == "remove":
                return True

            return False
        except Exception:
            return False

    def _start_fallback_polling(self):
        """Start fallback polling if pyudev is not available."""

        def _start():
            if self._fallback_timer:
                return
            LOGD("ADBDeviceManager: Starting fallback polling")
            self._fallback_timer = QTimer(self)
            self._fallback_timer.timeout.connect(self._check_and_update_device_list)
            self._fallback_timer.start(2000)  # Check every 2 seconds

        _run_on_qt_thread_for(self, _start)

    def _check_and_update_device_list(self):
        """Check current device list and update controllers accordingly."""
        # Ensure this runs on the manager's own thread to avoid cross-thread QObject child creation
        try:
            if QThread.currentThread() != self.thread():
                QTimer.singleShot(0, self, self._check_and_update_device_list)
                return
        except Exception:
            pass

        current_devices = self._get_connected_devices()

        # Check if overall device list has changed
        if current_devices != self._last_device_list:
            self._last_device_list = current_devices.copy()
            LOGD(f"ADBDeviceManager: Device list updated: {current_devices}")
            self.deviceListUpdated.emit(current_devices)

        # Update individual device controllers
        self._update_device_controllers(current_devices)

    def _get_connected_devices(self) -> List[str]:
        """Get list of currently connected ADB devices."""
        return ADBUtils.list_connected_devices()

    def _update_device_controllers(self, current_devices: List[str]):
        """Update device controllers based on current device list."""
        # Create controllers for newly connected devices
        for serial in current_devices:
            if serial not in self._device_controllers:
                controller = ADBDevice(serial, self)
                self._device_controllers[serial] = controller

                LOGD(f"ADBDeviceManager: Created controller for device {serial}")

        # Note: We don't remove controllers for disconnected devices immediately
        # They might reconnect, and the controller will handle connection state internally

    def get_device_controller(self, serial: str) -> Optional[ADBDevice]:
        """
        Get the device controller for a specific serial.

        Args:
            serial: Device serial number

        Returns:
            ADBDevice instance or None if device not found
        """
        if serial not in self._device_controllers:
            # Create controller on demand if device exists
            current_devices = self._get_connected_devices()
            if serial in current_devices:
                self._update_device_controllers([serial])

        return self._device_controllers.get(serial)

    def list_devices(self) -> List[str]:
        """
        List all connected Android devices.

        Returns:
            List of device serial numbers
        """
        return self._last_device_list.copy()

    def is_device_connected(self, serial: str) -> bool:
        """
        Check if a specific device is connected.

        Args:
            serial: Device serial number to check

        Returns:
            True if device is connected, False otherwise
        """
        controller = self.get_device_controller(serial)
        return controller.is_connected if controller else False

    def get_all_controllers(self) -> Dict[str, ADBDevice]:
        """
        Get all device controllers.

        Returns:
            Dictionary mapping serial numbers to ADBDevice instances
        """
        return self._device_controllers.copy()

    def stop_monitoring(self):
        """Stop all monitoring activities."""
        LOGD("ADBDeviceManager: Stopping all monitoring")

        # Stop pyudev monitoring thread
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            if self._stop_event:
                self._stop_event.set()
            self._monitoring_thread.join(timeout=2)

        # Stop fallback and safety polling timers on Qt thread
        def _stop_timers():
            if self._fallback_timer:
                self._fallback_timer.stop()
                self._fallback_timer = None
            if self._safety_poll_timer:
                self._safety_poll_timer.stop()
                self._safety_poll_timer = None

        _run_on_qt_thread_for(self, _stop_timers)

        # Stop all device controllers and clean up resources
        for controller in self._device_controllers.values():
            controller.cleanup_resources()

        # Clear controllers
        self._device_controllers.clear()

    def cleanup_device_resources(self, serial: str):
        """Clean up resources for a specific device."""
        if serial in self._device_controllers:
            controller = self._device_controllers[serial]
            controller.cleanup_resources()
            del self._device_controllers[serial]
            LOGD(f"ADBDeviceManager: Cleaned up resources for device {serial}")
