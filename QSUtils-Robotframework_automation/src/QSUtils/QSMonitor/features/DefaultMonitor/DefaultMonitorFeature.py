# -*- coding: utf-8 -*-
"""
DefaultMonitorFeature - Q-Symphony, ACM, Multiroom 모니터링 기능을 통합 관리하는 클래스
"""

from typing import List, Type

from QSUtils.QSMonitor.features.DefaultMonitor.DefaultMonitorDataProcessor import (
    DefaultMonitorDataProcessor,
)
from QSUtils.QSMonitor.features.DefaultMonitor.DefaultMonitorWidget import (
    DefaultMonitorWidget,
)
from QSUtils.QSMonitor.features.base.BaseFeature import BaseFeature
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.command.cmd_get_preference_data import (
    PreferenceDataCommandHandler,
)
from QSUtils.command.cmd_pp_symphony import SymphonyStatusCommandHandler
from QSUtils.command.cmd_pp_symphony_group import SymphonyGroupCommandHandler
from QSUtils.command.cmd_pp_symphony_volume_add import (
    SymphonyVolumeAddCommandHandler,
)


class DefaultMonitorFeature(BaseFeature):
    """
    Q-Symphony, ACM, Multiroom 모니터링 기능을 통합 관리하는 클래스

    DefaultMonitorDataProcessor는 공유하고 DefaultMonitorWidget은 각 인스턴스마다 생성하여
    이벤트 중복 등록 문제를 방지하면서 사용 편의성을 제공합니다.
    """

    def _create_data_processor(
        self, event_manager: EventManager
    ) -> DefaultMonitorDataProcessor:
        """
        DefaultMonitorDataProcessor 인스턴스 생성

        Args:
            event_manager: EventManager 인스턴스

        Returns:
            DefaultMonitorDataProcessor: 생성된 DataProcessor 인스턴스
        """
        return DefaultMonitorDataProcessor(event_manager)

    def _create_widget(self, parent, event_manager: EventManager):
        """
        DefaultMonitorWidget 인스턴스 생성

        Args:
            parent: 부모 위젯
            event_manager: EventManager 인스턴스

        Returns:
            DefaultMonitorWidget: 생성된 Widget 인스턴스
        """
        return DefaultMonitorWidget(parent, event_manager)

    @classmethod
    def get_required_command_handlers(cls) -> List[Type]:
        """
        이 Feature가 필요한 command handler 클래스 목록 반환

        DefaultMonitorFeature는 Q-Symphony, ACM, Multiroom 모니터링을 위해
        다음 command handler들을 필요로 합니다:
        - SymphonyStatusCommandHandler: Q-Symphony 상태 모니터링
        - SymphonyGroupCommandHandler: Q-Symphony 그룹 정보 조회
        - SymphonyVolumeAddCommandHandler: Q-Symphony 볼륨 추가 정보
        - PreferenceDataCommandHandler: 기본 설정 데이터 조회

        Returns:
            List[Type]: command handler 클래스 목록
        """
        return [
            SymphonyStatusCommandHandler,
            SymphonyGroupCommandHandler,
            SymphonyVolumeAddCommandHandler,
            PreferenceDataCommandHandler,
        ]

    def is_symphony_success(self):
        """
        Q-Symphony 성공 상태 확인 (DefaultMonitorDataProcessor 위임)

        Returns:
            bool: Q-Symphony 성공 상태
        """
        return self.data_processor.is_symphony_success()
