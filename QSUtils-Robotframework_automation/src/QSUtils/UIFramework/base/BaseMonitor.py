#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Monitor Application Class
공통 애플리케이션 기능을 제공하는 기반 클래스
"""

import signal
import sys
from typing import Type

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


class BaseMonitorApplication:
    """
    QSMonitor/QSLogMonitor의 공통 기능을 제공하는 기반 애플리케이션 클래스
    """

    def __init__(self, window_class: Type, app_name: str = None, app_config=None):
        """
        기반 애플리케이션 초기화

        Args:
            window_class: 메인 윈도우 클래스
            app_name: 애플리케이션 이름 (기존 호환용)
            app_config: 애플리케이션 설정 객체 (새로운 방식)
        """
        self.window_class = window_class
        self.app_name = app_name
        self.app_config = app_config

    def run(self) -> int:
        """
        애플리케이션 실행

        Returns:
            int: 애플리케이션 실행 결과 코드
        """
        app = QApplication(sys.argv)

        # app_config가 있으면 설정 객체를 전달, 없으면 기존 방식으로 윈도우 생성
        if self.app_config is not None:
            win = self.window_class(self.app_config)
        else:
            win = self.window_class()

        # 애플리케이션 설정
        self._setup_application(app, win)

        # 시그널 핸들러 설정
        self._setup_signal_handlers(app, win)

        # 윈도우 표시
        win.show()

        # 애플리케이션 실행
        return self._execute_app(app)

    def _setup_application(self, app: QApplication, win) -> None:
        """
        애플리케이션 기본 설정

        Args:
            app: QApplication 인스턴스
            win: 메인 윈도우 인스턴스
        """
        # 애플리케이션 종료 시 모든 디바이스 탭의 백그라운드 프로세스 중지
        app.aboutToQuit.connect(win.shutdown_all_tabs)

    def _setup_signal_handlers(self, app: QApplication, win) -> None:
        """
        시그널 핸들러 설정

        Args:
            app: QApplication 인스턴스
            win: 메인 윈도우 인스턴스
        """

        def _graceful_exit(signum, frame):
            """
            그레이스풀 종료 처리

            Args:
                signum: 시그널 번호
                frame: 스택 프레임
            """
            try:
                # Qt 루프에 종료 이벤트 포스트
                QTimer.singleShot(0, app.quit)
            except Exception:
                # 예외 발생 시 즉시 종료
                sys.exit(0)

        # Windows 호환성 고려한 시그널 핸들러 등록
        try:
            signal.signal(signal.SIGINT, _graceful_exit)
            # Windows에서는 SIGTERM 지원이 제한적
            if hasattr(signal, "SIGTERM") and sys.platform != "win32":
                signal.signal(signal.SIGTERM, _graceful_exit)
        except Exception:
            # 시그널 핸들러 등록 실패 시 무시
            pass

    def _execute_app(self, app: QApplication) -> int:
        """
        애플리케이션 실행

        Args:
            app: QApplication 인스턴스

        Returns:
            int: 실행 결과 코드
        """
        try:
            # 애플리케이션 메인 루프 실행
            rc = app.exec()
        except KeyboardInterrupt:
            # Ctrl+C로 종료 시 트레이스백 없이 깔끔하게 종료
            rc = 0
        return rc
