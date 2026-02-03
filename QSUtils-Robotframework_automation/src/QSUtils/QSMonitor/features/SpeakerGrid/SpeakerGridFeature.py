# -*- coding: utf-8 -*-
"""
SpeakerGridFeature - 스피커 그리드 모니터링 기능을 통합 관리하는 클래스
"""

from typing import List, Type

from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridDataProcessor import (
    SpeakerGridDataProcessor,
)
from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridWIdget import SpeakerGridGroup
from QSUtils.QSMonitor.features.base.BaseFeature import BaseFeature
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.command.cmd_pp_speaker_remap import SpeakerRemapCommandHandler
from QSUtils.command.cmd_pp_surround_speaker_remap import (
    SurroundSpeakerRemapCommandHandler,
)


class SpeakerGridFeature(BaseFeature):
    """
    스피커 그리드 모니터링 기능을 통합 관리하는 클래스

    SpeakerGridDataProcessor는 공유하고 SpeakerGridGroup은 각 인스턴스마다 생성하여
    이벤트 중복 등록 문제를 방지하면서 사용 편의성을 제공합니다.
    """

    def _create_data_processor(
        self, event_manager: EventManager
    ) -> SpeakerGridDataProcessor:
        """
        SpeakerGridDataProcessor 인스턴스 생성

        Args:
            event_manager: EventManager 인스턴스

        Returns:
            SpeakerGridDataProcessor: 생성된 DataProcessor 인스턴스
        """
        return SpeakerGridDataProcessor(event_manager)

    @classmethod
    def get_required_command_handlers(cls) -> List[Type]:
        """
        이 Feature가 필요한 command handler 클래스 목록 반환

        SpeakerGridFeature는 스피커 그리드 모니터링을 위해
        다음 command handler들을 필요로 합니다:
        - SpeakerRemapCommandHandler: 스피커 리매핑 정보 조회
        - SurroundSpeakerRemapCommandHandler: 서라운드 스피커 리매핑 정보 조회

        Returns:
            List[Type]: command handler 클래스 목록
        """
        return [SpeakerRemapCommandHandler, SurroundSpeakerRemapCommandHandler]

    def _create_widget(self, parent, event_manager: EventManager):
        """
        SpeakerGridGroup 인스턴스 생성

        Args:
            parent: 부모 위젯
            event_manager: EventManager 인스턴스

        Returns:
            SpeakerGridGroup: 생성된 Widget 인스턴스
        """
        return SpeakerGridGroup(parent, event_manager)
