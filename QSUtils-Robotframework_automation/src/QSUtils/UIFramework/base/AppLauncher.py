#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common Application Launcher
QSMonitor, QSLogger, QSAutoReboot의 공통 실행 로직을 처리하는 모듈
"""

import sys
from typing import Type, Any

from QSUtils.UIFramework.config.SettingsManager import SettingsManager
from QSUtils.UIFramework.config.app_settings import AppSettings
from QSUtils.Utils.logging_config import configure_logging, LoggingConfig


class AppLauncher:
    """
    공통 애플리케이션 실행기를 제공하는 클래스
    각 애플리케이션의 중복 코드를 제거하기 위함
    """

    @staticmethod
    def launch_app(app_class: Type, app_config: Any, app_name: str = None) -> None:
        """
        설정 객체를 사용하여 애플리케이션을 실행하는 메서드

        Args:
            app_class: 실행할 애플리케이션 클래스
            app_config: 애플리케이션 설정 객체
            app_name: 애플리케이션 이름 (로깅용, None이면 설정 객체에서 가져옴)
        """
        # 앱 이름이 없으면 설정 객체에서 가져오기
        if app_name is None:
            app_name = app_config.get_app_type()

        # 설정 관리자 초기화
        settings_manager = SettingsManager(
            app_config.get_config_file(), app_config.get_default_settings()
        )

        # Load YAML-based settings and configure standard logging once
        settings = AppSettings.load(app_config.get_config_file())

        # For QSMonitor, don't create log file but keep log directory for other logs
        log_file = None if app_name == "QSMonitor" else f"{app_name}.log"

        configure_logging(
            LoggingConfig(
                app_name=app_name,
                level=settings.log_level,
                log_dir=settings.log_directory,  # Remove Path() wrapper to handle None properly
                log_file=log_file,
                to_console=True,
            )
        )

        # 애플리케이션 인스턴스 생성 및 실행 (설정 객체 전달)
        app = app_class(app_config)
        rc = app.run()
        sys.exit(rc)
