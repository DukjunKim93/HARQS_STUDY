#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Command for QSMonitor application.
Handles device log collection using logcat command.
"""

from pathlib import Path

from QSUtils.Utils.DateTimeUtils import TimestampGenerator
from QSUtils.Utils.Logger import LOGI, LOGE, LOGD
from QSUtils.command.base_command import BaseCommand
from QSUtils.command.command_constants import SystemCommands
from QSUtils.command.log_file_manager import LogFileManager
from QSUtils.command.logging_signal_emitter import LoggingSignalEmitter
from QSUtils.command.process_manager import ProcessManager


class LoggingCommand(BaseCommand):
    """
    Command class for collecting device logs using logcat.
    Uses refactored components for better separation of concerns.
    """

    def __init__(self, device, log_file_path):
        """
        Initialize LoggingCommand.

        Args:
            device: ADBDevice instance
            log_file_path (str): Path to the log file
        """
        BaseCommand.__init__(self, device)
        self.log_file_path = Path(log_file_path)
        self.is_running = False

        # 리팩토링된 컴포넌트 초기화
        self.file_manager = LogFileManager(self.log_file_path)
        self.process_manager = ProcessManager()
        self.signal_emitter = LoggingSignalEmitter()

        # ProcessManager 시그널 연결 (ProcessManager 내부 연결은 제거)
        self.process_manager.process.started.connect(self._on_started)
        self.process_manager.process.finished.connect(self._on_finished)
        self.process_manager.process.errorOccurred.connect(self._on_error)
        self.process_manager.process.readyRead.connect(self._on_ready_read)

        LOGD(
            f"LoggingCommand initialized for device {device.serial}, log file: {log_file_path}"
        )

    def get_shell_command(self) -> str:
        """
        Return the shell command for logcat.

        Returns:
            str: Shell command string
        """
        return SystemCommands.LOGCAT

    def handle_response(self, response_lines):
        """
        Handle command response (not used for logging command).

        Args:
            response_lines: List of response lines

        Returns:
            None: Not used for logging
        """
        # This method is not used for logging command as output goes directly to file
        return None

    def execute(self, append_mode=False) -> bool:
        """
        Start the logging process.

        Args:
            append_mode (bool): Whether to append to existing log file

        Returns:
            bool: True if process started successfully, False otherwise
        """
        if self.is_running:
            LOGE(f"Logging already running for device {self.device.serial}")
            return False

        if not self.device or not self.device.is_connected:
            LOGE(
                f"Device not connected for logging: {self.device.serial if self.device else 'Unknown'}"
            )
            return False

        try:
            # 로그 파일 초기화
            if not self.file_manager.initialize_file(append_mode):
                return False

            # 프로세스 시작
            shell_command = self.get_shell_command()
            success = self.process_manager.start_process(
                self.device.serial, shell_command, shell_command.split()
            )

            if success:
                self.is_running = True
                LOGD(
                    f"Logging process started successfully for device {self.device.serial}"
                )
                return True
            else:
                self.file_manager.close_file()
                return False

        except Exception as e:
            LOGE(
                f"Exception starting logging for device {self.device.serial}: {str(e)}"
            )
            self.file_manager.close_file()
            return False

    def stop(self):
        """Stop the logging process."""
        if not self.process_manager or not self.is_running:
            return

        LOGI(f"Stopping logging process for device {self.device.serial}")

        try:
            # 의도적 종료 표시
            self.process_manager.set_intentionally_stopping(True)

            # 프로세스 정지
            self.process_manager.stop_process()
        except Exception as e:
            LOGE(
                f"Exception stopping logging for device {self.device.serial}: {str(e)}"
            )
        finally:
            # 로그 파일 닫기
            self.file_manager.close_file()
            # 추가 쓰기 방지
            self.is_running = False

    def force_stop(self):
        """Force stop the logging process (for emergency situations)."""
        if not self.process_manager:
            return

        LOGI(f"Force stopping logging process for device {self.device.serial}")

        try:
            # 의도적 종료 표시
            self.process_manager.set_intentionally_stopping(True)

            # 프로세스 강제 정지
            if self.process_manager.process:
                self.process_manager.process.terminate()
                if not self.process_manager.process.waitForFinished(1000):  # 1초 대기
                    self.process_manager.process.kill()
        except Exception as e:
            LOGE(
                f"Exception force stopping logging for device {self.device.serial}: {str(e)}"
            )
        finally:
            # 로그 파일 닫기
            self.file_manager.close_file()
            # 추가 쓰기 방지
            self.is_running = False

    def is_process_running(self):
        """
        Check if the logging process is currently running.

        Returns:
            bool: True if process is running, False otherwise
        """
        return self.is_running and self.process_manager.is_running()

    def get_log_file_path(self):
        """
        Get the path to the log file.

        Returns:
            str: Path to the log file
        """
        return self.file_manager.get_file_path()

    def _on_started(self):
        """Handle process started signal."""
        LOGD(f"Logging process started signal received for device {self.device.serial}")
        self.signal_emitter.emit_logging_started()

    def _on_finished(self, exit_code, exit_status):
        """
        Handle process finished signal.

        Args:
            exit_code (int): Process exit code
            exit_status (QProcess.ExitStatus): Process exit status
        """
        LOGD(
            f"Logging process finished for device {self.device.serial}, "
            f"exit code: {exit_code}, exit status: {exit_status}"
        )

        # ProcessManager에서 이미 비정상 종료 처리를 하므로 여기서는 시그널만 발산
        self.is_running = False
        self.signal_emitter.emit_logging_stopped()

    def _on_error(self, error):
        """
        Handle process error signal.

        Args:
            error (QProcess.ProcessError): Process error type
        """
        # 의도적 종료 중이면 무시
        if self.process_manager.is_intentionally_stopping():
            LOGD(
                f"Logging process error ignored due to intentional stop for device {self.device.serial}"
            )
            return

        error_msg = f"Logging process error for device {self.device.serial}: {self.process_manager.process.errorString()}"
        LOGE(error_msg)
        self.is_running = False
        self.signal_emitter.emit_logging_error(error_msg)

    def _on_ready_read(self):
        """Handle readyRead signal to read process output and write to file in real-time."""
        if not self.file_manager.is_file_open() or not self.is_running:
            return

        try:
            # Read all available data from the process
            data = self.process_manager.read_all_data()
            if data:
                # Convert bytes to string
                text = str(data, "utf-8", errors="replace")

                # 각 라인 앞에 타임스탬프 추가
                timestamp = f"[{TimestampGenerator.get_detailed_timestamp()}] "

                # 라인별로 처리하여 타임스탬프 추가
                lines = text.split("\n")
                timestamped_lines = []
                for line in lines:
                    if line.strip():  # 빈 라인이 아닌 경우에만 타임스탬프 추가
                        timestamped_lines.append(timestamp + line)
                    else:
                        timestamped_lines.append(line)  # 빈 라인은 그대로 유지

                timestamped_text = "\n".join(timestamped_lines)

                # 타임스탬프가 추가된 텍스트를 파일에 쓰기
                self.file_manager.write_line(timestamped_text)

                # Emit all log data for real-time processing
                self.signal_emitter.emit_log_line_data(timestamped_text)

                # Emit audio log data for real-time processing (for compatibility)
                # Check if the text contains ACM audio log patterns
                if "[^^^ACM]" in timestamped_text:
                    self.signal_emitter.emit_audio_log_data(timestamped_text)
        except Exception as e:
            error_msg = f"Error reading/writing log data for device {self.device.serial}: {str(e)}"
            LOGE(error_msg)
            self.signal_emitter.emit_logging_error(error_msg)

    # Property getters for signals to maintain compatibility with existing code
    @property
    def logging_started(self):
        """Get logging_started signal."""
        return self.signal_emitter.logging_started

    @property
    def logging_stopped(self):
        """Get logging_stopped signal."""
        return self.signal_emitter.logging_stopped

    @property
    def logging_error(self):
        """Get logging_error signal."""
        return self.signal_emitter.logging_error

    @property
    def log_line_data(self):
        """Get log_line_data signal."""
        return self.signal_emitter.log_line_data

    @property
    def audio_log_data(self):
        """Get audio_log_data signal."""
        return self.signal_emitter.audio_log_data
