#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QSMonitor Config 테스트
QSMonitorConfig 클래스 테스트
"""

from pathlib import Path

import pytest

from QSUtils.QSMonitor.core.config import QSMonitorConfig


class TestQSMonitorConfig:
    """QSMonitorConfig 테스트"""

    def test_get_config_file(self):
        """설정 파일 경로 반환 테스트"""
        config_file = QSMonitorConfig.get_config_file()
        assert isinstance(config_file, Path)
        assert config_file.name == "qsmonitor.json"
        assert "QSUtils" in str(config_file)

    def test_get_default_settings(self):
        """기본 설정 반환 테스트"""
        settings = QSMonitorConfig.get_default_settings()
        assert isinstance(settings, dict)
        assert "log_directory" in settings
        assert "window_geometry" in settings
        assert "filter_rules" in settings
        assert "log_level" in settings
        assert "auto_reboot" in settings
        assert "monitoring" in settings

    def test_get_app_title(self):
        """애플리케이션 타이틀 반환 테스트"""
        title = QSMonitorConfig.get_app_title()
        assert isinstance(title, str)
        assert title == "Q-Symphony Device Monitor"

    def test_get_app_type(self):
        """애플리케이션 타입 반환 테스트"""
        app_type = QSMonitorConfig.get_app_type()
        assert isinstance(app_type, str)
        assert app_type == "QSMonitor"

    def test_setup_specific_features(self):
        """QSMonitor 전용 기능 설정 테스트 (확장용)"""
        # 이 메서드는 현재 비어있으므로 예외 없이 실행되는지만 확인
        try:
            QSMonitorConfig.setup_specific_features()
        except Exception as e:
            pytest.fail(f"setup_specific_features() raised an exception: {e}")

    def test_default_settings_structure(self):
        """기본 설정의 구조 검증"""
        settings = QSMonitorConfig.get_default_settings()

        # window_geometry 구조 검증
        geometry = settings["window_geometry"]
        assert "width" in geometry
        assert "height" in geometry
        assert "x" in geometry
        assert "y" in geometry
        assert isinstance(geometry["width"], int)
        assert isinstance(geometry["height"], int)

        # auto_reboot 구조 검증
        auto_reboot = settings["auto_reboot"]
        assert "interval" in auto_reboot
        assert "sync_before_reboot" in auto_reboot
        assert "check_qs_before_reboot" in auto_reboot
        assert "reboot_after_qs_on" in auto_reboot
        assert isinstance(auto_reboot["interval"], int)
        assert isinstance(auto_reboot["sync_before_reboot"], bool)

        # monitoring 구조 검증
        monitoring = settings["monitoring"]
        assert "interval" in monitoring
        assert isinstance(monitoring["interval"], int)
