#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeviceCommandExecutor와 FeatureRegistry 통합 테스트
"""

from unittest.mock import Mock

import pytest

from QSUtils.UIFramework.base.DeviceCommandExecutor import DeviceCommandExecutor
from QSUtils.UIFramework.base.FeatureRegistry import FeatureRegistry
from tests.test_feature_registry import setup_test_features, clear_test_registry


class TestDeviceCommandExecutorIntegration:
    """DeviceCommandExecutor와 FeatureRegistry 통합 테스트"""

    @pytest.fixture
    def mock_adb_device(self):
        """Mock ADBDevice fixture"""
        return Mock()

    @pytest.fixture
    def result_callback(self):
        """Dummy result callback fixture"""
        return Mock()

    @pytest.fixture
    def registry(self):
        """FeatureRegistry fixture"""
        registry = FeatureRegistry()
        registry.clear_registry()
        return registry

    def test_feature_registry_integration_with_command_handlers(
        self, registry, mock_adb_device, result_callback
    ):
        """FeatureRegistry와 Command Handler 연동 테스트"""
        # Given: FeatureRegistry에 Feature 등록
        from QSUtils.command.cmd_get_preference_data import (
            PreferenceDataCommandHandler,
        )
        from QSUtils.command.cmd_network_interface import (
            NetworkInterfaceCommand,
        )

        registry.register_feature(
            "DefaultMonitor",
            Mock,
            [PreferenceDataCommandHandler, NetworkInterfaceCommand],
        )

        # When: DeviceCommandExecutor 생성
        executor = DeviceCommandExecutor(mock_adb_device, registry, result_callback)

        # Then: FeatureRegistry를 통해 생성된 handlers 확인
        handlers = executor._initialize_handlers()
        assert len(handlers) == 2
        # 순서는 FeatureRegistry 구현에 따라 달라질 수 있음
        handler_types = [type(handler) for handler in handlers]
        assert PreferenceDataCommandHandler in handler_types
        assert NetworkInterfaceCommand in handler_types

    def test_feature_registry_with_multiple_features(
        self, registry, mock_adb_device, result_callback
    ):
        """여러 Feature 등록 시 중복 제거 테스트"""
        # Given: 중복된 Handler를 가진 여러 Feature 등록
        from QSUtils.command.cmd_get_preference_data import (
            PreferenceDataCommandHandler,
        )
        from QSUtils.command.cmd_network_interface import (
            NetworkInterfaceCommand,
        )

        registry.register_feature(
            "DefaultMonitor",
            Mock,
            [PreferenceDataCommandHandler, NetworkInterfaceCommand],
        )
        registry.register_feature(
            "NetworkMonitor", Mock, [PreferenceDataCommandHandler]  # 중복
        )

        # When: DeviceCommandExecutor 생성
        executor = DeviceCommandExecutor(mock_adb_device, registry, result_callback)

        # Then: 중복 제거된 handlers 반환
        handlers = executor._initialize_handlers()
        assert len(handlers) == 2

        handler_types = [type(handler) for handler in handlers]
        assert PreferenceDataCommandHandler in handler_types
        assert NetworkInterfaceCommand in handler_types

    def test_feature_registry_with_real_features(
        self, mock_adb_device, result_callback
    ):
        """실제 Feature를 사용한 통합 테스트"""
        # Given: 테스트 Feature 설정
        registry = setup_test_features()

        # When: DeviceCommandExecutor 생성
        executor = DeviceCommandExecutor(mock_adb_device, registry, result_callback)

        # Then: 실제 Feature들의 handlers가 반환됨
        handlers = executor._initialize_handlers()
        assert len(handlers) == 7  # 3개 Feature의 총 7개 핸들러

        # Then: 각 Feature의 핸들러가 포함되어 있는지 확인
        from QSUtils.command.cmd_get_preference_data import PreferenceDataCommandHandler
        from QSUtils.command.cmd_network_interface import NetworkInterfaceCommand
        from QSUtils.command.cmd_pp_speaker_remap import SpeakerRemapCommandHandler
        from QSUtils.command.cmd_pp_surround_speaker_remap import (
            SurroundSpeakerRemapCommandHandler,
        )
        from QSUtils.command.cmd_pp_symphony import SymphonyStatusCommandHandler
        from QSUtils.command.cmd_pp_symphony_group import SymphonyGroupCommandHandler
        from QSUtils.command.cmd_pp_symphony_volume_add import (
            SymphonyVolumeAddCommandHandler,
        )

        handler_types = [type(handler) for handler in handlers]
        expected_types = [
            SymphonyStatusCommandHandler,
            SymphonyGroupCommandHandler,
            SpeakerRemapCommandHandler,
            SurroundSpeakerRemapCommandHandler,
            SymphonyVolumeAddCommandHandler,
            NetworkInterfaceCommand,
            PreferenceDataCommandHandler,
        ]

        for expected_type in expected_types:
            assert expected_type in handler_types

        # Cleanup
        clear_test_registry(registry)
