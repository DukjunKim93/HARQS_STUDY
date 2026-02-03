#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MainController
비즈니스 로직(디바이스 관리, 설정 관리)을 UI로부터 분리하기 위한 간단한 컨트롤러.
QSMonitor, QSLogger, QSAutoReboot가 공통으로 사용하는 기능을 제공합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from QSUtils.ADBDevice.ADBDeviceManager import ADBDeviceManager
from QSUtils.UIFramework.config.SettingsManager import SettingsManager
from QSUtils.Utils.Logger import set_log_level
from QSUtils.Utils.logging_config import configure_logging, LoggingConfig


class MainController:
    """
    메인 윈도우에서 사용하는 공통 비즈니스 로직을 담당합니다.
    - 디바이스 나열/제어
    - 애플리케이션 설정(윈도우 지오메트리, 로그 경로/레벨)
    """

    def __init__(
        self, app_config, qt_parent=None, settings_manager: SettingsManager = None
    ) -> None:
        self.app_config = app_config

        # 외부에서 settings_manager가 전달되면 사용하고, 없으면 app_config에서 설정 가져오기
        if settings_manager is not None:
            self.settings_manager = settings_manager
        else:
            # app_config 객체에서 직접 설정 파일과 기본 설정 가져오기
            config_file = app_config.get_config_file()
            default_settings = app_config.get_default_settings()
            self.settings_manager = SettingsManager(config_file, default_settings)

        # Qt 시그널 연결을 위해 parent를 넘겨 기존 동작과 호환
        self.device_hub = ADBDeviceManager(qt_parent)

    # ---- Device related ----
    def list_devices(self) -> List[str]:
        return self.device_hub.list_devices()

    def get_device_controller(self, serial: str):
        return self.device_hub.get_device_controller(serial)

    # ---- Settings related ----
    def get_window_geometry(self) -> dict:
        # 모든 앱이 "window_geometry" 키를 사용하도록 통일
        return self.settings_manager.get_window_geometry("window_geometry")

    def get_log_level(self) -> str:
        return self.settings_manager.get_log_level()

    def set_log_level(self, level_text: str) -> None:
        # 기존 로거 설정 유지 (Logger.py 시스템)
        set_log_level(level_text)

        # 중앙 로깅 시스템도 업데이트 (logging_config.py 시스템)
        try:
            # 현재 설정을 가져와서 로그 레벨만 업데이트
            current_log_dir = self.settings_manager.get_log_directory()
            config = LoggingConfig(
                level=level_text,
                log_dir=Path(current_log_dir) if current_log_dir else None,
            )
            configure_logging(config)
        except Exception as e:
            # 실패해도 기존 동작은 유지
            pass

        # 설정 저장
        self.settings_manager.set_log_level(level_text)

    def log_initialization_message(self):
        """Log initialization message with current settings."""
        self.settings_manager.log_initialization_message()
