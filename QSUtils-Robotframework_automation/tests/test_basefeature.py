#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaseFeature 단위 테스트
"""

import os
import sys
from unittest.mock import Mock

import pytest

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 모듈 캐시를 완전히 정리
modules_to_remove = [
    mod
    for mod in sys.modules.keys()
    if mod.startswith("QSUtils.QSMonitor.features.base")
]
for mod in modules_to_remove:
    del sys.modules[mod]

from QSUtils.QSMonitor.features.base.BaseFeature import BaseFeature


class ConcreteBaseFeature(BaseFeature):
    """테스트용 구체적인 BaseFeature 구현 클래스"""

    def _create_data_processor(self, event_manager):
        """테스트용 DataProcessor 생성"""
        mock_processor = Mock()
        mock_processor.setup_event_handlers = Mock()
        mock_processor.register_with_command_handler = Mock()
        mock_processor.reset_state_variables = Mock()
        mock_processor.process_command_result = Mock()
        mock_processor.get_current_states = Mock(return_value={})
        return mock_processor

    def _create_widget(self, parent, event_manager):
        """테스트용 Widget 생성"""
        mock_widget = Mock()
        mock_widget.set_enabled_all = Mock()
        return mock_widget


class TestBaseFeature:
    """BaseFeature 클래스 테스트"""

    @pytest.fixture
    def mock_parent(self):
        """Mock parent widget"""
        return Mock()

    @pytest.fixture
    def mock_device_context(self):
        """Mock device context"""
        mock_context = Mock()
        mock_context.event_manager = Mock()
        return mock_context

    @pytest.fixture
    def mock_command_handler(self):
        """Mock command handler"""
        return Mock()

    def test_get_required_command_handlers_default(
        self, mock_parent, mock_device_context, mock_command_handler
    ):
        """BaseFeature의 get_required_command_handlers 기본 구현 테스트"""
        # Given
        concrete_feature = ConcreteBaseFeature(
            mock_parent, mock_device_context, mock_command_handler
        )

        # When
        handlers = concrete_feature.get_required_command_handlers()

        # Then
        assert handlers == []  # 기본 구현은 빈 리스트 반환

    def test_get_required_command_handlers_can_be_overridden(self):
        """하위 클래스에서 get_required_command_handlers를 오버라이드할 수 있는지 검증"""

        # Given
        class CustomFeature(ConcreteBaseFeature):
            def get_required_command_handlers(self):
                return [Mock, Mock]  # Mock handler 클래스들

        mock_parent = Mock()
        mock_device_context = Mock()
        mock_device_context.event_manager = Mock()
        mock_command_handler = Mock()

        # When
        custom_feature = CustomFeature(
            mock_parent, mock_device_context, mock_command_handler
        )
        handlers = custom_feature.get_required_command_handlers()

        # Then
        assert len(handlers) == 2
        assert Mock in handlers
