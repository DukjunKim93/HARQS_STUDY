# -*- coding: utf-8 -*-
"""
Auto Reboot 탭을 관리하는 클래스
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout

from QSUtils.QSMonitor.features.AutoReboot.AutoRebootGroup import AutoRebootGroup
from QSUtils.QSMonitor.features.DefaultMonitor.DefaultMonitorFeature import (
    DefaultMonitorFeature,
)
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.Utils.Logger import LOGD


class AutoRebootTab(QWidget):
    """Auto Reboot 탭을 관리하는 클래스"""

    def __init__(self, parent, device_context: DeviceContext, command_handler=None):
        """
        AutoRebootTab 초기화

        Args:
            parent: 부모 위젯 (보통 DeviceWidget)
            device_context: DeviceContext 인스턴스
            command_handler: CommandHandler 인스턴스
        """
        super().__init__(parent)

        # device_context가 None이면 예외 발생
        if device_context is None:
            raise ValueError("device_context cannot be None")
        self.device_context = device_context
        self.event_manager = device_context.event_manager

        # command_handler가 None이면 예외 발생
        if command_handler is None:
            raise ValueError("command_handler cannot be None")
        self.command_handler = command_handler

        # UI 설정
        self._setup_ui()

        # Auto Reboot 그룹 생성
        self._create_auto_reboot_group()

        # 상태 그룹 생성
        self._create_status_groups()

        LOGD(f"AutoRebootTab: Initialized for device {self.device_context.serial}")

    def _setup_ui(self):
        """기본 UI 레이아웃 설정"""
        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

    def _create_auto_reboot_group(self):
        """Auto Reboot 그룹 생성"""
        # AutoRebootGroup 인스턴스 생성 (event_manager 전달)
        self.autoreboot_group = AutoRebootGroup(self, self.device_context)

        # 메인 레이아웃에 추가
        self.main_layout.addWidget(self.autoreboot_group)

    def _create_status_groups(self):
        """Q-Symphony, ACM, Multiroom 상태 그룹 생성"""
        # Auto Reboot 탭용 DefaultMonitorFeature 인스턴스 생성 (EventManager와 CommandHandler 전달)
        self.default_monitor_feature = DefaultMonitorFeature(
            self, self.device_context, self.command_handler
        )

        # 메인 레이아웃에 추가
        self.main_layout.addWidget(self.default_monitor_feature.get_widget())

    def set_enabled(self, enabled: bool):
        """
        Auto Reboot 탭의 UI 활성화 상태를 설정합니다 (DeviceWidget에서 호출용)

        Args:
            enabled: 활성화 여부
        """
        try:
            # Auto Reboot 그룹 활성화/비활성화
            self.autoreboot_group.apply_session_state(enabled)

            # 상태 그룹 활성화/비활성화
            self.default_monitor_feature.apply_session_state(enabled)
        except Exception as e:
            LOGD(f"AutoRebootTab: Error in set_enabled: {e}")
