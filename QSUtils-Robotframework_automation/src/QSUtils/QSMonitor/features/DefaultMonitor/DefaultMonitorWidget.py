# -*- coding: utf-8 -*-
"""
Q-Symphony, ACM, Multiroom 그룹을 포함하는 베이스 클래스
"""

from typing import Any, List

from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QCheckBox,
)

from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.UIFramework.widgets.BaseEventWidget import BaseEventWidget, UIElementGroup
from QSUtils.Utils.Logger import LOGD

GROUP_MINIMUM_WIDTH = 300


class DefaultMonitorWidget(BaseEventWidget):
    """Q-Symphony, ACM, Multiroom 그룹을 포함하는 기본 상태 그룹 클래스"""

    def __init__(self, parent, event_manager: EventManager):
        # event_manager가 None이면 예외 발생
        if event_manager is None:
            raise ValueError("event_manager cannot be None")

        super().__init__(parent, event_manager, self.__class__.__name__)
        self._setup_ui()
        self._setup_event_handlers()

    def _setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_container.setLayout(left_layout)

        # Q-Symphony 그룹 (왼쪽)
        self.qsymphony_group = self._create_qsymphony_group()
        self.qsymphony_group.setMinimumWidth(GROUP_MINIMUM_WIDTH)
        left_layout.addWidget(self.qsymphony_group)
        left_layout.addStretch()

        # 오른쪽에 ACM과 Multiroom 그룹들을 세로로 배치
        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_container.setLayout(right_layout)

        # ACM 그룹
        self.acm_group = self._create_acm_group()
        self.acm_group.setMinimumWidth(GROUP_MINIMUM_WIDTH)
        right_layout.addWidget(self.acm_group)

        # Multiroom 그룹
        self.multiroom_group = self._create_multiroom_group()
        self.multiroom_group.setMinimumWidth(GROUP_MINIMUM_WIDTH)
        right_layout.addWidget(self.multiroom_group)
        right_layout.addStretch()

        main_layout.addWidget(left_container)
        main_layout.addWidget(right_container)

    def _create_qsymphony_group(self):
        """Q-Symphony 그룹 생성"""
        qsymphony_group_box = QGroupBox("Q-Symphony")
        qsymphony_group_layout = QFormLayout()
        qsymphony_group_box.setLayout(qsymphony_group_layout)

        # Q-Symphony State
        qs_state_text = self.create_widget(
            QCheckBox, "qs_state_text", UIElementGroup.ALWAYS_DISABLED
        )
        qs_state_text.setStyleSheet(
            "            QCheckBox {"
            "                width: 20px;"
            "                height: 20px;"
            "                border-radius: 10px;"
            "                padding: 0px;"
            "                font-size: 7px;"
            "                font-weight: bold;"
            "                border: 1px solid #ccc;"
            "                text-align: center;"
            "            }"
            "            QCheckBox::indicator {"
            "                width: 0px;"
            "                height: 0px;"
            "                border: none;"
            "                background: none;"
            "                margin: 0px;"
            "                padding: 0px;"
            "            }"
            "            QCheckBox:checked {"
            "                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #45a049);"
            "                color: white;"
            "                border-color: #4CAF50;"
            "                text-align: center;"
            "            }"
            "            QCheckBox:unchecked {"
            "                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff4444, stop:1 #cc0000);"
            "                color: white;"
            "                border-color: #cc0000;"
            "                text-align: center;"
            "            }"
            "            QCheckBox:hover {"
            "                border-color: #999;"
            "            }"
            "        "
        )
        qs_state_text.setText("")
        qsymphony_state_layout = QHBoxLayout()
        qsymphony_state_layout.addStretch()
        qsymphony_state_layout.addWidget(qs_state_text)
        qsymphony_group_layout.addRow("State:", qsymphony_state_layout)

        # Sound Mode
        sound_mode_text = self.create_widget(
            QLineEdit, "sound_mode_text", UIElementGroup.SESSION_SYNC
        )
        sound_mode_text.setReadOnly(True)
        qsymphony_group_layout.addRow("Sound Mode:", sound_mode_text)

        # Symphony Mode Type
        symphony_mode_type_text = self.create_widget(
            QLineEdit, "symphony_mode_type_text", UIElementGroup.SESSION_SYNC
        )
        symphony_mode_type_text.setReadOnly(True)
        qsymphony_group_layout.addRow("Symphony Mode:", symphony_mode_type_text)

        # Speaker Mode
        qsymphony_mode_text = self.create_widget(
            QLineEdit, "qsymphony_mode_text", UIElementGroup.SESSION_SYNC
        )
        qsymphony_mode_text.setReadOnly(True)
        qsymphony_group_layout.addRow("Speaker Mode:", qsymphony_mode_text)

        # Adjust Level
        adjust_level_text = self.create_widget(
            QLineEdit, "adjust_level_text", UIElementGroup.SESSION_SYNC
        )
        adjust_level_text.setReadOnly(True)
        qsymphony_group_layout.addRow("Adjust Level:", adjust_level_text)

        return qsymphony_group_box

    def _create_acm_group(self):
        """ACM 그룹 생성"""
        acm_group_box = QGroupBox("ACM")
        acm_group_layout = QFormLayout()
        acm_group_box.setLayout(acm_group_layout)

        acm_service_state_text = self.create_widget(
            QLineEdit, "acm_service_state_text", UIElementGroup.SESSION_SYNC
        )
        acm_service_state_text.setReadOnly(True)
        acm_group_layout.addRow("Service State:", acm_service_state_text)

        return acm_group_box

    def _create_multiroom_group(self):
        """Multiroom 그룹 생성"""
        multiroom_group_box = QGroupBox("Multiroom")
        multiroom_group_layout = QFormLayout()
        multiroom_group_box.setLayout(multiroom_group_layout)

        multiroom_grouptype_text = self.create_widget(
            QLineEdit, "multiroom_grouptype_text", UIElementGroup.SESSION_SYNC
        )
        multiroom_grouptype_text.setReadOnly(True)
        multiroom_group_layout.addRow("Group Type:", multiroom_grouptype_text)

        multiroom_mode_text = self.create_widget(
            QLineEdit, "multiroom_mode_text", UIElementGroup.SESSION_SYNC
        )
        multiroom_mode_text.setReadOnly(True)
        multiroom_group_layout.addRow("Mode:", multiroom_mode_text)

        return multiroom_group_box

    def get_ui_elements(self):
        """UI 요소들 반환"""
        return self.ui_elements

    def update_ui_element(self, element_name, value):
        """특정 UI 요소 업데이트"""
        if element_name in self.ui_elements:
            widget = self.ui_elements[element_name]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QCheckBox):
                if value == "On":
                    widget.setChecked(True)
                    widget.setText("")
                elif value == "Off":
                    widget.setChecked(False)
                    widget.setText("")
                else:
                    widget.setChecked(False)
                    widget.setText("")

    def _groups_set_enabled(self, ui_element_names: List[str], enabled: bool):
        ui_elements = self.get_ui_elements()
        for element_name in ui_element_names:
            if element_name in ui_elements:
                widget = ui_elements[element_name]
                if widget is not None:
                    widget.setEnabled(enabled)

    def _symphony_groups_set_enabled(self, enabled: bool):
        """Q-Symphony 관련 UI 요소들의 활성화 상태를 설정합니다 (protected method)"""
        ui_element_names = [
            "qs_state_text",
            "sound_mode_text",
            "qsymphony_mode_text",
            "adjust_level_text",
            "symphony_mode_type_text",
        ]
        self._groups_set_enabled(ui_element_names, enabled)

    def _acm_groups_set_enabled(self, enabled: bool):
        """ACM 관련 UI 요소들의 활성화 상태를 설정합니다 (protected method)"""
        ui_element_names = ["acm_service_state_text"]
        self._groups_set_enabled(ui_element_names, enabled)

    def _multiroom_groups_set_enabled(self, enabled: bool):
        """Multiroom 관련 UI 요소들의 활성화 상태를 설정합니다 (protected method)"""
        ui_element_names = ["multiroom_grouptype_text", "multiroom_mode_text"]
        self._groups_set_enabled(ui_element_names, enabled)

    def update_ui(self, data: Any) -> None:
        """
        UI 업데이트 메서드 (BaseEventWidget 추상 메서드 구현)

        Args:
            data: UI 업데이트에 필요한 데이터
        """
        # data가 딕셔너리인 경우 각 키에 해당하는 UI 요소 업데이트
        if isinstance(data, dict):
            for key, value in data.items():
                self.update_ui_element(key, value)
        else:
            LOGD(f"{self.group_name}: update_ui called with non-dict data: {data}")

    def _register_specific_event_handlers(self, event_manager: EventManager):
        """DefaultMonitorGroup 특정 Event 핸들러 등록"""
        event_manager.register_event_handler(
            QSMonitorEventType.SYMPHONY_STATUS_UPDATED, self.on_symphony_status_updated
        )
        event_manager.register_event_handler(
            QSMonitorEventType.PREFERENCE_DATA_UPDATED, self.on_preference_data_updated
        )
        event_manager.register_event_handler(
            QSMonitorEventType.SYMPHONY_GROUP_UPDATED, self.on_symphony_group_updated
        )
        event_manager.register_event_handler(
            QSMonitorEventType.SYMPHONY_VOLUME_UPDATED, self.on_symphony_volume_updated
        )
        LOGD("DefaultMonitorGroup: Registered specific event handlers")

    def _setup_event_handlers(self):
        """
        이벤트 핸들러 설정 (BaseEventWidget 메서드 오버라이드)
        """
        LOGD(f"{self.group_name}: Setting up event handlers")

        # DeviceWidget에서 발생하는 이벤트 구독
        self.register_event_handler(
            QSMonitorEventType.SYMPHONY_STATUS_UPDATED, self.on_symphony_status_updated
        )
        self.register_event_handler(
            QSMonitorEventType.PREFERENCE_DATA_UPDATED, self.on_preference_data_updated
        )
        self.register_event_handler(
            QSMonitorEventType.SYMPHONY_GROUP_UPDATED, self.on_symphony_group_updated
        )
        self.register_event_handler(
            QSMonitorEventType.SYMPHONY_VOLUME_UPDATED, self.on_symphony_volume_updated
        )

    def on_symphony_status_updated(self, args) -> None:
        """
        Symphony 상태 업데이트 이벤트 핸들러

        Args:
            args: 이벤트 데이터 딕셔너리
        """
        LOGD(f"{self.group_name}: Handling symphony_status_updated event")

        qs_state = args.get("qs_state", "Unknown")
        sound_mode = args.get("sound_mode", "Unknown")
        mode_type = args.get("mode_type_display", "Unknown")

        # Q-Symphony State 업데이트
        self.update_ui_element("qs_state_text", qs_state)

        # Sound Mode 업데이트 (QS가 Off인 경우 N/A로 표시)
        if qs_state == "Off":
            self.update_ui_element("sound_mode_text", "N/A")
        else:
            self.update_ui_element("sound_mode_text", sound_mode)

        # Symphony Mode Type 업데이트
        self.update_ui_element("symphony_mode_type_text", mode_type)

    def on_preference_data_updated(self, args) -> None:
        """
        Preference 데이터 업데이트 이벤트 핸들러

        Args:
            args: 이벤트 데이터 딕셔너리
        """
        LOGD(f"{self.group_name}: Handling preference_data_updated event")

        acm_service_state = args.get("acm_service_state", "Unknown")
        multiroom_grouptype = args.get("multiroom_grouptype", "Unknown")
        multiroom_mode = args.get("multiroom_mode", "Unknown")

        # ACM Service State 업데이트
        self.update_ui_element("acm_service_state_text", acm_service_state)

        # Multiroom Group Type 업데이트
        self.update_ui_element("multiroom_grouptype_text", multiroom_grouptype)

        # Multiroom Mode 업데이트
        self.update_ui_element("multiroom_mode_text", multiroom_mode)

    def on_symphony_group_updated(self, args) -> None:
        """
        Symphony 그룹 업데이트 이벤트 핸들러

        Args:
            args: 이벤트 데이터 딕셔너리
        """
        LOGD(f"{self.group_name}: Handling symphony_group_updated event")

        group_mode = args.get("group_mode", "Unknown")

        # Speaker Mode 업데이트
        self.update_ui_element("qsymphony_mode_text", group_mode)

    def on_symphony_volume_updated(self, args) -> None:
        """
        Symphony 볼륨 업데이트 이벤트 핸들러

        Args:
            args: 이벤트 데이터 딕셔너리
        """
        LOGD(f"{self.group_name}: Handling symphony_volume_updated event")

        volume = args.get("volume", 0)

        # Adjust Level 업데이트
        self.update_ui_element("adjust_level_text", str(volume))
