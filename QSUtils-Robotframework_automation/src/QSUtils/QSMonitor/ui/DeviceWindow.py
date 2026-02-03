# -*- coding: utf-8 -*-
"""
Device window container for MDI interface.
Wraps DeviceTab in a window that can be managed by QMdiArea.
"""

from PySide6.QtWidgets import QLabel

from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.QSMonitor.core.GlobalEvents import GlobalEventType
from QSUtils.QSMonitor.ui.DeviceWidget import DeviceWidget
from QSUtils.UIFramework.base.BaseDeviceWindow import BaseDeviceWindow
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.base.GlobalEventManager import get_global_event_bus


class DeviceWindow(BaseDeviceWindow):
    """
    Device window container for MDI interface.
    Wraps DeviceTab in a window that can be managed by QMdiArea.
    """

    def __init__(self, parent, device_context: DeviceContext):
        """
        Initialize the device window.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext instance for device management
        """
        super().__init__(parent, device_context, DeviceWidget)

    def _add_custom_status_widgets(self):
        """AutoReboot 및 업로드 상태 표시를 위한 설정 (BaseDeviceWindow 훅 구현)"""
        self.autoreboot_label = QLabel("")
        self.autoreboot_label.hide()
        # 왼쪽에 표시하기 위해 addWidget 사용
        self.status_bar.addWidget(self.autoreboot_label)

        self.device_context.event_manager.register_event_handler(
            QSMonitorEventType.AUTO_REBOOT_STATUS_CHANGED,
            self._on_autoreboot_status_changed,
        )

        # JFrog 업로드 시작 시 덤프 상태를 제거하기 위해 전역 이벤트 구독
        get_global_event_bus().register_event_handler(
            GlobalEventType.JFROG_UPLOAD_STARTED, self._on_jfrog_upload_started
        )

    def _on_autoreboot_status_changed(self, args: dict):
        status = args.get("status", "")

        if status == "Stopped" or not status:
            self.autoreboot_label.setText("")
        else:
            # Count 정보 제거
            self.autoreboot_label.setText(f"AutoReboot: {status}")

        self._update_left_status_layout()

    def _on_jfrog_upload_started(self, args: dict):
        """JFrog 업로드 시작 시 덤프 상태 표시 제거"""
        targets = args.get("targets", [])
        if not targets:
            # targets가 없으면 모든 장치를 대상으로 간주하거나 무시할 수 있음.
            # 여기서는 안전하게 현재 장치가 덤프 상태라면 지워줍니다.
            if self.dump_label.text():
                self.dump_label.setText("")
                self._update_left_status_layout()
            return

        # 시리얼 번호 비교 (공백 제거 및 문자열 변환 강화)
        my_serial = str(self.device_context.serial).strip()
        target_serials = []
        for t in targets:
            if isinstance(t, (list, tuple, set)):
                target_serials.extend([str(x).strip() for x in t])
            else:
                target_serials.append(str(t).strip())

        if my_serial in target_serials:
            # 덤프 상태 라벨 텍스트를 비워서 AutoReboot 상태가 표시되도록 함
            self.dump_label.setText("")
            self._update_left_status_layout()

    def _update_left_status_layout(self):
        """왼쪽 상태바 영역의 우선순위 기반 레이아웃 조정"""
        # 부모 클래스의 기본 가시성 제어 수행 (dump_label 보이기/숨기기)
        super()._update_left_status_layout()

        # 우선순위: Dump > AutoReboot
        # dump_label이 표시 중(텍스트가 있음)이면 autoreboot_label은 숨깁니다.
        if not self.dump_label.isHidden():
            self.autoreboot_label.hide()
        else:
            # 덤프 중이 아닐 때만 autoreboot_label의 텍스트 여부에 따라 표시
            if self.autoreboot_label.text():
                self.autoreboot_label.show()
            else:
                self.autoreboot_label.hide()

    def get_device_tab(self) -> DeviceWidget:
        """내부 DeviceTab 인스턴스 반환"""
        return self.device_tab

    def closeEvent(self, event):
        """윈도우 닫기 시 리소스 정리"""
        # 이벤트 핸들러 해제
        self.device_context.event_manager.unregister_event_handler(
            QSMonitorEventType.AUTO_REBOOT_STATUS_CHANGED,
            self._on_autoreboot_status_changed,
        )
        get_global_event_bus().unregister_event_handler(
            GlobalEventType.JFROG_UPLOAD_STARTED, self._on_jfrog_upload_started
        )
        super().closeEvent(event)
