# -*- coding: utf-8 -*-
"""
NetworkMonitorFeature - 네트워크 인터페이스 모니터링 기능을 통합 관리하는 클래스
"""

from typing import List, Type

from QSUtils.QSMonitor.features.NetworkMonitor.NetworkMonitorDataProcessor import (
    NetworkMonitorDataProcessor,
)
from QSUtils.QSMonitor.features.NetworkMonitor.NetworkMonitorWidget import (
    NetworkInterfaceMonitorGroup,
)
from QSUtils.QSMonitor.features.base.BaseFeature import BaseFeature
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.command.cmd_network_interface import NetworkInterfaceCommand


class NetworkMonitorFeature(BaseFeature):
    """
    네트워크 인터페이스 모니터링 기능을 통합 관리하는 클래스

    NetworkMonitorDataProcessor는 공유하고 NetworkInterfaceMonitorGroup은 각 인스턴스마다 생성하여
    이벤트 중복 등록 문제를 방지하면서 사용 편의성을 제공합니다.
    """

    def _create_data_processor(
        self, event_manager: EventManager
    ) -> NetworkMonitorDataProcessor:
        """
        NetworkMonitorDataProcessor 인스턴스 생성

        Args:
            event_manager: EventManager 인스턴스

        Returns:
            NetworkMonitorDataProcessor: 생성된 DataProcessor 인스턴스
        """
        return NetworkMonitorDataProcessor(event_manager)

    @classmethod
    def get_required_command_handlers(cls) -> List[Type]:
        """
        이 Feature가 필요한 command handler 클래스 목록 반환

        NetworkMonitorFeature는 네트워크 인터페이스 모니터링을 위해
        다음 command handler를 필요로 합니다:
        - NetworkInterfaceCommand: 네트워크 인터페이스 정보 조회

        Returns:
            List[Type]: command handler 클래스 목록
        """
        return [NetworkInterfaceCommand]

    def _create_widget(self, parent, event_manager: EventManager):
        """
        NetworkInterfaceMonitorGroup 인스턴스 생성

        Args:
            parent: 부모 위젯
            event_manager: EventManager 인스턴스

        Returns:
            NetworkInterfaceMonitorGroup: 생성된 Widget 인스턴스
        """
        return NetworkInterfaceMonitorGroup(parent, event_manager)
