# -*- coding: utf-8 -*-
"""
Network Interface 그룹을 포함하는 클래스
"""

from PySide6.QtWidgets import QGroupBox, QFormLayout, QVBoxLayout, QLineEdit

from QSUtils.UIFramework.widgets.BaseEventWidget import BaseEventWidget, UIElementGroup
from QSUtils.Utils import LOGD

GROUP_MINIMUM_WIDTH = 300


class NetworkInterfaceMonitorGroup(BaseEventWidget):
    """Network Interface 그룹을 포함하는 클래스"""

    def __init__(self, parent, event_manager):
        super().__init__(parent, event_manager, self.__class__.__name__)
        self.ui_elements = {}
        self._setup_ui()

        self.setup_event_handlers(self.event_manager)

    def _setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Network Interface 그룹
        self.network_interface_group = self._create_network_interface_group()
        self.network_interface_group.setMinimumWidth(GROUP_MINIMUM_WIDTH)
        main_layout.addWidget(self.network_interface_group)

    def _create_network_interface_group(self):
        """Network Interface 그룹 생성"""
        network_interface_group_box = QGroupBox("Network Interface")
        network_interface_group_layout = QFormLayout()
        network_interface_group_box.setLayout(network_interface_group_layout)

        # IPv4
        p2p0_ipv4_text = self.create_widget(
            QLineEdit, "p2p0_ipv4_text", UIElementGroup.SESSION_SYNC
        )
        p2p0_ipv4_text.setReadOnly(True)
        p2p0_ipv4_text.setPlaceholderText("N/A")
        network_interface_group_layout.addRow("IPv4:", p2p0_ipv4_text)

        # IPv6
        p2p0_ipv6_text = self.create_widget(
            QLineEdit, "p2p0_ipv6_text", UIElementGroup.SESSION_SYNC
        )
        p2p0_ipv6_text.setReadOnly(True)
        p2p0_ipv6_text.setPlaceholderText("N/A")
        network_interface_group_layout.addRow("IPv6:", p2p0_ipv6_text)

        # Flags
        p2p0_flags_text = self.create_widget(
            QLineEdit, "p2p0_flags_text", UIElementGroup.SESSION_SYNC
        )
        p2p0_flags_text.setReadOnly(True)
        p2p0_flags_text.setPlaceholderText("N/A")
        network_interface_group_layout.addRow("Flags:", p2p0_flags_text)

        return network_interface_group_box

    def get_ui_elements(self):
        """UI 요소들 반환"""
        return self.ui_elements

    def _update_ui_element(self, element_name, value):
        """특정 UI 요소 업데이트"""
        if element_name in self.ui_elements:
            widget = self.ui_elements[element_name]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))

    def update_ui_elements(self, ipv4: str, ipv6: str, flags: str):
        self._update_ui_element("p2p0_ipv4_text", ipv4)
        self._update_ui_element("p2p0_ipv6_text", ipv6)
        self._update_ui_element("p2p0_flags_text", flags)

    def setup_event_handlers(self, event_manager):
        """이벤트 핸들러 설정"""
        from QSUtils.QSMonitor.core.Events import QSMonitorEventType

        LOGD("NetworkInterfaceMonitorGroup: Setting up event handlers")

        # Network Interface 업데이트 이벤트 핸들러 등록
        event_manager.register_event_handler(
            QSMonitorEventType.NETWORK_INTERFACE_UPDATED,
            self._on_network_interface_updated,
        )

        LOGD("NetworkInterfaceMonitorGroup: Event handlers setup completed")

    def _register_specific_event_handlers(self, event_manager):
        """구체적인 Event 핸들러 등록 로직 구현"""
        from QSUtils.QSMonitor.core.Events import QSMonitorEventType

        event_manager.register_event_handler(
            QSMonitorEventType.NETWORK_INTERFACE_UPDATED,
            self._on_network_interface_updated,
        )
        LOGD("NetworkInterfaceMonitorGroup: Registered specific event handlers")

    def update_ui(self, data):
        """UI 업데이트 메서드 구현"""
        if isinstance(data, dict):
            ipv4 = data.get("ipv4", "N/A")
            ipv6 = data.get("ipv6", "N/A")
            flags = data.get("flags", "N/A")
            self.update_ui_elements(ipv4, ipv6, flags)

    def _on_network_interface_updated(self, data):
        """Network Interface 업데이트 이벤트 핸들러"""
        LOGD(f"NetworkInterfaceMonitorGroup: Received network interface update: {data}")

        if isinstance(data, dict):
            ipv4 = data.get("ipv4", "N/A")
            ipv6 = data.get("ipv6", "N/A")
            flags = data.get("flags", "N/A")
            self.update_ui_elements(ipv4, ipv6, flags)
