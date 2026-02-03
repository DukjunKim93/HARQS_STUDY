#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QSLogger Application Class
QSLogger 애플리케이션 실행을 위한 구체적인 구현
"""

from QSUtils.UIFramework.base.BaseMonitor import BaseMonitorApplication


class QSLoggerApplication(BaseMonitorApplication):
    """
    QSLogger 애플리케이션 클래스
    """

    def __init__(self, app_config=None):
        """
        QSLogger 애플리케이션 초기화
        """
        from QSUtils.QSLogger.views.MainWindow import MainWindow

        if app_config is not None:
            super().__init__(MainWindow, app_config=app_config)
        else:
            super().__init__(MainWindow, "QSLogger")
