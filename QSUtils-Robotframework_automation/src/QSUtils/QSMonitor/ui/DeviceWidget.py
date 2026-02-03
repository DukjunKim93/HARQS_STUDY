# -*- coding: utf-8 -*-
"""
Device tab view for the LogViewer application.
"""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget

from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.QSMonitor.services.CrashMonitorService import CrashMonitorService
from QSUtils.QSMonitor.ui.tab.AutoRebootTab import AutoRebootTab
from QSUtils.QSMonitor.ui.tab.GeneralTab import GeneralTab
from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.widgets.BaseDeviceWidget import BaseDeviceWidget, SessionState
from QSUtils.Utils.Logger import LOGD


class DeviceWidget(BaseDeviceWidget):
    """
    Tab widget for displaying and controlling logs from a specific Android device.
    """

    def __init__(self, parent, device_context: DeviceContext):
        """
        Initialize the device tab.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext instance for device management
        """

        # BaseDeviceWidget 초기화 (DeviceContext 전달)
        super().__init__(parent, device_context, min_width=350)

        # CommandHandler 생성
        self.command_handler = CommandHandler()

        # DeviceContext에 컴포넌트 등록
        self.device_context.register_app_component(
            "command_handler", self.command_handler
        )

        # 탭 인터페이스 생성 (먼저 생성해야 ui_manager가 general_tab에 접근 가능)
        self._create_tab_interface()

        # EventManager 준비 알림 (모든 컴포넌트가 자기 등록하도록 유도)
        self.event_manager.set_ready()

        # CrashMonitorService 생성 (자율적인 서비스)
        self.crash_service = CrashMonitorService(
            self.adb_device, self.device_context.event_manager
        )
        self.device_context.register_app_component("crash_service", self.crash_service)

        # Event 핸들러 등록
        self._setup_event_handlers()

    def _on_session_started(self, manual: bool):
        self.general_tab.on_session_started(manual)
        self.autoreboot_tab.set_enabled(True)

        self.crash_service.set_monitoring_interval(500)
        self.crash_service.start_monitoring()

    def _on_session_stopped(self):
        self.general_tab.on_session_stopped()
        self.autoreboot_tab.set_enabled(False)
        self.crash_service.stop_monitoring()

    def _setup_app_specific_ui(self):
        # BaseDeviceWidget의 _setup_app_specific_ui를 오버라이드하여 아무것도 하지 않음
        # 이렇게 하면 BaseDeviceWidget이 app_specific_layout만 제공하고,
        # DeviceWidget에서 나중에 탭 위젯을 추가할 수 있음
        pass

    def _setup_event_handlers(self):
        """Event 핸들러 설정"""
        LOGD("DeviceWidget: Setting up event handlers")

        # BaseDeviceWidget의 이벤트 핸들러 설정 먼저 호출 (중요!)
        # BaseDeviceWidget은 EventManager가 있을 때만 이벤트 핸들러를 설정함
        if self.event_manager:
            super()._setup_event_handlers()
            LOGD("DeviceWidget: BaseDeviceWidget event handlers setup completed")
        else:
            LOGD(
                "DeviceWidget: No EventManager available, skipping BaseDeviceWidget event handlers"
            )

        self.register_event_handler(
            QSMonitorEventType.CRASH_DETECTED, self._on_crash_detected
        )
        LOGD("DeviceWidget: Internal signal handlers connected")

    # -----------------------------
    # Event 기반 연결/해제 처리
    # -----------------------------
    def on_device_connected(self):
        """디바이스 연결 Event 처리 - QSMonitor 특화"""
        LOGD(f"DeviceWidget: Device {self.serial} connected event received.")
        # QSMonitor 특화 연결 처리가 필요하면 여기에 구현
        # 기본 처리는 BaseDeviceWidget에서 이미 handled됨

        self.start_session(
            manual=False if self.session_state == SessionState.PAUSED else True
        )

    def on_device_disconnected(self):
        """디바이스 연결 해제 Event 처리 - QSMonitor 특화"""
        LOGD(f"DeviceWidget: Device {self.serial} disconnected event received.")
        # QSMonitor 특화 연결 해제 처리가 필요하면 여기에 구현
        # 기본 처리는 BaseDeviceWidget에서 이미 handled됨
        self.stop_session()

    def _create_tab_interface(self):
        """탭 인터페이스 생성 - 별도 메서드로 분리"""
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()

        self.general_tab = GeneralTab(
            self, self.device_context, self.command_handler, self.on_toggle_clicked
        )

        # Auto Reboot 탭 생성
        self.autoreboot_tab = AutoRebootTab(
            self, self.device_context, self.command_handler
        )

        # 탭 위젯에 탭 추가
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.autoreboot_tab, "Auto Reboot")

        # app_specific_layout에 탭 위젯 추가
        self.app_specific_layout.addWidget(self.tab_widget)

        LOGD(f"DeviceWidget: Tab interface setup completed for {self.serial}")

        # BaseDeviceWidget의 공통 버튼 활성화 확인
        if hasattr(self, "control_buttons_frame") and self.control_buttons_frame:
            self.control_buttons_frame.show()

        # 레이아웃 업데이트
        self.update()

    def register_event_handler(self, event_type, handler):
        """
        이벤트 핸들러 등록 (EventManager 위임)

        Args:
            event_type: 이벤트 타입 ('reboot_completed', 'qs_state_changed', 'dump_completed', 'crash_detected')
            handler: 이벤트 핸들러 함수
        """
        self.event_manager.register_event_handler(event_type, handler)

    def _update_ui_controls_state(self, enabled: bool):
        """UI 컨트롤 활성화 상태 업데이트 (GeneralTab의 Start 버튼 포함)"""
        # 부모 클래스의 기본 컨트롤 업데이트
        super()._update_ui_controls_state(enabled)

        # GeneralTab의 toggle_btn 업데이트
        if hasattr(self, "general_tab") and self.general_tab:
            if hasattr(self.general_tab, "toggle_btn") and self.general_tab.toggle_btn:
                self.general_tab.toggle_btn.setEnabled(enabled)
                LOGD(
                    f"DeviceWidget: GeneralTab toggle_btn {'enabled' if enabled else 'disabled'}"
                )

    def on_toggle_clicked(self, manual: bool = False):
        """Start/Stop 버튼 클릭 처리
        Args:
            manual (bool): True if triggered by user action; False for automatic (e.g., reconnect)
        """
        if self.session_state in [SessionState.STOPPED, SessionState.PAUSED]:
            LOGD(f"DeviceWidget: Start button clicked. manual={manual}")
            self._start_user_session(manual=manual)
        else:
            LOGD("DeviceWidget: Stop button clicked.")
            self._stop_user_session()

    def _on_crash_detected(self, crash_info: dict):
        """crash 감지 콜백 핸들러"""
        crash_files = crash_info.get("crash_files", [])
        crash_count = crash_info.get("crash_count", 0)

        LOGD(
            f"DeviceWidget: Crash detected via callback - {crash_count} files: {crash_files}"
        )

        # BaseDeviceWidget의 덤프 기능 호출
        super().on_dump_clicked()
