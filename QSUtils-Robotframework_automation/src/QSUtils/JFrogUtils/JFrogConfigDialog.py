#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JFrog Configuration Dialog

JFrog 업로드 설정을 구성하는 다이얼로그입니다.
"""

from typing import Dict, Any

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFormLayout,
)

# Conditional BaseDialog import for testing
try:
    from QSUtils.UIFramework.base.BaseDialog import BaseDialog
except ImportError:
    # Use QDialog directly if UIFramework is not available
    from PySide6.QtWidgets import QDialog as BaseDialog

from QSUtils.Utils.Logger import get_logger

# 기본 설정 상수
DEFAULT_JFROG_CONFIG = {
    "auto_upload_enabled": True,
    "jfrog_server_url": "https://bart.sec.samsung.net/artifactory",
    "jfrog_default_repo": "oneos-qsymphony-issues-generic-local",
    "jfrog_server_name": "qsutils-server",
    "local_directory_prefix": "issues",
    "upload_directory_prefix": "issues",
}


class JFrogConfigDialog(BaseDialog):
    """JFrog 설정 다이얼로그"""

    def __init__(self, settings_manager, parent=None):
        """
        JFrogConfigDialog 초기화
        Args:
            settings_manager: 설정 관리자
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.logger = get_logger()

        # 현재 설정 저장
        self.current_config = self._load_current_config()

        # UI 초기화
        self.setup_ui()
        self.setup_connections()
        self._load_settings_to_ui()

        self.logger.info("JFrogConfigDialog initialization completed")

    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("Issue Upload Configuration")
        self.setMinimumSize(500, 400)
        self.resize(550, 450)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # JFrog 서버 설정 그룹
        server_group = QGroupBox("JFrog Server Settings")
        server_layout = QFormLayout()

        # Server URL
        self.server_url_edit = QLineEdit()
        server_layout.addRow("Server URL:", self.server_url_edit)

        # Repository
        self.repository_edit = QLineEdit()
        server_layout.addRow("Repository:", self.repository_edit)

        # Server Name
        self.server_name_edit = QLineEdit()
        server_layout.addRow("Server Name:", self.server_name_edit)

        server_group.setLayout(server_layout)
        main_layout.addWidget(server_group)

        # 디렉토리 설정 그룹
        directory_group = QGroupBox("Directory Settings")
        directory_layout = QFormLayout()

        # Local Directory Prefix
        self.local_dir_prefix_edit = QLineEdit()
        self.local_dir_prefix_edit.setPlaceholderText("Local storage directory prefix")
        directory_layout.addRow("Local Dir Prefix:", self.local_dir_prefix_edit)

        # Upload Directory Prefix
        self.upload_dir_prefix_edit = QLineEdit()
        self.upload_dir_prefix_edit.setPlaceholderText("JFrog upload directory prefix")
        directory_layout.addRow("Upload Dir Prefix:", self.upload_dir_prefix_edit)

        directory_group.setLayout(directory_layout)
        main_layout.addWidget(directory_group)

        # 설명 라벨
        info_label = QLabel(
            "Note: Local directory prefix affects local storage path (logs/{prefix}/{timestamp}/).\n"
            "Upload directory prefix affects JFrog upload path ({prefix}/{issue_id}/)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px;")
        main_layout.addWidget(info_label)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # Set to Default 버튼
        self.reset_button = QPushButton("Set to Default")
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        # OK 버튼
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)

        # Cancel 버튼
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def setup_connections(self):
        """시그널/슬롯 연결"""
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self._on_reset_to_default)

    def _load_current_config(self) -> Dict[str, Any]:
        """현재 설정 로드"""
        try:
            upload_settings = self.settings_manager.get("dump.upload_settings", {})
            # 기본값과 현재 설정 병합
            config = DEFAULT_JFROG_CONFIG.copy()
            config.update(upload_settings)
            return config
        except Exception as e:
            self.logger.error(f"Failed to load current config: {e}")
            return DEFAULT_JFROG_CONFIG.copy()

    def _load_settings_to_ui(self):
        """설정을 UI에 로드"""
        self.server_url_edit.setText(self.current_config.get("jfrog_server_url", ""))
        self.repository_edit.setText(self.current_config.get("jfrog_default_repo", ""))
        self.server_name_edit.setText(self.current_config.get("jfrog_server_name", ""))
        self.local_dir_prefix_edit.setText(
            self.current_config.get("local_directory_prefix", "")
        )
        self.upload_dir_prefix_edit.setText(
            self.current_config.get("upload_directory_prefix", "")
        )

    def _get_ui_settings(self) -> Dict[str, Any]:
        """UI에서 현재 설정 가져오기"""
        return {
            "jfrog_server_url": self.server_url_edit.text().strip(),
            "jfrog_default_repo": self.repository_edit.text().strip(),
            "jfrog_server_name": self.server_name_edit.text().strip(),
            "local_directory_prefix": self.local_dir_prefix_edit.text().strip(),
            "upload_directory_prefix": self.upload_dir_prefix_edit.text().strip(),
        }

    def _validate_settings(self, settings: Dict[str, Any]) -> bool:
        """설정 유효성 검증"""
        errors = []

        # Server URL 검증
        server_url = settings.get("jfrog_server_url", "")
        if not server_url:
            errors.append("Server URL is required.")
        elif not (
            server_url.startswith("http://") or server_url.startswith("https://")
        ):
            errors.append("Server URL must start with http:// or https://")

        # Repository 검증
        if not settings.get("jfrog_default_repo", ""):
            errors.append("Repository is required.")

        # Server Name 검증
        if not settings.get("jfrog_server_name", ""):
            errors.append("Server Name is required.")

        # Directory Prefix 검증
        local_prefix = settings.get("local_directory_prefix", "")
        if not local_prefix:
            errors.append("Local Directory Prefix is required.")

        upload_prefix = settings.get("upload_directory_prefix", "")
        if not upload_prefix:
            errors.append("Upload Directory Prefix is required.")

        if errors:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please fix the following errors:\n\n"
                + "\n".join(f"• {error}" for error in errors),
            )
            return False

        return True

    def _on_reset_to_default(self):
        """기본값으로 재설정"""
        reply = QMessageBox.question(
            self,
            "Reset to Default",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 기본값으로 UI 업데이트
            self.server_url_edit.setText(DEFAULT_JFROG_CONFIG["jfrog_server_url"])
            self.repository_edit.setText(DEFAULT_JFROG_CONFIG["jfrog_default_repo"])
            self.server_name_edit.setText(DEFAULT_JFROG_CONFIG["jfrog_server_name"])
            self.local_dir_prefix_edit.setText(
                DEFAULT_JFROG_CONFIG["local_directory_prefix"]
            )
            self.upload_dir_prefix_edit.setText(
                DEFAULT_JFROG_CONFIG["upload_directory_prefix"]
            )
            self.logger.info("Settings reset to default values")

    def accept(self):
        """OK 버튼 클릭 시 처리"""
        # 현재 UI 설정 가져오기
        settings = self._get_ui_settings()

        # 설정 유효성 검증
        if not self._validate_settings(settings):
            return  # 유효성 검증 실패 시 다이얼로그 닫지 않음

        # 설정 저장
        try:
            self.settings_manager.set("dump.upload_settings", settings)
            self.logger.info(f"JFrog settings saved: {settings}")
            super().accept()
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(
                self, "Save Error", f"Failed to save settings:\n{str(e)}"
            )

    def get_current_settings(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        return self.current_config.copy()
