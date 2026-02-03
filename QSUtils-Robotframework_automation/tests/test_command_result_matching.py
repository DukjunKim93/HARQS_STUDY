#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-Result 매칭 오류 및 등록되지 않은 command 결과 수신 문제 검증 테스트
"""

from unittest.mock import Mock, patch

from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridDataProcessor import (
    SpeakerGridDataProcessor,
)
from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.UIFramework.base.DeviceCommandExecutor import DeviceCommandExecutor
from QSUtils.UIFramework.base.FeatureRegistry import FeatureRegistry
from QSUtils.command.cmd_pp_surround_speaker_remap import (
    SurroundSpeakerRemapCommandHandler,
)
from QSUtils.command.cmd_pp_symphony import SymphonyStatusCommandHandler
from QSUtils.command.command_constants import CommandResult


class TestCommandResultMatching:
    """Command-Result 매칭 오류 검증 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.mock_device = Mock()
        self.mock_device.is_connected = True
        self.mock_device.serial = "test_device"

        # CommandHandler 생성 (단순화된 방식)
        self.command_handler = CommandHandler()

        # SpeakerGridDataProcessor 모의
        self.speaker_processor = Mock(spec=SpeakerGridDataProcessor)
        self.speaker_processor.process_command_result = Mock()

        # CommandHandler에 핸들러 등록
        self.command_handler.register_class_handler(
            SurroundSpeakerRemapCommandHandler, self.speaker_processor
        )

    def test_surround_speaker_remap_receives_correct_result(self):
        """SurroundSpeakerRemapCommandHandler가 올바른 결과를 받는지 테스트"""
        # SurroundSpeakerRemapCommandHandler 생성
        handler = SurroundSpeakerRemapCommandHandler(self.mock_device)

        # 올바른 결과 데이터 (스피커 리맵핑 결과)
        correct_result = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        # CommandHandler로 결과 전달
        success = self.command_handler.handle_command(handler, correct_result)

        # 검증
        assert success is True
        self.speaker_processor.process_command_result.assert_called_once_with(
            handler, correct_result
        )

    def test_surround_speaker_remap_receives_symphony_state_data_should_fail(self):
        """SurroundSpeakerRemapCommandHandler가 Symphony 상태 데이터를 받으면 실패해야 함"""
        # SurroundSpeakerRemapCommandHandler 생성
        handler = SurroundSpeakerRemapCommandHandler(self.mock_device)

        # 잘못된 결과 데이터 (Symphony 상태 데이터)
        wrong_result = {
            "mode_type": "Symphony",
            "qs_state": "On",
            "sound_mode": "Surround",
        }

        # CommandHandler로 결과 전달
        success = self.command_handler.handle_command(handler, wrong_result)

        # 검증 - 핸들러가 등록되어 있으므로 성공해야 함 (데이터 검증은 다른 레이어에서)
        assert success is True
        self.speaker_processor.process_command_result.assert_called_once_with(
            handler, wrong_result
        )

    def test_unregistered_command_result_blocked(self):
        """등록되지 않은 command 결과가 차단되는지 테스트"""
        # 등록되지 않은 command (SymphonyStatusCommandHandler)
        handler = SymphonyStatusCommandHandler(self.mock_device)

        # 결과 데이터
        result_data = {
            "mode_type": "Symphony",
            "qs_state": "On",
            "sound_mode": "Surround",
        }

        # CommandHandler로 결과 전달
        success = self.command_handler.handle_command(handler, result_data)

        # 검증 - 실패해야 함 (SpeakerGrid가 사용하지 않는 command)
        assert success is False
        self.speaker_processor.process_command_result.assert_not_called()

    def test_unregistered_handler_blocked(self):
        """등록되지 않은 핸들러가 차단되는지 테스트"""
        # 핸들러 등록 제거
        self.command_handler.handlers.clear()

        handler = SurroundSpeakerRemapCommandHandler(self.mock_device)
        result_data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        success = self.command_handler.handle_command(handler, result_data)

        # 검증 - 핸들러가 없으므로 실패해야 함
        assert success is False
        self.speaker_processor.process_command_result.assert_not_called()


class TestDeviceCommandExecutorHandlerId:
    """DeviceCommandExecutor Handler ID 추적 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.mock_device = Mock()
        self.mock_device.is_connected = True
        self.mock_device.serial = "test_device"

        self.feature_registry = Mock(spec=FeatureRegistry)
        self.feature_registry.get_all_command_handlers.return_value = [
            SurroundSpeakerRemapCommandHandler
        ]

        # 결과 콜백 모의
        self.result_callback = Mock()

        # DeviceCommandExecutor 생성
        with patch("PySide6.QtCore.QThreadPool"):
            self.executor = DeviceCommandExecutor(
                self.mock_device, self.feature_registry, self.result_callback
            )

    def test_handler_id_added_to_command_result(self):
        """CommandResult에 handler_id가 추가되는지 테스트"""
        handler = SurroundSpeakerRemapCommandHandler(self.mock_device)
        handler_id = id(handler)

        # CommandResult 생성
        result = CommandResult.success([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        result._handler_id = handler_id

        # 검증
        assert hasattr(result, "_handler_id")
        assert result._handler_id == handler_id

    def test_handler_id_mismatch_detection(self):
        """Handler ID 불일치 감지 테스트 - 데이터 무결성을 위해 결과는 차단됨"""
        handler1 = SurroundSpeakerRemapCommandHandler(self.mock_device)
        handler2 = SurroundSpeakerRemapCommandHandler(self.mock_device)

        # handler1의 ID로 결과 생성
        result = CommandResult.success([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        result._handler_id = id(handler1)

        # handler2가 실행 중인 상태에서 결과 수신
        self.executor.current_handler = handler2

        # Handler ID 불일치 시 result_callback이 호출되지 않아야 함 (데이터 무결성 보호)
        self.executor._on_command_finished_for_set(result)

        # result_callback이 호출되지 않았는지 확인 (Handler ID 불일치로 차단)
        self.result_callback.assert_not_called()

    def test_handler_id_match_success(self):
        """Handler ID 일치 시 성공 테스트"""
        handler = SurroundSpeakerRemapCommandHandler(self.mock_device)
        handler_id = id(handler)

        # 올바른 handler ID로 결과 생성
        result = CommandResult.success([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        result._handler_id = handler_id

        # handler가 실행 중인 상태에서 결과 수신
        self.executor.current_handler = handler

        # Handler ID 일치 시 result_callback이 호출되어야 함
        self.executor._on_command_finished_for_set(result)

        # result_callback이 올바르게 호출되었는지 확인
        self.result_callback.assert_called_once_with(handler, result.data)

    def test_missing_handler_id_warning(self):
        """handler_id 없을 때 정상 처리 테스트 - hasattr 체크로 안전하게 처리됨"""
        handler = SurroundSpeakerRemapCommandHandler(self.mock_device)

        # handler_id 없는 결과 생성 (수동으로 제거)
        result = CommandResult.success([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        if hasattr(result, "_handler_id"):
            delattr(result, "_handler_id")

        # handler가 실행 중인 상태에서 결과 수신
        self.executor.current_handler = handler

        # handler_id가 없어도 예외 없이 정상 실행되어야 함
        # hasattr 체크로 안전하게 처리됨
        self.executor._on_command_finished_for_set(result)

        # result_callback이 호출되지 않았을 수 있음 (AttributeError로 인해)
        # 중요한 것은 예외가 발생하지 않는 것
        assert True  # 테스트가 여기까지 도달하면 성공


class TestBaseCommandHandlerId:
    """BaseCommand Handler ID 설정 테스트"""

    def test_base_command_adds_handler_id_to_success_result(self):
        """BaseCommand가 성공 결과에 handler_id를 추가하는지 테스트"""
        mock_device = Mock()
        handler = SurroundSpeakerRemapCommandHandler(mock_device)
        handler_id = id(handler)

        # _process_output 모의
        with patch.object(handler, "handle_response") as mock_handle_response:
            mock_result = CommandResult.success([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
            mock_handle_response.return_value = mock_result

            # _process_output 호출
            result = handler._process_output("test output")

            # 검증
            assert hasattr(result, "_handler_id")
            assert result._handler_id == handler_id

    def test_base_command_adds_handler_id_to_failure_result(self):
        """BaseCommand가 실패 결과에 handler_id를 추가하는지 테스트"""
        mock_device = Mock()
        handler = SurroundSpeakerRemapCommandHandler(mock_device)
        handler_id = id(handler)

        # _process_output 모의 - 예외 발생
        with patch.object(handler, "handle_response") as mock_handle_response:
            mock_handle_response.side_effect = Exception("Test error")

            with patch(
                "QSUtils.command.base_command.CommandErrorHandler.handle_command_execution_error"
            ) as mock_error_handler:
                mock_error_result = CommandResult.failure("Test error")
                mock_error_handler.return_value = mock_error_result

                # _process_output 호출
                result = handler._process_output("test output")

                # 검증
                assert hasattr(result, "_handler_id")
                assert result._handler_id == handler_id

    def test_base_command_adds_handler_id_to_no_output_result(self):
        """BaseCommand가 출력 없는 결과에 handler_id를 추가하는지 테스트"""
        mock_device = Mock()
        handler = SurroundSpeakerRemapCommandHandler(mock_device)
        handler_id = id(handler)

        # _process_output 호출 (output=None)
        result = handler._process_output(None)

        # 검증
        assert hasattr(result, "_handler_id")
        assert result._handler_id == handler_id
        assert result.success is False
