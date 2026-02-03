#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device window container for MDI interface.
Wraps DeviceTab in a window that can be managed by QMdiArea.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout

from QSUtils.QSLogger.views.DeviceWidget import DeviceWidget
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.Utils.Logger import LOGD


class DeviceWindow(QWidget):
    """
    Device window container for MDI interface.
    Wraps DeviceTab in a window that can be managed by QMdiArea.
    """

    def __init__(self, parent, device_context: DeviceContext):
        """
        Initialize the device window.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext instance containing device-specific components
        """
        super().__init__(parent)

        self.device_context = device_context

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # DeviceTab 생성 using DeviceContext
        self.device_tab = DeviceWidget(parent=self, device_context=device_context)
        LOGD(
            f"DeviceWindow: Created DeviceWidget for {device_context.serial} using DeviceContext"
        )
        layout.addWidget(self.device_tab)
        self.setLayout(layout)
        self._connect_signals()

    def _connect_signals(self):
        """시그널 연결"""
        # DeviceTab의 시그널이 필요하다면 여기서 연결
        pass

    def get_device_tab(self) -> DeviceWidget:
        """내부 DeviceTab 인스턴스 반환"""
        return self.device_tab

    def closeEvent(self, event):
        """윈도우 닫힘 이벤트 처리"""
        # DeviceTab 정리
        if hasattr(self, "device_tab"):
            # Stop monitoring if it's running
            if hasattr(self.device_tab, "is_running") and self.device_tab.is_running:
                self.device_tab.on_toggle_clicked(
                    manual=False
                )  # 자동 정지 시 manual=False

            # 스레드 안전 종료를 위해 잠시 대기
            from PySide6.QtCore import QCoreApplication

            QCoreApplication.processEvents()

        super().closeEvent(event)
