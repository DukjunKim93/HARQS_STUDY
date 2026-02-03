#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrog Upload Progress Dialog

Dialog for displaying upload progress status.
"""

import time
from typing import Dict, Any, Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QGroupBox,
)

# Conditional BaseDialog import for testing
try:
    from QSUtils.UIFramework.base.BaseDialog import BaseDialog
except ImportError:
    # Use QDialog directly if UIFramework is not available
    from PySide6.QtWidgets import QDialog as BaseDialog
from QSUtils.JFrogUtils.JFrogUploadWorker import (
    JFrogUploadWorker,
    JFrogChunkedUploadWorker,
)
from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.Utils.Logger import get_logger


class JFrogUploadDialog(BaseDialog):
    """JFrog Upload Progress Dialog"""

    def __init__(self, config: JFrogConfig, parent=None):
        """
        Initialize JFrogUploadDialog

        Args:
            config: JFrog configuration object
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self.logger = get_logger()

        # Worker management
        self.worker: Optional[JFrogUploadWorker] = None
        self.upload_result: Optional[Dict[str, Any]] = None

        # UI state
        self.is_uploading = False
        self.upload_completed = False

        # UI initialization
        self.setup_ui()
        self.setup_connections()

        self.logger.info("JFrogUploadDialog initialization completed")

    def setup_ui(self):
        """UI setup"""
        self.setWindowTitle("JFrog File Upload")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Overall progress group
        overall_group = QGroupBox("Overall Progress")
        overall_layout = QVBoxLayout()

        # Overall progress label
        self.overall_label = QLabel("Overall Progress: 0/0 files (0 MB/0 MB)")
        self.overall_label.setFont(QFont("", 10, QFont.Bold))
        overall_layout.addWidget(self.overall_label)

        # Overall progress Progress Bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setValue(0)
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setFormat("%v% (%p%)")
        overall_layout.addWidget(self.overall_progress)

        overall_group.setLayout(overall_layout)
        main_layout.addWidget(overall_group)

        # Details information group
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout()

        # Information layout
        info_layout = QHBoxLayout()

        # Left information
        left_info = QVBoxLayout()

        self.speed_label = QLabel("Speed: 0 MB/s")
        self.speed_label.setFont(QFont("", 9))
        left_info.addWidget(self.speed_label)

        self.eta_label = QLabel("ETA: --")
        self.eta_label.setFont(QFont("", 9))
        left_info.addWidget(self.eta_label)

        self.elapsed_label = QLabel("Elapsed Time: 00:00:00")
        self.elapsed_label.setFont(QFont("", 9))
        left_info.addWidget(self.elapsed_label)

        # Right information
        right_info = QVBoxLayout()

        self.uploaded_count_label = QLabel("Uploaded: 0")
        self.uploaded_count_label.setFont(QFont("", 9))
        right_info.addWidget(self.uploaded_count_label)

        self.failed_count_label = QLabel("Failed: 0")
        self.failed_count_label.setFont(QFont("", 9))
        right_info.addWidget(self.failed_count_label)

        self.size_label = QLabel("Size: 0 MB / 0 MB")
        self.size_label.setFont(QFont("", 9))
        right_info.addWidget(self.size_label)

        info_layout.addLayout(left_info)
        info_layout.addLayout(right_info)
        details_layout.addLayout(info_layout)

        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)

        # Log area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 8))
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Button layout
        button_layout = QHBoxLayout()

        # Pause/Resume button
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)

        # Close button
        self.close_button = QPushButton("Close")
        button_layout.addWidget(self.close_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Initial state setup
        self._update_ui_state()

    def setup_connections(self):
        """Signal/slot connections"""
        # Button connections
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.close_button.clicked.connect(self._on_close_clicked)

        # Progress update timer
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress_display)
        self.progress_timer.setInterval(500)  # Update every 0.5 seconds

    def start_file_upload(
        self, local_path: str, target_path: str = None, repo: str = None
    ):
        """
        Start single file upload

        Args:
            local_path: Local file path to upload
            target_path: Target path
            repo: Repository
        """
        files = [(local_path, target_path or local_path.split("/")[-1])]
        self._start_upload(files, repo, False)

    def start_directory_upload(
        self, local_path: str, target_path: str = None, repo: str = None
    ):
        """
        Start directory upload

        Args:
            local_path: Local directory path to upload
            target_path: Target path
            repo: Repository
        """
        # Worker creation and setup
        self.worker = JFrogUploadWorker(self.config, self)
        self.worker.setup_directory_upload(local_path, target_path, repo)
        self._setup_worker_connections()

        # Start upload
        self._start_upload_process()

    def start_files_upload(
        self, files: list, repo: str = None, use_chunked: bool = False
    ):
        """
        Start multiple files upload

        Args:
            files: List of files to upload [(local_path, target_path), ...]
            repo: Repository
            use_chunked: Whether to use chunked upload
        """
        self._start_upload(files, repo, use_chunked)

    def _start_upload(self, files: list, repo: str = None, use_chunked: bool = False):
        """
        Start upload (internal method)

        Args:
            files: List of files to upload
            repo: Repository
            use_chunked: Whether to use chunked upload
        """
        # Worker creation
        if use_chunked:
            self.worker = JFrogChunkedUploadWorker(self.config, self)
        else:
            self.worker = JFrogUploadWorker(self.config, self)

        # Worker setup
        self.worker.setup_upload(files, repo)
        self._setup_worker_connections()

        # Start upload
        self._start_upload_process()

    def _setup_worker_connections(self):
        """Worker signal connections"""
        if not self.worker:
            return

        # Signal connections
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.file_completed.connect(self._on_file_completed)
        self.worker.upload_completed.connect(self._on_upload_completed)
        self.worker.error_occurred.connect(self._on_error_occurred)

    def _start_upload_process(self):
        """Start upload process"""
        if not self.worker:
            return

        # State initialization
        self.is_uploading = True
        self.upload_completed = False
        self.upload_result = None

        # UI state update
        self._update_ui_state()

        # Log initialization
        self.log_text.clear()
        self._add_log("Starting upload...")

        # Progress timer start
        self.progress_timer.start()

        # Worker start
        self.worker.start()

        # Dialog modal display
        self.setModal(True)
        self.show()

    def _on_progress_updated(self, progress_data: Dict[str, Any]):
        """Progress status update"""
        if not self.is_uploading:
            return

        # Progress data storage
        self.current_progress_data = progress_data

    def _on_file_completed(self, file_path: str, file_info: Dict[str, Any]):
        """File upload completed"""
        chunked_text = " (chunked)" if file_info.get("chunked", False) else ""
        self._add_log(f"Completed: {file_path}{chunked_text}")

    def _on_upload_completed(
        self, success: bool, message: str, result_data: Dict[str, Any]
    ):
        """Upload completed"""
        self.is_uploading = False
        self.upload_completed = True
        self.upload_result = result_data

        # Progress timer stop
        self.progress_timer.stop()

        # Log addition
        self._add_log(f"Upload completed: {message}")

        if result_data.get("failed_files"):
            self._add_log(f"Failed files: {len(result_data['failed_files'])}")
            for failed_file in result_data["failed_files"]:
                self._add_log(
                    f"  - {failed_file['local_path']}: {failed_file.get('error', 'Unknown error')}"
                )

        # UI state update
        self._update_ui_state()

        # Final progress display
        self._update_progress_display()

    def _on_error_occurred(self, error_message: str):
        """Error occurred"""
        self._add_log(f"Error: {error_message}")
        self.is_uploading = False
        self.upload_completed = True

        # Progress timer stop
        self.progress_timer.stop()

        # UI state update
        self._update_ui_state()

    def _update_progress_display(self):
        """Progress display update"""
        if not hasattr(self, "current_progress_data") or not self.current_progress_data:
            return

        data = self.current_progress_data

        # Overall progress status
        total_files = data.get("total_files", 0)
        completed_files = data.get("completed_files", 0)
        total_bytes = data.get("total_bytes", 0)
        uploaded_bytes = data.get("uploaded_bytes", 0)
        progress_percentage = data.get("progress_percentage", 0)

        self.overall_label.setText(
            f"Overall Progress: {completed_files}/{total_files} files "
            f"({self._format_bytes(uploaded_bytes)}/{self._format_bytes(total_bytes)})"
        )
        self.overall_progress.setValue(int(progress_percentage))

        # Details information
        speed_bps = data.get("speed_bps", 0)
        self.speed_label.setText(f"Speed: {self._format_speed(speed_bps)}")

        eta_seconds = data.get("eta_seconds", 0)
        if eta_seconds > 0:
            self.eta_label.setText(f"ETA: {self._format_time(eta_seconds)}")
        else:
            self.eta_label.setText("ETA: --")

        elapsed_time = data.get("elapsed_time", 0)
        self.elapsed_label.setText(f"Elapsed Time: {self._format_time(elapsed_time)}")

        # Display upload result information if available
        if self.upload_result:
            uploaded_count = self.upload_result.get("total_uploaded", 0)
            failed_count = self.upload_result.get("total_failed", 0)
            total_size = self.upload_result.get("total_size", 0)

            self.uploaded_count_label.setText(f"Uploaded: {uploaded_count}")
            self.failed_count_label.setText(f"Failed: {failed_count}")
            self.size_label.setText(f"Size: {self._format_bytes(total_size)}")
        else:
            self.uploaded_count_label.setText(f"Uploaded: {completed_files}")
            self.failed_count_label.setText("Failed: 0")
            self.size_label.setText(f"Size: {self._format_bytes(uploaded_bytes)}")

    def _on_pause_clicked(self):
        """Pause button clicked"""
        if not self.worker:
            return

        if self.worker.is_paused():
            self.worker.resume_upload()
            self.pause_button.setText("Pause")
            self._add_log("Resuming upload...")
        else:
            self.worker.pause_upload()
            self.pause_button.setText("Resume")
            self._add_log("Pausing upload...")

    def _on_cancel_clicked(self):
        """Cancel button clicked"""
        if not self.worker:
            return

        # Confirmation dialog
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Upload Cancel",
            "Are you sure you want to cancel the upload?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.worker.cancel_upload()
            self._add_log("Canceling upload...")

    def _on_close_clicked(self):
        """Close button clicked"""
        if self.is_uploading:
            # Cancel confirmation if uploading
            from PySide6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Upload Stop",
                "Upload is in progress. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes and self.worker:
                self.worker.cancel_upload()

        self.accept()

    def _update_ui_state(self):
        """UI state update"""
        if self.is_uploading:
            # Uploading
            self.pause_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.close_button.setEnabled(False)

            if self.worker and self.worker.is_paused():
                self.pause_button.setText("Resume")
            else:
                self.pause_button.setText("Pause")
        else:
            # Upload completed or stopped
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.close_button.setEnabled(True)

    def _add_log(self, message: str):
        """Add log message"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)

        # Auto scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _format_bytes(self, bytes_count: int) -> str:
        """Format byte size"""
        if bytes_count == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(bytes_count)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    def _format_speed(self, bps: float) -> str:
        """Format speed"""
        if bps == 0:
            return "0 B/s"

        return f"{self._format_bytes(int(bps))}/s"

    def _format_time(self, seconds: float) -> str:
        """Format time"""
        if seconds == 0:
            return "00:00:00"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get upload result"""
        return self.upload_result

    def closeEvent(self, event):
        """Dialog close event"""
        if self.is_uploading:
            event.ignore()
            self._on_close_clicked()
        else:
            if self.worker:
                self.worker.quit()
                self.worker.wait()
            super().closeEvent(event)
