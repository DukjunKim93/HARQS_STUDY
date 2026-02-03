#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Registry 통합 테스트
전체 시스템의 Feature Registry와 DeviceCommandExecutor 연동 검증
"""

from unittest.mock import Mock

import pytest

from QSUtils.UIFramework.base.DeviceCommandExecutor import DeviceCommandExecutor
from QSUtils.command.cmd_get_preference_data import PreferenceDataCommandHandler
from QSUtils.command.cmd_network_interface import NetworkInterfaceCommand
from QSUtils.command.cmd_pp_speaker_remap import SpeakerRemapCommandHandler
from QSUtils.command.cmd_pp_surround_speaker_remap import (
    SurroundSpeakerRemapCommandHandler,
)
from QSUtils.command.cmd_pp_symphony import SymphonyStatusCommandHandler
from QSUtils.command.cmd_pp_symphony_group import SymphonyGroupCommandHandler
from QSUtils.command.cmd_pp_symphony_volume_add import SymphonyVolumeAddCommandHandler
from tests.test_feature_registry import setup_test_features, clear_test_registry


class TestFeatureRegistryIntegration:
    """Feature Registry 통합 테스트"""

    @pytest.fixture(autouse=True)
    def setup_test_features_fixture(self):
        """모든 테스트 전에 Feature 설정"""
        registry = setup_test_features()
        yield
        clear_test_registry(registry)

    @pytest.fixture
    def mock_adb_device(self):
        """Mock ADBDevice fixture"""
        return Mock()

    @pytest.fixture
    def result_callback(self):
        return Mock()

    def test_full_system_integration_registry_to_handlers(
        self, mock_adb_device, result_callback
    ):
        """전체 시스템 통합: Registry → DeviceCommandExecutor → Handlers"""
        # Given
        registry = setup_test_features()
        executor = DeviceCommandExecutor(mock_adb_device, registry, result_callback)

        # When
        handlers = executor._initialize_handlers()
        # 활성화 Feature 목록 정의
        active_features = ["DefaultMonitor", "SpeakerGrid", "NetworkMonitor"]
        registry_handlers = registry.get_command_handlers_for_features(active_features)

        # Then - 전체 파이프라인이 정상적으로 동작해야 함
        assert len(handlers) == 7
        assert len(registry_handlers) == 7

        # Registry가 반환한 클래스 타입과 실제 생성된 핸들러 타입 집합이 일치 (순서는 무관)
        registry_handler_set = set(registry_handlers)
        handler_instance_set = {type(h) for h in handlers}
        assert registry_handler_set == handler_instance_set

        # 여러 Executor 인스턴스 간 일관성 검증
        executor2 = DeviceCommandExecutor(mock_adb_device, registry, result_callback)
        handlers2 = executor2._initialize_handlers()
        # 활성화 Feature 목록은 동일한 결과
        active_features2 = ["DefaultMonitor", "SpeakerGrid", "NetworkMonitor"]

        # 모든 인스턴스에서 동일한 상태 유지
        assert active_features == active_features2
        assert len(handlers) == len(handlers2) == 7

        # 핸들러 타입 집합이 동일한지 확인 (순서는 무관)
        handler_types2 = {type(h) for h in handlers2}
        assert handler_instance_set == handler_types2

        # Cleanup
        clear_test_registry(registry)

    def test_feature_to_handler_mapping_completeness(
        self, mock_adb_device, result_callback
    ):
        """Feature에서 Handler로의 매핑 완전성 검증"""
        # Given
        registry = setup_test_features()
        executor = DeviceCommandExecutor(mock_adb_device, registry, result_callback)
        # 활성화 Feature 목록 정의
        active_features = ["DefaultMonitor", "SpeakerGrid", "NetworkMonitor"]

        # When
        handlers = executor._initialize_handlers()
        feature_handlers = registry.get_command_handlers_for_features(active_features)

        # Then - 모든 Feature가 필요한 핸들러를 제공해야 함
        expected_handler_mapping = {
            "DefaultMonitor": [
                PreferenceDataCommandHandler,
                SymphonyStatusCommandHandler,
                SymphonyGroupCommandHandler,
                SymphonyVolumeAddCommandHandler,
            ],
            "NetworkMonitor": [NetworkInterfaceCommand],
            "SpeakerGrid": [
                SpeakerRemapCommandHandler,
                SurroundSpeakerRemapCommandHandler,
            ],
        }

        # 각 Feature별 핸들러 수 검증
        total_expected_handlers = 0
        for feature_name, expected_handlers in expected_handler_mapping.items():
            feature_info = registered_features = registry.get_registered_features()
            if feature_name in registered_features:
                total_expected_handlers += len(expected_handlers)

        assert len(feature_handlers) == 7  # 총 7개 핸들러
        assert len(handlers) == 7

        # Cleanup
        clear_test_registry(registry)

    def test_registry_error_propagation_to_executor(
        self, mock_adb_device, result_callback
    ):
        """Registry 에러가 DeviceCommandExecutor에 적절히 전파되는지 검증"""
        # Given - Mock registry를 사용하여 에러 상황 시뮬레이션
        mock_registry = Mock()
        mock_registry.get_all_command_handlers.side_effect = Exception("Registry error")

        # When & Then - Registry 에러 시 예외 발생해야 함 (생성자에서 발생)
        with pytest.raises(Exception, match="Registry error"):
            DeviceCommandExecutor(mock_adb_device, mock_registry, result_callback)

    def test_system_performance_under_load(self, mock_adb_device, result_callback):
        """시스템 부하 하에서의 성능 테스트"""
        import time

        # Given
        registry = setup_test_features()
        executor = DeviceCommandExecutor(mock_adb_device, registry, result_callback)

        # When - 여러 번 초기화 실행
        start_time = time.time()
        for _ in range(10):
            handlers = executor._initialize_handlers()
            assert len(handlers) == 7
        end_time = time.time()

        # Then - 성능이 기준치 내에 있어야 함
        total_time = end_time - start_time
        avg_time = total_time / 10
        assert avg_time < 0.05  # 평균 50ms 내에 완료되어야 함

        # Cleanup
        clear_test_registry(registry)
