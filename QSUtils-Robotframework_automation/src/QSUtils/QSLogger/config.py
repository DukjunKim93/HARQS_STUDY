#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QSLogger Application Configuration
애플리케이션별 설정을 관리하는 클래스
"""

from pathlib import Path
from typing import Dict, Any


class QSLoggerConfig:
    """QSLogger 애플리케이션 설정 클래스"""

    @staticmethod
    def get_config_file() -> Path:
        """설정 파일 경로 반환"""
        return Path.home() / ".QSUtils" / "qslogger.json"

    @staticmethod
    def get_default_settings() -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "log_directory": str(Path.home() / "QSMonitor_logs"),
            "window_geometry": {"width": 770, "height": 980, "x": 200, "y": 200},
            "filter_rules": [],
            "log_level": "Error",
        }

    @staticmethod
    def get_app_title() -> str:
        """애플리케이션 타이틀 반환"""
        return "Q-Symphony Log Monitor"

    @staticmethod
    def get_app_type() -> str:
        """애플리케이션 타입 반환"""
        return "QSLogger"

    @staticmethod
    def setup_specific_features():
        """QSLogger 전용 기능 설정 (확장용)"""
        pass
