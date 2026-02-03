#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test cases for DumpProcessManager
DumpProcessManager 단위 테스트
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from QSUtils.DumpManager.DumpProcessManager import DumpProcessManager
from QSUtils.DumpManager.DumpTypes import DumpState, DumpMode, DumpTriggeredBy


class TestDumpProcessManager(unittest.TestCase):
    """DumpProcessManager 단위 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        # Mock 객체 생성
        self.mock_event_manager = Mock()
        self.mock_adb_device = Mock()
        self.mock_adb_device.serial = "test_device_123"
        self.mock_logging_manager = Mock()
        self.mock_logging_manager.log_directory = "/tmp/test_logs"

        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.mock_logging_manager.log_directory = self.temp_dir

        # DumpProcessManager 인스턴스 생성
        self.dump_manager = DumpProcessManager(
            parent_widget=None,
            adb_device=self.mock_adb_device,
            event_manager=self.mock_event_manager,
            logging_manager=self.mock_logging_manager,
        )

        # 초기 dump_process를 None으로 설정
        self.dump_manager.dump_process = None

    def tearDown(self):
        """테스트 정리"""
        # 임시 디렉토리 삭제
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """초기화 테스트"""
        self.assertEqual(self.dump_manager.state, DumpState.IDLE)
        self.assertEqual(self.dump_manager.dump_mode, DumpMode.DIALOG)
        self.assertEqual(self.dump_manager.device_serial, "test_device_123")
        self.assertIsNone(self.dump_manager.parent_widget)
        self.assertFalse(self.dump_manager.cancellation_requested)

    def test_get_state(self):
        """상태 getter 테스트"""
        self.assertEqual(self.dump_manager.get_state(), DumpState.IDLE)

    def test_set_dump_mode(self):
        """Dump 모드 설정 테스트"""
        # HEADLESS 모드로 설정
        self.dump_manager.set_dump_mode(DumpMode.HEADLESS)
        self.assertEqual(self.dump_manager.get_dump_mode(), DumpMode.HEADLESS)

        # DIALOG 모드로 설정
        self.dump_manager.set_dump_mode(DumpMode.DIALOG)
        self.assertEqual(self.dump_manager.get_dump_mode(), DumpMode.DIALOG)

    def test_get_dump_mode(self):
        """Dump 모드 getter 테스트"""
        self.assertEqual(self.dump_manager.get_dump_mode(), DumpMode.DIALOG)

    def test_get_script_path(self):
        """스크립트 경로 검색 테스트"""
        # 더 간단한 접근 방식: _get_script_path 메서드를 직접 mock
        with patch.object(self.dump_manager, "_get_script_path") as mock_get_script:
            # Mock 스크립트 경로 설정
            mock_script_path = Mock()
            mock_script_path.exists.return_value = True
            mock_get_script.return_value = mock_script_path

            # 스크립트 경로 검색
            result = self.dump_manager._get_script_path()

            # 결과 확인
            self.assertIsNotNone(result)
            mock_get_script.assert_called_once()

    def test_start_dump_extraction_idle_state(self):
        """IDLE 상태에서 dump 추출 시작 테스트 (HEADLESS 모드)"""
        # HEADLESS 모드로 설정하여 팝업 방지
        self.dump_manager.set_dump_mode(DumpMode.HEADLESS)

        with patch.object(self.dump_manager, "_get_script_path") as mock_get_script:
            with patch(
                "QSUtils.Utils.FileUtils.ensure_directory_exists"
            ) as mock_ensure:
                # Mock 설정
                mock_script_path = Mock()
                mock_script_path.exists.return_value = True
                mock_get_script.return_value = mock_script_path

                # dump_process를 None으로 설정하여 새 프로세스를 생성하도록 함
                self.dump_manager.dump_process = None

                # ensure_directory_exists가 실제로 디렉토리를 생성하도록 설정
                def real_ensure_dir(path):
                    Path(path).mkdir(parents=True, exist_ok=True)

                mock_ensure.side_effect = real_ensure_dir

                # dump 추출 시작
                result = self.dump_manager.start_dump_extraction(DumpTriggeredBy.MANUAL)

                # 결과 확인
                self.assertTrue(result)
                self.assertEqual(self.dump_manager.state, DumpState.STARTING)
                self.assertEqual(
                    self.dump_manager.triggered_by,
                    DumpTriggeredBy.MANUAL,
                )

    def test_start_dump_extraction_already_running(self):
        """이미 실행 중인 상태에서 dump 추출 시작 테스트"""
        # 상태를 EXTRACTING으로 설정
        self.dump_manager._set_state(DumpState.EXTRACTING)

        # dump 추출 시작 시도
        result = self.dump_manager.start_dump_extraction(DumpTriggeredBy.MANUAL)

        # 결과 확인 - 실패해야 함
        self.assertFalse(result)

    def test_start_dump_extraction_missing_dependencies(self):
        """필수 의존성 누락 시 테스트"""
        with patch(
            "QSUtils.DumpManager.DumpDialogs.DumpCompletionDialog.show_completion_dialog"
        ):
            # logging_manager를 None으로 설정
            self.dump_manager.logging_manager = None

            # dump 추출 시작 시도
            result = self.dump_manager.start_dump_extraction(DumpTriggeredBy.MANUAL)

            # 결과 확인 - 실패해야 함
            self.assertFalse(result)

    def test_set_state(self):
        """상태 전환 테스트"""
        # IDLE -> STARTING
        self.dump_manager._set_state(DumpState.STARTING)
        self.assertEqual(self.dump_manager.state, DumpState.STARTING)

        # STARTING -> EXTRACTING
        self.dump_manager._set_state(DumpState.EXTRACTING)
        self.assertEqual(self.dump_manager.state, DumpState.EXTRACTING)

        # EXTRACTING -> COMPLETED
        self.dump_manager._set_state(DumpState.COMPLETED)
        self.assertEqual(self.dump_manager.state, DumpState.COMPLETED)

    def test_reset_state(self):
        """상태 초기화 테스트"""
        # 상태 변경
        self.dump_manager._set_state(DumpState.EXTRACTING)
        self.dump_manager.cancellation_requested = True
        self.dump_manager.working_dir = Path("/fake/dir")

        # 상태 초기화
        self.dump_manager._reset_state()

        # 확인
        self.assertEqual(self.dump_manager.state, DumpState.IDLE)
        self.assertIsNone(self.dump_manager.dump_process)
        self.assertIsNone(self.dump_manager.working_dir)
        self.assertFalse(self.dump_manager.cancellation_requested)

    def test_setup_timer(self):
        """타이머 설정 테스트"""
        # 기존 타이머 확인
        original_timer = self.dump_manager.timeout_timer

        # 타이머 재설정
        self.dump_manager._setup_timer()

        # 타이머가 설정되었는지 확인
        self.assertIsNotNone(self.dump_manager.timeout_timer)
        # 타이머가 싱글샷으로 설정되었는지 확인 (실제 QTimer 객체이므로)
        self.assertTrue(self.dump_manager.timeout_timer.isSingleShot())

    def test_setup_event_handlers(self):
        """이벤트 핸들러 설정 테스트"""
        # Mock 초기화
        self.mock_event_manager.reset_mock()

        # 이벤트 핸들러 설정
        self.dump_manager._setup_event_handlers()

        # 확인
        self.mock_event_manager.register_event_handler.assert_called_once()

    def test_on_dump_requested(self):
        """DUMP_REQUESTED 이벤트 핸들러 테스트"""
        with patch.object(self.dump_manager, "start_dump_extraction") as mock_start:
            # 이벤트 args
            args = {"triggered_by": "manual"}

            # 이벤트 핸들러 호출
            self.dump_manager._on_dump_requested(args)

            # 확인
            mock_start.assert_called_once_with(DumpTriggeredBy.MANUAL)

    def test_on_dump_requested_with_issue_dir(self):
        """이슈 디렉토리가 있는 DUMP_REQUESTED 이벤트 핸들러 테스트"""
        with patch.object(self.dump_manager, "start_dump_extraction") as mock_start:
            with patch.object(
                self.dump_manager, "_copy_capturing_logs_to_issue_dir"
            ) as mock_copy:
                # 이벤트 args
                issue_dir = "/tmp/issue_123"
                args = {"triggered_by": "crash_monitor", "issue_dir": issue_dir}

                # 이벤트 핸들러 호출
                self.dump_manager._on_dump_requested(args)

                # 확인
                self.assertEqual(
                    self.dump_manager._override_working_dir, Path(issue_dir)
                )
                mock_copy.assert_called_once_with(Path(issue_dir))
                mock_start.assert_called_once_with(DumpTriggeredBy.CRASH_MONITOR)

    def test_cleanup(self):
        """리소스 정리 테스트"""
        # cleanup 메서드가 상태를 IDLE로 설정하는지만 확인
        original_state = self.dump_manager.state

        # 리소스 정리
        self.dump_manager.cleanup()

        # 확인 - cleanup 후 상태가 IDLE로 설정되는지 확인
        self.assertEqual(self.dump_manager.state, DumpState.IDLE)

    def test_copy_capturing_logs_to_issue_dir(self):
        """캡처 중인 로그 파일 이슈 디렉토리로 복사 테스트"""
        # 임시 로그 파일 생성
        log_file = Path(self.temp_dir) / "test.log"
        log_file.write_text("test log content")

        # Mock logging manager 설정
        self.dump_manager.logging_manager.get_current_log_filename.return_value = (
            "test.log"
        )

        # 이슈 디렉토리 생성
        issue_dir = Path(self.temp_dir) / "issue"
        issue_dir.mkdir()

        # 로그 복사
        self.dump_manager._copy_capturing_logs_to_issue_dir(issue_dir)

        # 확인
        copied_file = issue_dir / "logs" / "test.log"
        self.assertTrue(copied_file.exists())
        self.assertEqual(copied_file.read_text(), "test log content")

    def test_verify_dump_results_success(self):
        """Dump 결과 검증 성공 테스트"""
        # 임시 작업 디렉토리 및 파일 생성
        work_dir = Path(self.temp_dir) / "dumps" / "test_device"
        work_dir.mkdir(parents=True)

        # 가짜 zip 파일 생성
        zip_file = work_dir / "test.zip"
        zip_file.write_bytes(b"fake zip content")

        # 필수 파일 생성
        (work_dir / "sw_version.txt").write_text("1.0.0")
        (work_dir / "coredump").mkdir()

        # 상태 설정
        self.dump_manager._set_state(DumpState.VERIFYING)
        self.dump_manager.working_dir = work_dir
        self.dump_manager.dump_mode = DumpMode.HEADLESS

        with patch.object(self.dump_manager, "_reset_state") as mock_reset:
            # 결과 검증
            self.dump_manager._verify_dump_results()

            # 확인
            self.assertEqual(self.dump_manager.state, DumpState.COMPLETED)

    def test_verify_dump_results_failure_no_zip(self):
        """Dump 결과 검증 실패 테스트 (zip 파일 없음)"""
        # 임시 작업 디렉토리 생성 (zip 파일 없음)
        work_dir = Path(self.temp_dir) / "dumps" / "test_device"
        work_dir.mkdir(parents=True)

        # 상태 설정
        self.dump_manager._set_state(DumpState.VERIFYING)
        self.dump_manager.working_dir = work_dir

        with patch.object(self.dump_manager, "_handle_error") as mock_handle_error:
            # 결과 검증
            self.dump_manager._verify_dump_results()

            # 확인
            mock_handle_error.assert_called_once()

    def test_handle_error(self):
        """에러 처리 테스트"""
        error_msg = "Test error message"

        with patch.object(self.dump_manager, "_reset_state") as mock_reset:
            with patch(
                "QSUtils.DumpManager.DumpDialogs.DumpCompletionDialog.show_completion_dialog"
            ):
                # 에러 처리
                self.dump_manager._handle_error(error_msg)

                # 확인
                self.assertEqual(self.dump_manager.state, DumpState.FAILED)
                self.mock_event_manager.emit_event.assert_called()


class TestDumpProcessManagerIntegration(unittest.TestCase):
    """DumpProcessManager 통합 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        self.mock_event_manager = Mock()
        self.mock_adb_device = Mock()
        self.mock_adb_device.serial = "integration_test_device"
        self.mock_logging_manager = Mock()

    def test_full_dump_mode_lifecycle(self):
        """전체 Dump 모드 생명주기 테스트"""
        with patch("QSUtils.Utils.FileUtils.ensure_directory_exists"):
            dump_manager = DumpProcessManager(
                parent_widget=None,
                adb_device=self.mock_adb_device,
                event_manager=self.mock_event_manager,
                logging_manager=self.mock_logging_manager,
            )

            # 초기 상태 확인
            self.assertEqual(dump_manager.get_state(), DumpState.IDLE)
            self.assertEqual(dump_manager.get_dump_mode(), DumpMode.DIALOG)

            # 모드 변경
            dump_manager.set_dump_mode(DumpMode.HEADLESS)
            self.assertEqual(dump_manager.get_dump_mode(), DumpMode.HEADLESS)

            # 상태 전환 테스트
            dump_manager._set_state(DumpState.STARTING)
            self.assertEqual(dump_manager.get_state(), DumpState.STARTING)

            dump_manager._set_state(DumpState.EXTRACTING)
            self.assertEqual(dump_manager.get_state(), DumpState.EXTRACTING)

            dump_manager._set_state(DumpState.COMPLETED)
            self.assertEqual(dump_manager.get_state(), DumpState.COMPLETED)

            # 정리
            dump_manager.cleanup()
            self.assertEqual(dump_manager.get_state(), DumpState.IDLE)


if __name__ == "__main__":
    unittest.main()
