#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base device window container for MDI interface.

Provides a common base class for device windows that can be managed by QMdiArea.
Wraps device-specific widgets in a window container with DeviceContext architecture.
"""

from typing import TypeVar, Generic, Type

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStatusBar, QLabel

from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.widgets.BaseDeviceWidget import BaseDeviceWidget, SessionState
from QSUtils.Utils.Logger import LOGD

T = TypeVar("T", bound=BaseDeviceWidget)


class BaseDeviceWindow(QWidget, Generic[T]):
    """
    Base device window container for MDI interface.
    Wraps device-specific widgets in a window that can be managed by QMdiArea.

    This class provides the common structure for all device windows across different
    applications (QSMonitor, QSLogger, etc.) while maintaining DeviceContext architecture.
    """

    def __init__(
        self,
        parent,
        device_context: DeviceContext,
        device_widget_cls: Type[T],
    ):
        """
        Initialize the base device window.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext instance for device management
            device_widget_cls: Class type for the device-specific widget
        """
        super().__init__(parent)
        self.device_context = device_context
        self.device_widget_cls = device_widget_cls

        # Setup layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create device-specific widget using DeviceContext architecture
        self.device_tab = self._create_device_widget()
        LOGD(
            f"BaseDeviceWindow: Created {device_widget_cls.__name__} for {device_context.serial}"
        )

        layout.addWidget(self.device_tab)

        # Setup Status Bar
        self.status_bar = QStatusBar()
        self._setup_status_bar()
        layout.addWidget(self.status_bar)

        self.setLayout(layout)

    def _setup_status_bar(self):
        """기본 상태바 설정 및 이벤트 등록"""
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setStyleSheet(
            "QStatusBar { border-top: 1px solid #808080; padding: 2px; }"
        )

        # 현재 상태를 반영하여 초기 텍스트 설정
        is_connected = self.device_context.adb_device.is_connected
        conn_text = "● Connected" if is_connected else "○ Disconnected"

        session_state = getattr(self.device_tab, "session_state", SessionState.STOPPED)
        if session_state == SessionState.RUNNING:
            session_text = "▶ Running"
        elif session_state == SessionState.PAUSED:
            session_text = "⏸ Paused"
        else:
            session_text = "■ Stopped"

        # 기본 상태 항목들
        self.conn_label = QLabel(conn_text)
        self.session_label = QLabel(session_text)
        self.dump_label = QLabel("")

        # 영구 위젯으로 추가 (오른쪽)
        self.status_bar.addPermanentWidget(self.session_label)
        self.status_bar.addPermanentWidget(self.conn_label)

        # 기본 상태 항목 (왼쪽 - 덤프 상태)
        self.status_bar.addWidget(self.dump_label)
        self.dump_label.hide()

        # 하위 클래스에서 추가 위젯을 넣을 수 있는 훅 호출
        self._add_custom_status_widgets()

        # 레이아웃 초기화
        self._update_left_status_layout()

        # 이벤트 등록
        self.device_context.event_manager.register_event_handler(
            CommonEventType.DEVICE_CONNECTION_CHANGED, self._on_connection_changed
        )
        self.device_context.event_manager.register_event_handler(
            CommonEventType.SESSION_STATE_CHANGED, self._on_session_state_changed
        )
        self.device_context.event_manager.register_event_handler(
            CommonEventType.DUMP_PROGRESS_UPDATED, self._on_dump_progress_updated
        )
        self.device_context.event_manager.register_event_handler(
            CommonEventType.DUMP_STATUS_CHANGED, self._on_dump_status_changed
        )

    def _on_connection_changed(self, args: dict):
        connected = args.get("connected", False)
        text = "● Connected" if connected else "○ Disconnected"
        self.conn_label.setText(text)

    def _on_session_state_changed(self, args: dict):
        state = args.get("state", SessionState.STOPPED)
        if state == SessionState.RUNNING:
            text = "▶ Running"
        elif state == SessionState.PAUSED:
            text = "⏸ Paused"
        else:
            text = "■ Stopped"

        self.session_label.setText(text)

    def _on_dump_progress_updated(self, args: dict):
        progress = args.get("progress", 0)
        stage = args.get("stage", "")
        message = args.get("message", "")

        if message:
            # message가 있으면 우선 표시
            self.dump_label.setText(f"Dump: {message}")
        elif progress > 0 or stage:
            self.dump_label.setText(f"Dump {progress}% ({stage})")
        else:
            self.dump_label.setText("Dump...")

        self._update_left_status_layout()

    def _on_dump_status_changed(self, args: dict):
        status = args.get("status", "")
        if status == "completed":
            self.dump_label.setText("Dump ✓")
        elif status == "failed":
            self.dump_label.setText("Dump ✗")
        elif status == "cancelled":
            self.dump_label.setText("Dump (Cancelled)")
        elif status == "in_progress":
            self.dump_label.setText("Dump...")
        else:
            self.dump_label.setText("")
        self._update_left_status_layout()

    def _update_left_status_layout(self):
        """왼쪽 상태바 영역의 레이아웃 및 가시성 조정 (서브클래스 확장용)"""
        if self.dump_label.text():
            self.dump_label.show()
        else:
            self.dump_label.hide()

    def _add_custom_status_widgets(self):
        """하위 클래스에서 상태바 위젯을 추가하기 위한 훅"""
        pass

    def add_status_widget(self, widget: QWidget, stretch: int = 0):
        """상태바에 일반 위젯 추가 (왼쪽)"""
        self.status_bar.addWidget(widget, stretch)

    def add_permanent_status_widget(self, widget: QWidget, stretch: int = 0):
        """상태바에 영구 위젯 추가 (오른쪽)"""
        self.status_bar.addPermanentWidget(widget, stretch)

    def _create_device_widget(self) -> T:
        """
        Create the device-specific widget.

        Returns:
            T: The created device widget instance
        """
        return self.device_widget_cls(parent=self, device_context=self.device_context)

    def get_device_tab(self) -> T:
        """
        Get the internal device widget instance.

        Returns:
            T: The device widget instance
        """
        return self.device_tab

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        # 이벤트 핸들러 해제
        self.device_context.event_manager.unregister_event_handler(
            CommonEventType.DEVICE_CONNECTION_CHANGED, self._on_connection_changed
        )
        self.device_context.event_manager.unregister_event_handler(
            CommonEventType.SESSION_STATE_CHANGED, self._on_session_state_changed
        )
        self.device_context.event_manager.unregister_event_handler(
            CommonEventType.DUMP_PROGRESS_UPDATED, self._on_dump_progress_updated
        )
        self.device_context.event_manager.unregister_event_handler(
            CommonEventType.DUMP_STATUS_CHANGED, self._on_dump_status_changed
        )

        # Clean up device widget if it's running
        if hasattr(self, "device_tab") and self.device_tab:
            # Stop monitoring if it's running
            if hasattr(self.device_tab, "is_running") and self.device_tab.is_running:
                if hasattr(self.device_tab, "on_toggle_clicked"):
                    self.device_tab.on_toggle_clicked()

            # Thread-safe shutdown with brief wait
            QCoreApplication.processEvents()

        super().closeEvent(event)
