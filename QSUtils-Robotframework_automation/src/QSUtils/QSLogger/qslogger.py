#!/usr/bin/env python3

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from QSUtils.QSLogger.config import QSLoggerConfig
from QSUtils.UIFramework.base.AppLauncher import AppLauncher
from QSUtils.QSLogger.QSLoggerApplication import QSLoggerApplication


def main():
    """
    Main entry point for the QSLogger application.

    Creates and shows the main window using the base application framework.
    """
    app_config = QSLoggerConfig()
    AppLauncher.launch_app(QSLoggerApplication, app_config)


if __name__ == "__main__":
    main()
