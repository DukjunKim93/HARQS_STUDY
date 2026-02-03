import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from QSUtils.QSMonitor.core.config import QSMonitorConfig
from QSUtils.UIFramework.base.AppLauncher import AppLauncher
from QSUtils.QSMonitor.QSMonitorApplication import QSMonitorApplication


def main():
    """
    Main entry point for the QSMonitor application.

    Creates and shows the main window using the base application framework.
    """
    app_config = QSMonitorConfig()
    AppLauncher.launch_app(QSMonitorApplication, app_config)


if __name__ == "__main__":
    main()
