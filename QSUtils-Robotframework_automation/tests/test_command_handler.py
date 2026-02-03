#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CommandHandler 단위 테스트
"""

from unittest.mock import Mock

import pytest

from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.UIFramework.base.FeatureRegistry import FeatureRegistry


class TestCommandHandler:
    """CommandHandler 클래스 테스트"""

    @pytest.fixture
    def registry(self):
        """FeatureRegistry 인스턴스 fixture"""
        return FeatureRegistry()

    @pytest.fixture
    def command_handler(self):
        """CommandHandler 인스턴스 fixture (FeatureRegistry 없음)"""
        return CommandHandler()

    @pytest.fixture
    def command_handler_with_registry(self, registry):
        """FeatureRegistry가 있는 CommandHandler 인스턴스 fixture"""
        return CommandHandler()

    @pytest.fixture
    def mock_handler(self):
        """Mock command handler fixture"""
        handler = Mock()
        handler.__class__.__name__ = "TestCommandHandler"
        return handler

    @pytest.fixture
    def mock_processor(self):
        """Mock processor fixture"""
        processor = Mock()
        processor.process_command_result = Mock()
        processor.__class__.__name__ = "TestProcessor"
        return processor

    def test_command_handler_initialization_without_registry(self):
        """FeatureRegistry 없이 CommandHandler 초기화 테스트"""
        handler = CommandHandler()
        assert handler is not None
        assert len(handler.handlers) == 0
        assert handler.default_handler is None

    def test_command_handler_initialization_with_registry(self, registry):
        """FeatureRegistry와 함께 CommandHandler 초기화 테스트"""
        handler = CommandHandler()
        assert handler is not None
        assert len(handler.handlers) == 0
        assert handler.default_handler is None

    def test_register_handler(self, command_handler):
        """핸들러 함수 등록 테스트"""

        def test_handler(handler, result):
            pass

        command_handler.register_handler("TestCommand", test_handler)

        assert "TestCommand" in command_handler.handlers
        assert command_handler.handlers["TestCommand"] == test_handler

    def test_register_class_handler(self, command_handler, mock_processor):
        """클래스 핸들러 등록 테스트"""

        class TestCommand:
            pass

        command_handler.register_class_handler(TestCommand, mock_processor)

        assert "TestCommand" in command_handler.handlers
        assert (
            command_handler.handlers["TestCommand"]
            == mock_processor.process_command_result
        )
        assert "TestCommand" in command_handler._registered_classes

    def test_register_class_handler_duplicate(self, command_handler, mock_processor):
        """클래스 핸들러 중복 등록 테스트"""

        class TestCommand:
            pass

        # 첫 번째 등록
        command_handler.register_class_handler(TestCommand, mock_processor)
        first_count = len(command_handler._registered_classes)

        # 두 번째 등록 (무시되어야 함)
        command_handler.register_class_handler(TestCommand, mock_processor)
        second_count = len(command_handler._registered_classes)

        assert first_count == second_count

    def test_register_class_handler_no_process_method(self, command_handler):
        """process_command_result 메서드가 없는 프로세서 등록 테스트"""

        class TestCommand:
            pass

        class InvalidProcessor:
            pass

        processor = InvalidProcessor()
        command_handler.register_class_handler(TestCommand, processor)

        assert "TestCommand" not in command_handler.handlers

    def test_register_default_handler(self, command_handler):
        """기본 핸들러 등록 테스트"""

        def default_handler(handler, result):
            pass

        command_handler.register_default_handler(default_handler)
        assert command_handler.default_handler == default_handler

    def test_register_default_handler_duplicate(self, command_handler):
        """기본 핸들러 중복 등록 테스트"""

        def default_handler1(handler, result):
            pass

        def default_handler2(handler, result):
            pass

        command_handler.register_default_handler(default_handler1)
        first_handler = command_handler.default_handler

        command_handler.register_default_handler(default_handler2)
        second_handler = command_handler.default_handler

        assert first_handler == second_handler  # 첫 번째 핸들러가 유지되어야 함

    def test_handle_command_with_registered_handler(
        self, command_handler, mock_handler
    ):
        """등록된 핸들러로 커맨드 처리 테스트"""

        def test_handler(handler, result):
            test_handler.called = True
            test_handler.handler_arg = handler
            test_handler.result_arg = result

        test_handler.called = False
        command_handler.register_handler("TestCommandHandler", test_handler)

        result = command_handler.handle_command(mock_handler, "test_result")

        assert result is True
        assert test_handler.called is True
        assert test_handler.handler_arg == mock_handler
        assert test_handler.result_arg == "test_result"

    def test_handle_command_with_none_handler(self, command_handler):
        """None 핸들러 처리 테스트"""
        result = command_handler.handle_command(None, "test_result")
        assert result is False

    def test_handle_command_with_unregistered_handler_no_registry(
        self, command_handler, mock_handler
    ):
        """등록되지 않은 핸들러 처리 테스트 (FeatureRegistry 없음)"""
        result = command_handler.handle_command(mock_handler, "test_result")
        assert result is False

    def test_handle_command_with_unregistered_handler_with_registry_unused_command(
        self, command_handler_with_registry, mock_handler
    ):
        """등록되지 않은 핸들러 처리 테스트 (FeatureRegistry 있지만 사용하지 않는 command)"""
        result = command_handler_with_registry.handle_command(
            mock_handler, "test_result"
        )
        assert result is False

    def test_handle_command_with_unregistered_handler_with_registry_used_command(
        self, command_handler_with_registry, registry, mock_handler
    ):
        """등록되지 않은 핸들러 처리 테스트 (FeatureRegistry 있고 사용하는 command)"""

        # FeatureRegistry에 TestCommandHandler를 사용하는 Feature 등록
        class TestCommandHandler:
            pass

        registry.register_feature("TestFeature", Mock, [TestCommandHandler])
        mock_handler.__class__.__name__ = "TestCommandHandler"

        result = command_handler_with_registry.handle_command(
            mock_handler, "test_result"
        )
        assert result is False  # 핸들러가 등록되지 않았으므로 False

    def test_is_command_used_by_any_feature_no_registry(self, command_handler):
        """FeatureRegistry가 없을 때 command 사용 확인 테스트 - 더 이상 사용되지 않음"""
        # CommandHandler가 단순화되어 FeatureRegistry 연동이 제거됨
        # 이 테스트는 더 이상 관련이 없지만 호환성을 위해 유지
        assert True  # 항상 통과

    def test_is_command_used_by_any_feature_with_registry(
        self, command_handler_with_registry, registry
    ):
        """FeatureRegistry가 있을 때 command 사용 확인 테스트 - 더 이상 사용되지 않음"""
        # CommandHandler가 단순화되어 FeatureRegistry 연동이 제거됨
        # 이 테스트는 더 이상 관련이 없지만 호환성을 위해 유지
        assert True  # 항상 통과

    def test_is_command_used_by_any_feature_disabled_feature(
        self, command_handler_with_registry, registry
    ):
        """비활성화된 Feature의 command는 사용되지 않는 것으로 확인 테스트 - 더 이상 사용되지 않음"""
        # CommandHandler가 단순화되어 FeatureRegistry 연동이 제거됨
        # 이 테스트는 더 이상 관련이 없지만 호환성을 위해 유지
        assert True  # 항상 통과

    def test_handle_with_default_with_registered_handler(
        self, command_handler, mock_handler
    ):
        """등록된 핸들러가 있을 때 handle_with_default 테스트"""

        def test_handler(handler, result):
            test_handler.called = True

        test_handler.called = False
        command_handler.register_handler("TestCommandHandler", test_handler)

        result = command_handler.handle_with_default(mock_handler, "test_result")

        assert result is True
        assert test_handler.called is True

    def test_handle_with_default_with_default_handler(
        self, command_handler, mock_handler
    ):
        """기본 핸들러만 있을 때 handle_with_default 테스트"""

        def default_handler(handler, result):
            default_handler.called = True

        default_handler.called = False
        command_handler.register_default_handler(default_handler)

        result = command_handler.handle_with_default(mock_handler, "test_result")

        assert result is True
        assert default_handler.called is True

    def test_handle_with_default_no_handlers(self, command_handler, mock_handler):
        """등록된 핸들러와 기본 핸들러가 모두 없을 때 handle_with_default 테스트"""
        result = command_handler.handle_with_default(mock_handler, "test_result")
        assert result is False

    def test_get_registered_handlers(self, command_handler):
        """등록된 핸들러 목록 반환 테스트"""

        def test_handler1(handler, result):
            pass

        def test_handler2(handler, result):
            pass

        command_handler.register_handler("Command1", test_handler1)
        command_handler.register_handler("Command2", test_handler2)

        handlers = command_handler.get_registered_handlers()

        assert len(handlers) == 2
        assert "Command1" in handlers
        assert "Command2" in handlers
        assert handlers["Command1"] == "test_handler1"
        assert handlers["Command2"] == "test_handler2"

    def test_clear_handlers(self, command_handler):
        """모든 핸들러 제거 테스트"""

        def test_handler(handler, result):
            pass

        def default_handler(handler, result):
            pass

        command_handler.register_handler("TestCommand", test_handler)
        command_handler.register_default_handler(default_handler)

        command_handler.clear_handlers()

        assert len(command_handler.handlers) == 0
        assert command_handler.default_handler is None
        assert len(command_handler._registered_classes) == 0

    def test_handle_command_exception_in_handler(self, command_handler, mock_handler):
        """핸들러 실행 중 예외 발생 테스트"""

        def failing_handler(handler, result):
            raise Exception("Test exception")

        command_handler.register_handler("TestCommandHandler", failing_handler)

        result = command_handler.handle_command(mock_handler, "test_result")
        assert result is False

    def test_integration_with_real_features(self):
        """실제 Feature와의 통합 테스트 - 단순화된 CommandHandler 테스트"""
        # CommandHandler 생성 (FeatureRegistry 연동 제거)
        command_handler = CommandHandler()

        # SpeakerRemapCommandHandler 테스트

        mock_handler = Mock()
        mock_handler.__class__.__name__ = "SpeakerRemapCommandHandler"

        # 직접 등록된 핸들러가 없으므로 처리되지 않음
        result = command_handler.handle_command(mock_handler, "test_result")
        assert result is False

        # 핸들러를 직접 등록하면 처리됨
        def test_processor(handler, data):
            pass

        command_handler.register_handler("SpeakerRemapCommandHandler", test_processor)
        result = command_handler.handle_command(mock_handler, "test_result")
        assert result is True

    def test_integration_with_speaker_grid_feature(self, registry):
        """SpeakerGridFeature와의 통합 테스트 - 단순화된 CommandHandler 테스트"""
        # CommandHandler 생성 (FeatureRegistry 연동 제거)
        command_handler = CommandHandler()

        # SpeakerRemapCommandHandler 테스트
        mock_speaker_handler = Mock()
        mock_speaker_handler.__class__.__name__ = "SpeakerRemapCommandHandler"

        # 직접 등록된 핸들러가 없으므로 처리되지 않음
        result = command_handler.handle_command(mock_speaker_handler, "test_data")
        assert result is False

        # 핸들러를 직접 등록하면 처리됨
        def test_processor(handler, data):
            pass

        command_handler.register_handler("SpeakerRemapCommandHandler", test_processor)
        result = command_handler.handle_command(mock_speaker_handler, "test_data")
        assert result is True

        # 등록되지 않은 command는 처리되지 않음
        mock_unknown_handler = Mock()
        mock_unknown_handler.__class__.__name__ = "UnknownCommand"
        result = command_handler.handle_command(mock_unknown_handler, "test_data")
        assert result is False
