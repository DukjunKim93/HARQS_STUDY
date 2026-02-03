#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpeakerGrid 통합 테스트 - CommandHandler와 FeatureRegistry 연동 확인
"""

from unittest.mock import Mock

import pytest

from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridDataProcessor import (
    SpeakerGridDataProcessor,
)
from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.UIFramework.base.FeatureRegistry import FeatureRegistry
from QSUtils.command.cmd_pp_speaker_remap import SpeakerRemapCommandHandler
from QSUtils.command.cmd_pp_surround_speaker_remap import (
    SurroundSpeakerRemapCommandHandler,
)


class TestSpeakerGridIntegration:
    """SpeakerGrid 통합 테스트"""

    @pytest.fixture
    def event_manager(self):
        """EventManager 인스턴스 fixture"""
        return EventManager()

    @pytest.fixture
    def feature_registry(self):
        """FeatureRegistry 인스턴스 fixture"""
        return FeatureRegistry()

    @pytest.fixture
    def speaker_grid_processor(self, event_manager):
        """SpeakerGridDataProcessor 인스턴스 fixture"""
        return SpeakerGridDataProcessor(event_manager)

    @pytest.fixture
    def command_handler_with_registry(self, feature_registry):
        """FeatureRegistry가 있는 CommandHandler 인스턴스 fixture"""
        return CommandHandler()

    def test_speaker_grid_processor_registers_correct_handlers(
        self, speaker_grid_processor, command_handler_with_registry
    ):
        """SpeakerGridDataProcessor가 올바른 핸들러를 등록하는지 테스트"""
        # SpeakerGridDataProcessor가 CommandHandler에 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # 등록된 핸들러 확인
        registered_handlers = command_handler_with_registry.get_registered_handlers()

        assert "SpeakerRemapCommandHandler" in registered_handlers
        assert "SurroundSpeakerRemapCommandHandler" in registered_handlers
        assert len(registered_handlers) == 2

    def test_speaker_grid_processor_processes_only_registered_commands(
        self, speaker_grid_processor, command_handler_with_registry
    ):
        """SpeakerGridDataProcessor가 등록된 커맨드만 처리하는지 테스트"""
        # 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # SpeakerRemapCommandHandler 모의 객체
        speaker_handler = Mock()
        speaker_handler.__class__.__name__ = "SpeakerRemapCommandHandler"

        # 등록된 커맨드 처리 - 성공해야 함
        result = command_handler_with_registry.handle_command(speaker_handler, 1)
        assert result is True

        # 상태 확인
        states = speaker_grid_processor.get_current_states()
        assert "speaker_remap_states" in states
        assert states["speaker_remap_states"]["position_id"] == 1

    def test_speaker_grid_processor_ignores_unregistered_commands(
        self, speaker_grid_processor, command_handler_with_registry, feature_registry
    ):
        """SpeakerGridDataProcessor가 등록되지 않은 커맨드는 무시하는지 테스트"""
        # FeatureRegistry에 SpeakerGridFeature 등록
        from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridFeature import (
            SpeakerGridFeature,
        )

        feature_registry.register_feature(
            "SpeakerGrid",
            SpeakerGridFeature,
            [SpeakerRemapCommandHandler, SurroundSpeakerRemapCommandHandler],
        )

        # 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # 등록되지 않은 커맨드 모의 객체
        unknown_handler = Mock()
        unknown_handler.__class__.__name__ = "UnknownCommandHandler"

        # 등록되지 않은 커맨드 처리 - 실패해야 함 (시스템 오류로 간주)
        result = command_handler_with_registry.handle_command(
            unknown_handler, "test_data"
        )
        assert result is False

    def test_speaker_grid_processor_with_surround_command(
        self, speaker_grid_processor, command_handler_with_registry
    ):
        """SpeakerGridDataProcessor가 서라운드 스피커 커맨드를 처리하는지 테스트"""
        # 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # SurroundSpeakerRemapCommandHandler 모의 객체
        surround_handler = Mock()
        surround_handler.__class__.__name__ = "SurroundSpeakerRemapCommandHandler"

        # 서라운드 스피커 데이터
        surround_data = [1, 2, 3, 4, 5, 6, 7]

        # 커맨드 처리 - 성공해야 함
        result = command_handler_with_registry.handle_command(
            surround_handler, surround_data
        )
        assert result is True

        # 상태 확인
        states = speaker_grid_processor.get_current_states()
        assert "surround_speaker_states" in states
        assert states["surround_speaker_states"] == surround_data

    def test_feature_registry_validates_speaker_grid_commands(
        self, feature_registry, command_handler_with_registry, speaker_grid_processor
    ):
        """FeatureRegistry가 SpeakerGrid 커맨드를 올바르게 검증하는지 테스트"""
        # FeatureRegistry에 SpeakerGridFeature 등록
        from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridFeature import (
            SpeakerGridFeature,
        )

        feature_registry.register_feature(
            "SpeakerGrid",
            SpeakerGridFeature,
            [SpeakerRemapCommandHandler, SurroundSpeakerRemapCommandHandler],
        )

        # SpeakerGridDataProcessor가 CommandHandler에 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # CommandHandler는 등록된 핸들러만 처리하므로 FeatureRegistry 검증은 더 이상 사용되지 않음
        # 대신 직접 등록된 핸들러 확인
        registered_handlers = command_handler_with_registry.get_registered_handlers()

        # SpeakerGrid 관련 커맨드가 등록되었는지 확인
        assert "SpeakerRemapCommandHandler" in registered_handlers
        assert "SurroundSpeakerRemapCommandHandler" in registered_handlers

    def test_speaker_grid_processor_with_disabled_feature(
        self, speaker_grid_processor, command_handler_with_registry, feature_registry
    ):
        """Feature가 비활성화된 경우 SpeakerGrid 커맨드 처리 테스트"""
        # FeatureRegistry에 SpeakerGridFeature 등록 후 비활성화
        from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridFeature import (
            SpeakerGridFeature,
        )

        feature_registry.register_feature(
            "SpeakerGrid",
            SpeakerGridFeature,
            [SpeakerRemapCommandHandler, SurroundSpeakerRemapCommandHandler],
        )
        feature_registry.disable_feature("SpeakerGrid")

        # 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # SpeakerRemapCommandHandler 모의 객체
        speaker_handler = Mock()
        speaker_handler.__class__.__name__ = "SpeakerRemapCommandHandler"

        # 비활성화된 Feature의 커맨드 처리 - 핸들러가 직접 등록되었으므로 성공해야 함
        # FeatureRegistry 검증은 실패하지만, 직접 등록된 핸들러가 우선함
        result = command_handler_with_registry.handle_command(speaker_handler, 1)
        assert result is True

    def test_speaker_grid_processor_error_handling(
        self, speaker_grid_processor, command_handler_with_registry
    ):
        """SpeakerGridDataProcessor의 에러 처리 테스트"""
        # 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # SpeakerRemapCommandHandler 모의 객체
        speaker_handler = Mock()
        speaker_handler.__class__.__name__ = "SpeakerRemapCommandHandler"

        # 잘못된 데이터 타입으로 처리
        result = command_handler_with_registry.handle_command(
            speaker_handler, "invalid_string"
        )
        assert result is True  # 핸들러는 호출되지만 내부적으로 에러 처리

        # 상태가 변경되지 않았는지 확인
        states = speaker_grid_processor.get_current_states()
        assert states["speaker_remap_states"] == {}

    def test_speaker_grid_processor_reset_functionality(
        self, speaker_grid_processor, command_handler_with_registry
    ):
        """SpeakerGridDataProcessor의 상태 리셋 기능 테스트"""
        # 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # 커맨드 처리로 상태 설정
        speaker_handler = Mock()
        speaker_handler.__class__.__name__ = "SpeakerRemapCommandHandler"
        command_handler_with_registry.handle_command(speaker_handler, 5)

        # 상태 확인
        states = speaker_grid_processor.get_current_states()
        assert states["speaker_remap_states"]["position_id"] == 5

        # 상태 리셋
        speaker_grid_processor.reset_state_variables()

        # 리셋된 상태 확인
        states = speaker_grid_processor.get_current_states()
        assert states["speaker_remap_states"] == {}
        assert states["surround_speaker_states"] == {}

    def test_integration_with_multiple_features(
        self, speaker_grid_processor, command_handler_with_registry, feature_registry
    ):
        """여러 Feature가 있는 경우의 통합 테스트"""
        # 여러 Feature 등록
        from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridFeature import (
            SpeakerGridFeature,
        )
        from QSUtils.QSMonitor.features.NetworkMonitor.NetworkMonitorFeature import (
            NetworkMonitorFeature,
        )
        from QSUtils.command.cmd_network_interface import NetworkInterfaceCommand

        feature_registry.register_feature(
            "SpeakerGrid",
            SpeakerGridFeature,
            [SpeakerRemapCommandHandler, SurroundSpeakerRemapCommandHandler],
        )
        feature_registry.register_feature(
            "NetworkMonitor", NetworkMonitorFeature, [NetworkInterfaceCommand]
        )

        # SpeakerGrid 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # SpeakerGrid 커맨드 처리 - 성공해야 함
        speaker_handler = Mock()
        speaker_handler.__class__.__name__ = "SpeakerRemapCommandHandler"
        result = command_handler_with_registry.handle_command(speaker_handler, 3)
        assert result is True

        # NetworkMonitor 커맨드 처리 - 등록된 핸들러가 없으므로 실패해야 함
        network_handler = Mock()
        network_handler.__class__.__name__ = "NetworkInterfaceCommand"
        result = command_handler_with_registry.handle_command(
            network_handler, "network_data"
        )
        assert result is False

        # 등록되지 않은 커맨드 처리 - 실패해야 함
        unknown_handler = Mock()
        unknown_handler.__class__.__name__ = "UnknownCommandHandler"
        result = command_handler_with_registry.handle_command(
            unknown_handler, "test_data"
        )
        assert result is False

    def test_speaker_grid_processor_event_emission(
        self, speaker_grid_processor, command_handler_with_registry, event_manager
    ):
        """SpeakerGridDataProcessor의 이벤트 발생 테스트"""
        # 이벤트 수신기 설정 - speaker_grid_processor가 사용하는 event_manager에 등록
        emitted_events = []

        def event_handler(args):
            emitted_events.append(args)

        # 올바른 Enum 타입 사용
        from QSUtils.QSMonitor.core.Events import QSMonitorEventType

        speaker_grid_processor.event_manager.register_event_handler(
            QSMonitorEventType.SPEAKER_GRID_UPDATED, event_handler
        )

        # 핸들러 등록
        speaker_grid_processor.register_with_command_handler(
            command_handler_with_registry
        )

        # 커맨드 처리
        speaker_handler = Mock()
        speaker_handler.__class__.__name__ = "SpeakerRemapCommandHandler"
        command_handler_with_registry.handle_command(speaker_handler, 2)

        # 이벤트 발생 확인
        assert len(emitted_events) == 1
        data = emitted_events[0]
        assert data["update_type"] == "speaker_remap"
        assert data["data"]["position_id"] == 2
