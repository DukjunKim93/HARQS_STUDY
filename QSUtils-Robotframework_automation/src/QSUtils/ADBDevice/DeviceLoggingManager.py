#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manages logging functionality for a specific Android device within the DeviceWidget.
"""

import os
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from QSUtils.Utils.DateTimeUtils import TimestampGenerator
from QSUtils.Utils.FileUtils import open_file_browser
from QSUtils.Utils.Logger import LOGD, LOGE
from QSUtils.command.cmd_logging import LoggingCommand


class DeviceLoggingManager(QObject):
    """
    Handles all logging-related operations for a device, including starting/stopping logs,
    managing log files, and handling logging states.
    """

    # Signals to communicate with the DeviceWidget (UI)
    logging_started_signal = Signal(str)  # Emits the log file name when logging starts
    logging_stopped_signal = Signal()  # Emits when logging stops
    logging_error_signal = Signal(str)  # Emits an error message string
    log_file_display_updated_signal = Signal(
        str
    )  # Emits the log file name for UI display
    new_log_line_signal = Signal(str)  # Emits new log line for real-time display

    def __init__(self, adb_device, parent=None):
        """
        Initialize the DeviceLoggingManager.

        Args:
            adb_device: ADBDevice instance for the target device.
            parent: Parent QObject, typically the DeviceWidget.
        """
        super().__init__(parent)
        self.adb_device = adb_device

        # Logging related attributes
        self.log_directory = None
        self.logging_command = None
        self.is_logging_enabled = False
        self.current_log_file_path = None
        self.is_manual_start = False
        self.last_log_file_path = None  # Stores the last used log file path
        self.was_logging_before_disconnect = (
            False  # Flag to preserve state across disconnects
        )
        self._intentional_stop = (
            False  # Internal flag to differentiate user stop vs disconnect/crash
        )

        # === 로그 파일 관리 속성 (BaseDeviceWidget에서 이전) ===
        self.current_log_filename = None  # 현재 로그 파일 이름
        self.log_file_persistent = False  # 로그 파일 지속성 플래그
        self.log_file_defined_on_disconnect = False  # 연결 해제 전 로그 파일 정의 여부
        self.pending_log_filename = None  # 다음 세션을 위해 미리 생성된 로그 파일 이름

        # ADBDevice 시그널 직접 연결
        self._setup_device_signals()

    def get_log_directory(self) -> str:
        """현재 설정된 로그 디렉토리 반환"""
        return self.log_directory

    def set_log_directory(self, directory):
        """Sets the log saving directory and updates the display."""
        self.log_directory = directory
        self._update_log_file_display()
        LOGD(f"DeviceLoggingManager: Log directory set to {directory}")

    def start_logging(self, manual_start: bool = False):
        """
        Starts the logging process using DeviceLoggingManager's own log file management policy.

        Args:
            manual_start (bool): True if triggered by user action; False for automatic (e.g., reconnect).
        """
        if not self.log_directory or not self.adb_device.is_connected:
            LOGD(
                f"DeviceLoggingManager: Cannot start logging - no directory or device not connected"
            )
            return

        self.is_manual_start = manual_start

        # Centralize manual-start policy: if user explicitly started, ensure fresh file
        if manual_start:
            if not self.pending_log_filename:
                self.reset_log_file_state()
                self.prepare_new_log_filename_for_session()

        # Use DeviceLoggingManager's own log file management policy
        append_mode = self.should_use_append_mode()

        if append_mode:
            # Use existing log file (append mode)
            log_filename = self.get_current_log_filename()
            if log_filename:
                log_file_path = str(Path(self.log_directory) / log_filename)
                LOGD(
                    f"DeviceLoggingManager: Using existing log file (append mode): {log_file_path}"
                )
            else:
                # Fallback: create new log file
                self.define_log_file_for_session()
                log_filename = self.get_current_log_filename()
                log_file_path = str(Path(self.log_directory) / log_filename)
                append_mode = False
                LOGD(f"DeviceLoggingManager: Fallback to new log file: {log_file_path}")
        else:
            # Create new log file
            self.define_log_file_for_session()
            log_filename = self.get_current_log_filename()
            log_file_path = str(Path(self.log_directory) / log_filename)
            LOGD(f"DeviceLoggingManager: Created new log file: {log_file_path}")

        self.current_log_file_path = log_file_path
        self.last_log_file_path = log_file_path
        LOGD(
            f"DeviceLoggingManager: start_logging path={log_file_path}, append={append_mode}"
        )

        # Update UI display immediately
        self._update_log_file_display()

        self.logging_command = LoggingCommand(self.adb_device, log_file_path)

        # Connect signals from LoggingCommand to internal handlers
        self.logging_command.logging_started.connect(self._on_internal_logging_started)
        self.logging_command.logging_stopped.connect(self._on_internal_logging_stopped)
        self.logging_command.logging_error.connect(self._on_internal_logging_error)
        self.logging_command.log_line_data.connect(self._on_log_line_received)

        if self.logging_command.execute(append_mode=append_mode):
            self.is_logging_enabled = True
            self.was_logging_before_disconnect = False  # Reset after successful start
            LOGD(
                f"DeviceLoggingManager: Logging started for device {self.adb_device.serial}"
            )
        else:
            self.is_logging_enabled = False
            LOGD(
                f"DeviceLoggingManager: Failed to start logging for device {self.adb_device.serial}"
            )
            # Emit error signal if execute fails immediately
            self.logging_error_signal.emit("Failed to initialize logging command.")

    def stop_logging(self):
        """Stops the logging process."""
        if self.logging_command and self.is_logging_enabled:
            # Mark as intentional stop so we don't set reconnect flags
            self._intentional_stop = True
            self.logging_command.stop()
            # is_logging_enabled will be set to False in _on_internal_logging_stopped
            LOGD(
                f"DeviceLoggingManager: Logging stop requested for device {self.adb_device.serial}"
            )
        else:
            LOGD(
                f"DeviceLoggingManager: Logging not active or command not initialized for device {self.adb_device.serial}"
            )

    def force_stop_logging(self):
        """Force stops the logging process (for emergency situations)."""
        if self.logging_command:
            # Mark as intentional stop so we don't set reconnect flags
            self._intentional_stop = True
            self.logging_command.force_stop()
            self.is_logging_enabled = False
            LOGD(
                f"DeviceLoggingManager: Logging force stop requested for device {self.adb_device.serial}"
            )
        else:
            LOGD(
                f"DeviceLoggingManager: Logging not active or command not initialized for device {self.adb_device.serial}"
            )

    def open_log_directory(self):
        """Opens the log directory in the file browser."""
        if self.log_directory:
            open_file_browser(self.log_directory)
            LOGD(f"DeviceLoggingManager: Opened log directory {self.log_directory}")

    def get_current_log_file_name(self) -> str:
        """Return the current log file name for UI display.
        Before Start, do not suggest a concrete file name to avoid confusion.
        Only show a name if a specific file has been selected/created previously.
        """
        from pathlib import Path

        # If we already chose a specific path for this session, prefer it
        if self.current_log_file_path:
            return Path(self.current_log_file_path).name
        # Otherwise, if there's a known last file, show it
        if self.last_log_file_path:
            return Path(self.last_log_file_path).name
        # Otherwise, no file name should be shown before logging starts
        return ""

    def _update_log_file_display(self):
        """Emits a signal to update the log file name display in the UI.
        Avoid emitting an empty string that would clear the placeholder text in the UI.
        """
        file_name = self.get_current_log_file_name()
        # Always emit something: if empty, emit a friendly hint to keep UI informative
        if not file_name:
            file_name = "(select Start to create log file)"
        self.log_file_display_updated_signal.emit(file_name)
        LOGD(f"DeviceLoggingManager: Log file display updated to: {file_name}")

    def _on_internal_logging_started(self):
        """Internal handler for LoggingCommand.logging_started signal."""
        self._update_log_file_display()
        self.logging_started_signal.emit(self.get_current_log_file_name())
        LOGD(f"DeviceLoggingManager: Internal logging started signal received")

    def _on_internal_logging_stopped(self):
        """Internal handler for LoggingCommand.logging_stopped signal."""
        self.is_logging_enabled = False
        # If stop was not intentional, remember to append on next reconnect
        if not self._intentional_stop:
            self.was_logging_before_disconnect = True
        # Reset the flag after handling
        self._intentional_stop = False
        self.logging_stopped_signal.emit()
        LOGD(f"DeviceLoggingManager: Internal logging stopped signal received")
        # Removed auto-restart logic to prevent infinite loops on process crash.
        # User must manually restart.

    def _on_internal_logging_error(self, error_msg: str):
        """Internal handler for LoggingCommand.logging_error signal."""
        LOGD(f"DeviceLoggingManager: Internal logging error: {error_msg}")
        self.is_logging_enabled = False
        # Treat unexpected errors like unintentional stops to allow append on reconnect
        if not self._intentional_stop:
            self.was_logging_before_disconnect = True
        # Reset the intentional flag after handling
        self._intentional_stop = False
        self.logging_error_signal.emit(error_msg)

    def set_was_logging_before_disconnect(self, state: bool):
        """Sets the flag indicating if logging was active before a disconnect."""
        self.was_logging_before_disconnect = state
        LOGD(f"DeviceLoggingManager: was_logging_before_disconnect set to {state}")

    def _on_log_line_received(self, log_line: str):
        """Internal handler for new log line data from LoggingCommand."""
        # Check if log_line contains null characters and handle them
        if "\x00" in log_line:
            # If null characters are present, we need to handle them carefully
            # We'll try to clean the string by encoding/decoding
            try:
                # Attempt to encode to bytes and decode back, ignoring errors
                cleaned_log_line = log_line.encode("utf-8", errors="ignore").decode(
                    "utf-8"
                )
            except Exception:
                # If encoding/decoding fails, we'll use a simple replacement
                cleaned_log_line = log_line.replace("\x00", "?")
        else:
            cleaned_log_line = log_line

        # Debug log to check if log lines are being received (commented out to prevent console output)
        # LOGD(f"DeviceLoggingManager: Received log line: {cleaned_log_line[:100]}...")  # Show first 100 chars

        # 공백 라인 또는 내용이 없는 라인 필터링
        # 타임스탬프와 프로세스 정보만 있고 실제 내용이 없는 라인 제거
        if not log_line or not log_line.strip():
            return

        # 로그 라인에서 실제 메시지 부분 추출 (타임스탬프 이후 부분)
        import re

        # 패턴: [타임스탬프] 날짜 프로세스[PID]: 메시지
        pattern = r"\[\d{6}-\d{2}:\d{2}:\d{2}\.\d{3}\]\s+\w+\s+\d+\s+\S+.*?:\s*(.*)"
        match = re.search(pattern, log_line)

        if match:
            actual_message = match.group(1).strip()
            if not actual_message:
                return  # 실제 메시지 내용이 없으면 표시하지 않음

        # Emit the log line to UI for real-time display
        self.new_log_line_signal.emit(log_line)

    def is_currently_logging(self) -> bool:
        """Checks if logging is currently enabled or was active moments ago.
        Uses a tolerant OR check to avoid race conditions during disconnect."""
        if self.logging_command:
            try:
                return (
                    self.is_logging_enabled or self.logging_command.is_process_running()
                )
            except Exception:
                return self.is_logging_enabled
        return self.is_logging_enabled

    # -----------------------------
    # 로그 파일 관리 메서드 (BaseDeviceWidget에서 이전)
    # -----------------------------
    def generate_new_log_filename(self) -> str:
        """
        새로운 로그 파일 이름 생성 (모든 앱 공통)
        하위 클래스에서 override하지 않음

        Returns:
            str: 생성된 로그 파일 이름 (예: "log_123456789_250925-175312.log")
        """
        timestamp = TimestampGenerator.get_log_timestamp()
        return f"log_{self.adb_device.serial}_{timestamp}.log"

    def prepare_new_log_filename_for_session(self) -> str:
        """
        다음 로깅 세션을 위해 새로운 로그 파일 이름을 미리 생성합니다.
        - 실제 파일은 아직 생성하지 않음
        - append 모드를 강제하지 않기 위해 persistence는 설정하지 않음
        - start_logging()에서 define_log_file_for_session()을 호출할 때
          이 사전 생성된 파일명을 우선 사용합니다.
        Returns:
            str: 생성된 로그 파일 이름
        """
        new_filename = self.generate_new_log_filename()
        # pending 이름을 저장하여 다음 define_log_file_for_session에서 사용
        self.pending_log_filename = new_filename
        LOGD(
            f"DeviceLoggingManager: Prepared new log file for session (pending): {new_filename}"
        )
        return new_filename

    def define_log_file_for_session(self) -> bool:
        """
        세션용 로그 파일 정의 (재부팅 간 지속성 보장)
        현재 로그 파일이 정의되어 있지 않은 경우에만 새로 생성
        또한, prepare_new_log_filename_for_session()으로 미리 준비된 파일명이 있으면 이를 우선 사용

        Returns:
            bool: 새로운 로그 파일을 생성했으면 True, 기존 파일이 있으면 False
        """
        if not self.current_log_filename:
            # pending 파일명이 있으면 그것을 사용
            if self.pending_log_filename:
                new_filename = self.pending_log_filename
                # 사용했으니 pending 초기화
                self.pending_log_filename = None
            else:
                new_filename = self.generate_new_log_filename()
            self.set_current_log_filename(new_filename)
            LOGD(
                f"DeviceLoggingManager: Defined new log file for session: {new_filename}"
            )
            return True
        return False

    def set_current_log_filename(self, filename: str):
        """
        현재 로그 파일 이름 설정 및 UI 업데이트
        연결 상태와 무관하게 로그 파일 이름을 지속적으로 표시

        Args:
            filename (str): 설정할 로그 파일 이름
        """
        self.current_log_filename = filename
        self.log_file_persistent = True
        self.log_file_defined_on_disconnect = True
        LOGD(f"DeviceLoggingManager: Set current log filename: {filename}")
        self._update_log_file_display()

    def get_current_log_filename(self) -> str:
        """
        현재 로그 파일 이름 반환 (연결 상태 무관)

        Returns:
            str: 현재 로그 파일 이름, 없으면 None
        """
        return self.current_log_filename

    def should_use_append_mode(self) -> bool:
        """
        append 모드 사용 여부 결정
        기존 로그 파일이 정의되어 있으면 append 모드 사용

        Returns:
            bool: append 모드를 사용해야 하면 True, 새 파일 생성이면 False
        """
        return self.log_file_persistent and self.current_log_filename is not None

    def reset_log_file_state(self):
        """
        로그 파일 상태 초기화 (완전히 새로운 세션 시작 시)
        모든 로그 파일 관련 상태를 초기화하고 UI 업데이트
        """
        self.current_log_filename = None
        self.log_file_persistent = False
        self.log_file_defined_on_disconnect = False
        self.pending_log_filename = None
        LOGD("DeviceLoggingManager: Reset log file state")
        self._update_log_file_display()

    def get_log_file_display_name(self) -> str:
        """
        UI에 표시할 로그 파일 이름 반환
        current_log_filename을 기반으로 파일명만 반환

        Returns:
            str: 표시할 로그 파일 이름
        """
        if self.current_log_filename:
            return os.path.basename(self.current_log_filename)
        return ""

    # -----------------------------
    # ADBDevice 시그널 직접 연결
    # -----------------------------
    def _setup_device_signals(self):
        """ADBDevice 시그널 직접 연결 설정"""
        if self.adb_device:
            # 디바이스 연결/해제 시그널 직접 연결
            self.adb_device.deviceConnected.connect(self._on_device_connected)
            self.adb_device.deviceDisconnected.connect(self._on_device_disconnected)
            LOGD(
                f"DeviceLoggingManager: Connected to ADBDevice signals for {self.adb_device.serial}"
            )

    def _on_device_connected(self):
        """ADBDevice deviceConnected 시그널 핸들러"""
        LOGD(f"DeviceLoggingManager: Device {self.adb_device.serial} connected")

        # 재연결 시에만 상태 복원 로직 실행
        if self.was_logging_before_disconnect or self.log_file_defined_on_disconnect:
            LOGD(
                f"DeviceLoggingManager: was_logging={self.was_logging_before_disconnect}, "
                f"log_file_defined={self.log_file_defined_on_disconnect}"
            )
            LOGD("DeviceLoggingManager: Auto-resuming logging after reconnect")
            self._restore_logging_state()

    def _on_device_disconnected(self):
        """ADBDevice deviceDisconnected 시그널 핸들러"""
        LOGD(f"DeviceLoggingManager: Device {self.adb_device.serial} disconnected")

        # 로깅 상태 저장
        if self.is_currently_logging():
            self.set_was_logging_before_disconnect(True)
            LOGD(
                "DeviceLoggingManager: Logging state saved as active before disconnect"
            )

            # 디바이스가 연결 해제되면 로깅 프로세스 강제 종료
            try:
                self.force_stop_logging()
                LOGD(
                    f"DeviceLoggingManager: Force stopped logging for device {self.adb_device.serial}"
                )
            except Exception as e:
                LOGE(f"DeviceLoggingManager: Error force stopping logging: {str(e)}")

        # 로그 파일이 정의되어 있으면 연결 해제 전 상태로 표시 유지
        if self.current_log_filename:
            self.log_file_defined_on_disconnect = True
            LOGD(
                f"DeviceLoggingManager: Log file defined before disconnect: {self.current_log_filename}"
            )

    def _restore_logging_state(self):
        """로깅 상태 자동 복원"""
        if self.was_logging_before_disconnect and not self.is_currently_logging():
            LOGD("DeviceLoggingManager: Auto-restarting logging only after reconnect")

            # 로그 파일 상태 확인 및 처리
            if (
                not self.current_log_filename
                and not self.log_file_defined_on_disconnect
            ):
                # 로그 파일이 정의되어 있지 않으면 새로 생성
                self.define_log_file_for_session()
            elif self.log_file_defined_on_disconnect:
                # 연결 해제 전에 로그 파일이 정의되어 있었으면 지속성 유지
                self.log_file_persistent = True
                LOGD(
                    f"DeviceLoggingManager: Restoring log file persistence: {self.current_log_filename}"
                )

            # 로깅 시작 (자동 복원이므로 manual_start=False)
            self.start_logging(manual_start=False)
