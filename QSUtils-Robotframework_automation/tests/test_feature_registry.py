#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FeatureRegistry 단위 테스트
"""

from unittest.mock import Mock

import pytest

from QSUtils.QSMonitor.features.DefaultMonitor.DefaultMonitorFeature import (
    DefaultMonitorFeature,
)
from QSUtils.QSMonitor.features.NetworkMonitor.NetworkMonitorFeature import (
    NetworkMonitorFeature,
)
from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridFeature import SpeakerGridFeature
from QSUtils.UIFramework.base.FeatureRegistry import FeatureRegistry


class TestFeatureRegistry:
    """FeatureRegistry 클래스 테스트"""

    # 테스트 상수 정의
    EXPECTED_HANDLER_COUNT = 3
    SINGLE_HANDLER_COUNT = 1
    EMPTY_HANDLER_COUNT = 0
    TWO_HANDLER_COUNT = 2

    # 테스트용 상수
    TEST_FEATURE_NAME = "TestFeature"
    TEST_FEATURE_NAME_1 = "TestFeature1"
    TEST_FEATURE_NAME_2 = "TestFeature2"
    NONEXISTENT_FEATURE = "NonExistentFeature"
    MOCK_FEATURE_CLASS_NAME = "MockFeatureClass"

    @pytest.fixture
    def registry(self):
        """FeatureRegistry 인스턴스 fixture"""
        return FeatureRegistry()

    @pytest.fixture
    def mock_feature_class(self):
        """Mock feature 클래스 fixture"""
        mock_class = Mock()
        mock_class.__name__ = TestFeatureRegistry.MOCK_FEATURE_CLASS_NAME
        return mock_class

    @pytest.fixture
    def mock_handlers(self):
        """Mock command handler 리스트 fixture"""
        handler1 = Mock()
        handler1.__name__ = "MockHandler1"
        handler2 = Mock()
        handler2.__name__ = "MockHandler2"
        handler3 = Mock()
        handler3.__name__ = "MockHandler3"
        return [handler1, handler2, handler3]

    def test_feature_registry_initialization(self, registry):
        """FeatureRegistry 초기화 테스트"""
        assert registry is not None
        assert len(registry._registered_features) == self.EMPTY_HANDLER_COUNT
        assert len(registry._feature_instances) == self.EMPTY_HANDLER_COUNT

    def test_register_feature(self, registry, mock_feature_class, mock_handlers):
        """Feature 등록 테스트"""
        command_handlers = [mock_handlers[0], mock_handlers[1]]

        registry.register_feature(
            self.TEST_FEATURE_NAME, mock_feature_class, command_handlers
        )

        registered_features = registry.get_registered_features()
        assert self.TEST_FEATURE_NAME in registered_features
        assert (
            registered_features[self.TEST_FEATURE_NAME]["feature_class"]
            == mock_feature_class.__name__
        )
        assert (
            registered_features[self.TEST_FEATURE_NAME]["handler_count"]
            == self.TWO_HANDLER_COUNT
        )
        assert registered_features[self.TEST_FEATURE_NAME]["enabled"] == True

    def test_register_feature_without_handlers(self, registry, mock_feature_class):
        """Command handler 없이 Feature 등록 테스트"""
        registry.register_feature(self.TEST_FEATURE_NAME, mock_feature_class)

        registered_features = registry.get_registered_features()
        assert self.TEST_FEATURE_NAME in registered_features
        assert (
            registered_features[self.TEST_FEATURE_NAME]["handler_count"]
            == self.EMPTY_HANDLER_COUNT
        )

    def test_enable_feature(self, registry, mock_feature_class, mock_handlers):
        """Feature 활성화 테스트"""
        registry.register_feature(
            self.TEST_FEATURE_NAME, mock_feature_class, [mock_handlers[0]]
        )
        registry.disable_feature(self.TEST_FEATURE_NAME)  # 먼저 비활성화

        registry.enable_feature(self.TEST_FEATURE_NAME)

        registered_features = registry.get_registered_features()
        assert registered_features[self.TEST_FEATURE_NAME]["enabled"] == True

    def test_disable_feature(self, registry, mock_feature_class, mock_handlers):
        """Feature 비활성화 테스트"""
        registry.register_feature(
            self.TEST_FEATURE_NAME, mock_feature_class, [mock_handlers[0]]
        )

        registry.disable_feature(self.TEST_FEATURE_NAME)

        registered_features = registry.get_registered_features()
        assert registered_features[self.TEST_FEATURE_NAME]["enabled"] == False

    def test_get_command_handlers_for_features(
        self, registry, mock_feature_class, mock_handlers
    ):
        """활성화된 feature들의 command handlers 반환 테스트"""
        handler1 = mock_handlers[0]
        handler2 = mock_handlers[1]
        handler3 = mock_handlers[2]

        registry.register_feature(
            self.TEST_FEATURE_NAME_1, mock_feature_class, [handler1, handler2]
        )
        registry.register_feature(
            self.TEST_FEATURE_NAME_2, mock_feature_class, [handler2, handler3]
        )

        handlers = registry.get_command_handlers_for_features(
            [self.TEST_FEATURE_NAME_1, self.TEST_FEATURE_NAME_2]
        )

        # 중복 제거되어 3개의 handler가 반환되어야 함
        assert len(handlers) == self.EXPECTED_HANDLER_COUNT
        assert handler1 in handlers
        assert handler2 in handlers
        assert handler3 in handlers

    def test_get_command_handlers_for_features_with_disabled_feature(
        self, registry, mock_feature_class, mock_handlers
    ):
        """비활성화된 feature는 command handlers에 포함되지 않음 테스트"""
        handler1 = mock_handlers[0]
        handler2 = mock_handlers[1]

        registry.register_feature(
            self.TEST_FEATURE_NAME_1, mock_feature_class, [handler1]
        )
        registry.register_feature(
            self.TEST_FEATURE_NAME_2, mock_feature_class, [handler2]
        )
        registry.disable_feature(self.TEST_FEATURE_NAME_2)  # feature2 비활성화

        handlers = registry.get_command_handlers_for_features(
            [self.TEST_FEATURE_NAME_1, self.TEST_FEATURE_NAME_2]
        )

        assert len(handlers) == self.SINGLE_HANDLER_COUNT
        assert handler1 in handlers
        assert handler2 not in handlers

    def test_get_all_command_handlers(
        self, registry, mock_feature_class, mock_handlers
    ):
        """등록된 모든 활성화된 feature의 command handlers 반환 테스트"""
        handler1 = mock_handlers[0]
        handler2 = mock_handlers[1]

        registry.register_feature(
            self.TEST_FEATURE_NAME_1, mock_feature_class, [handler1]
        )
        registry.register_feature(
            self.TEST_FEATURE_NAME_2, mock_feature_class, [handler2]
        )
        registry.disable_feature(self.TEST_FEATURE_NAME_2)  # feature2 비활성화

        handlers = registry.get_all_command_handlers()

        assert len(handlers) == self.SINGLE_HANDLER_COUNT
        assert handler1 in handlers
        assert handler2 not in handlers

    def test_clear_registry(self, registry, mock_feature_class, mock_handlers):
        """레지스트리 초기화 테스트"""
        registry.register_feature(
            self.TEST_FEATURE_NAME, mock_feature_class, [mock_handlers[0]]
        )

        registry.clear_registry()

        assert len(registry._registered_features) == self.EMPTY_HANDLER_COUNT
        assert len(registry._feature_instances) == self.EMPTY_HANDLER_COUNT

    def test_get_registered_features(self, registry, mock_feature_class, mock_handlers):
        """등록된 모든 feature 정보 반환 테스트"""
        handler1 = mock_handlers[0]
        handler2 = mock_handlers[1]
        registry.register_feature(
            self.TEST_FEATURE_NAME, mock_feature_class, [handler1, handler2]
        )

        registered_features = registry.get_registered_features()

        assert self.TEST_FEATURE_NAME in registered_features
        assert registered_features[self.TEST_FEATURE_NAME]["enabled"] == True
        assert (
            registered_features[self.TEST_FEATURE_NAME]["handler_count"]
            == self.TWO_HANDLER_COUNT
        )
        assert (
            registered_features[self.TEST_FEATURE_NAME]["feature_class"]
            == mock_feature_class.__name__
        )

    def test_register_feature_update_existing(
        self, registry, mock_feature_class, mock_handlers
    ):
        """이미 등록된 feature 업데이트 테스트"""
        # 처음 등록
        registry.register_feature(
            self.TEST_FEATURE_NAME, mock_feature_class, [mock_handlers[0]]
        )

        # 업데이트
        registry.register_feature(
            self.TEST_FEATURE_NAME,
            mock_feature_class,
            [mock_handlers[1], mock_handlers[2]],
        )

        registered_features = registry.get_registered_features()
        assert (
            registered_features[self.TEST_FEATURE_NAME]["handler_count"]
            == self.TWO_HANDLER_COUNT
        )

    def test_get_command_handlers_for_nonexistent_feature(self, registry):
        """존재하지 않는 feature의 handlers 요청 테스트"""
        handlers = registry.get_command_handlers_for_features(
            [self.NONEXISTENT_FEATURE]
        )

        assert len(handlers) == self.EMPTY_HANDLER_COUNT

    def test_enable_disable_nonexistent_feature(self, registry):
        """존재하지 않는 feature 활성화/비활성화 테스트"""
        # 에러가 발생하지 않아야 함
        registry.enable_feature(self.NONEXISTENT_FEATURE)
        registry.disable_feature(self.NONEXISTENT_FEATURE)

        # 레지스트리는 비어있어야 함
        assert len(registry._registered_features) == self.EMPTY_HANDLER_COUNT


# Test helper functions for integration tests
def setup_test_features():
    """
    테스트를 위해 FeatureRegistry에 기본 Feature들을 등록하는 함수

    등록되는 Feature들:
    - DefaultMonitor: 4개 핸들러
    - NetworkMonitor: 1개 핸들러
    - SpeakerGrid: 2개 핸들러
    총 7개 핸들러
    """
    registry = FeatureRegistry()
    registry.clear_registry()

    # DefaultMonitorFeature 등록 (4개 핸들러)
    registry.register_feature(
        "DefaultMonitor",
        DefaultMonitorFeature,
        DefaultMonitorFeature.get_required_command_handlers(),
    )

    # NetworkMonitorFeature 등록 (1개 핸들러)
    registry.register_feature(
        "NetworkMonitor",
        NetworkMonitorFeature,
        NetworkMonitorFeature.get_required_command_handlers(),
    )

    # SpeakerGridFeature 등록 (2개 핸들러)
    registry.register_feature(
        "SpeakerGrid",
        SpeakerGridFeature,
        SpeakerGridFeature.get_required_command_handlers(),
    )

    return registry


def clear_test_registry(registry):
    """
    테스트 후 FeatureRegistry를 정리하는 함수
    """
    registry.clear_registry()
