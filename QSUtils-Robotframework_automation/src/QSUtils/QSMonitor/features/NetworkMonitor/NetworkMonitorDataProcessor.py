# -*- coding: utf-8 -*-
"""
NetworkInterfaceMonitorDataProcessor - Network Interface 상태 데이터 처리 및 이벤트 발생 담당 클래스
"""

from typing import Any, Optional

from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.QSMonitor.features.base.BaseDataProcessor import BaseDataProcessor
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_network_interface import NetworkInterfaceCommand


class NetworkMonitorDataProcessor(BaseDataProcessor):
    """
    Network Interface 상태 데이터 처리 및 이벤트 발생 담당 클래스

    DeviceWidget에서 Network Interface 데이터 처리 로직을 분리하여 책임을 명확히 분리하고
    중복 코드를 제거하기 위한 클래스
    """

    def __init__(self, event_manager: EventManager):
        """
        NetworkInterfaceMonitorDataProcessor 초기화

        Args:
            event_manager: 이벤트 발생을 위한 EventManager 인스턴스
        """
        self.current_flags = None
        self.current_ipv6 = None
        self.current_ipv4 = None
        super().__init__(event_manager)

    def reset_state_variables(self):
        """모든 상태 변수를 초기값으로 리셋"""
        self.current_ipv4 = "N/A"
        self.current_ipv6 = "N/A"
        self.current_flags = "N/A"

    def process_command_result(self, handler, result):
        """
        Command 실행 결과를 처리하는 메인 메서드

        Args:
            handler: Command 핸들러 인스턴스
            result: Command 실행 결과
        """
        LOGD(
            f"NetworkInterfaceMonitorDataProcessor: Processing command result from {handler.__class__.__name__}"
        )

        if result is None:
            LOGD(
                f"NetworkInterfaceMonitorDataProcessor: Result is None, skipping processing"
            )
            return

        # 핸들러 타입에 따라 적절한 처리 메서드 호출
        # isinstance 대신 __class__.__name__을 직접 비교하여 TypeError 방지
        if getattr(handler, "__class__", None):
            handler_name = handler.__class__.__name__

            if handler_name == "NetworkInterfaceCommand":
                self.process_network_interface(result)
            else:
                LOGD(
                    f"NetworkInterfaceMonitorDataProcessor: Unknown handler type: {handler_name}"
                )

    def process_network_interface(self, actual_data: Optional[Any]):
        """
        Network Interface 정보 처리

        Args:
            actual_data: Network Interface 데이터
        """
        LOGD(
            f"NetworkInterfaceMonitorDataProcessor: Processing network interface data: {actual_data}"
        )

        if isinstance(actual_data, dict):
            # 상태 캐싱
            self.current_ipv4 = actual_data.get("ipv4", "N/A")
            self.current_ipv6 = actual_data.get("ipv6", "N/A")
            self.current_flags = ", ".join(actual_data.get("flags", []))

            # Event 발생
            self.event_manager.emit_event(
                QSMonitorEventType.NETWORK_INTERFACE_UPDATED,
                {
                    "ipv4": self.current_ipv4,
                    "ipv6": self.current_ipv6,
                    "flags": self.current_flags,
                },
            )

    def get_current_states(self):
        """
        현재 상태 정보 반환

        Returns:
            dict: 현재 상태 정보 딕셔너리
        """
        return {
            "ipv4": self.current_ipv4,
            "ipv6": self.current_ipv6,
            "flags": self.current_flags,
        }

    def register_with_command_handler(self, command_handler):
        """
        CommandHandler에 자신을 등록

        Args:
            command_handler: CommandHandler 인스턴스
        """

        # NetworkInterface 커맨드 클래스 등록
        command_handler.register_class_handler(NetworkInterfaceCommand, self)

        LOGD(f"NetworkInterfaceMonitorDataProcessor: Registered with CommandHandler")

    def setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        LOGD("NetworkInterfaceMonitorDataProcessor: Setting up event handlers")
        # Network Interface는 내부 상태 변경 이벤트가 필요 없으므로 별도로 등록할 핸들러 없음
        LOGD("NetworkInterfaceMonitorDataProcessor: Event handlers setup completed")
