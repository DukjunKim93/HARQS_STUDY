#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""JFrogUploader 단위 테스트"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.JFrogUploader import JFrogUploader, UploadProgress, UploadResult
from QSUtils.JFrogUtils.exceptions import (
    JFrogUploadError,
    JFrogConfigurationError,
)


class TestJFrogUploader:
    """JFrogUploader 클래스 테스트"""

    @pytest.fixture
    def config(self):
        """JFrogConfig fixture"""
        return JFrogConfig()

    @pytest.fixture
    def uploader(self, config):
        """JFrogUploader fixture"""
        return JFrogUploader(config)

    def test_initialization(self, config):
        """JFrogUploader 초기화 테스트"""
        uploader = JFrogUploader(config)
        assert uploader.config == config
        assert uploader.logger is not None
        assert uploader.active_uploads == {}

    def test_initialization_invalid_config(self):
        """잘못된 설정으로 초기화 테스트"""
        invalid_config = JFrogConfig(server_url="")  # 빈 서버 URL
        with pytest.raises(JFrogConfigurationError):
            JFrogUploader(invalid_config)

    def test_upload_file_success(self, uploader):
        """단일 파일 업로드 성공 테스트"""
        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024

                        mock_run.return_value = Mock(
                            returncode=0, stdout="Upload successful", stderr=""
                        )

                        result = uploader.upload_file("/test/file.txt", "target.txt")

                        assert result.success is True
                        assert result.total_uploaded == 1
                        assert result.total_failed == 0
                        assert result.total_size == 1024
                        assert len(result.uploaded_files) == 1
                        assert (
                            result.uploaded_files[0]["local_path"] == "/test/file.txt"
                        )
                        assert result.uploaded_files[0]["target_path"] == "target.txt"

    def test_upload_file_not_found(self, uploader):
        """파일을 찾을 수 없을 때 테스트"""
        with patch("pathlib.Path.exists", return_value=False):
            result = uploader.upload_file("/test/nonexistent.txt")

            assert result.success is False
            assert result.total_uploaded == 0
            assert result.total_failed == 1
            assert len(result.failed_files) == 1
            assert "파일을 찾을 수 없습니다" in result.failed_files[0]["error"]

    def test_upload_file_not_file(self, uploader):
        """파일이 아닐 때 테스트"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=False):
                result = uploader.upload_file("/test/directory")

                assert result.success is False
                assert "파일이 아닙니다" in result.failed_files[0]["error"]

    def test_upload_file_jf_error(self, uploader):
        """jf-cli 명령어 실패 테스트"""
        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024

                        mock_run.return_value = Mock(
                            returncode=1, stdout="", stderr="Permission denied"
                        )

                        result = uploader.upload_file("/test/file.txt")

                        assert result.success is False
                        assert result.total_uploaded == 0
                        assert result.total_failed == 1
                        assert "Permission denied" in result.failed_files[0]["error"]

    def test_upload_file_timeout(self, uploader):
        """업로드 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024

                        mock_run.side_effect = subprocess.TimeoutExpired("jf", 30)

                        result = uploader.upload_file("/test/file.txt")

                        assert result.success is False
                        assert result.total_failed == 1
                        assert len(result.failed_files) == 1
                        # 타임아웃 에러 메시지 확인
                        error_msg = result.failed_files[0]["error"]
                        assert (
                            "TimeoutExpired" in error_msg
                            or "업로드 타임아웃" in error_msg
                        )

    def test_upload_file_default_target(self, uploader):
        """타겟 경로 기본값 테스트"""
        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        with patch("pathlib.Path.name", "file.txt"):
                            mock_stat.return_value.st_size = 1024

                            mock_run.return_value = Mock(
                                returncode=0, stdout="Upload successful", stderr=""
                            )

                            result = uploader.upload_file("/test/file.txt")

                            assert result.success is True
                            assert result.uploaded_files[0]["target_path"] == "file.txt"

    def test_upload_directory_success(self, uploader):
        """디렉토리 업로드 성공 테스트"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=True):
                with patch("pathlib.Path.rglob") as mock_rglob:
                    with patch("pathlib.Path.relative_to") as mock_relative:
                        with patch("pathlib.Path.stat") as mock_stat:
                            # Mock 파일 목록
                            mock_file1 = Mock()
                            mock_file1.is_file.return_value = True
                            mock_file1.stat.return_value.st_size = 512
                            mock_file1.relative_to.return_value = Path("file1.txt")

                            mock_file2 = Mock()
                            mock_file2.is_file.return_value = True
                            mock_file2.stat.return_value.st_size = 256
                            mock_file2.relative_to.return_value = Path(
                                "subdir/file2.txt"
                            )

                            mock_rglob.return_value = [mock_file1, mock_file2]

                            # Mock 업로드 성공
                            with patch.object(uploader, "upload_file") as mock_upload:
                                mock_upload.side_effect = [
                                    Mock(
                                        success=True,
                                        uploaded_files=[
                                            {"local_path": "/test/file1.txt"}
                                        ],
                                    ),
                                    Mock(
                                        success=True,
                                        uploaded_files=[
                                            {"local_path": "/test/subdir/file2.txt"}
                                        ],
                                    ),
                                ]

                                result = uploader.upload_directory("/test/dir")

                                assert result.success is True
                                assert result.total_uploaded == 2
                                assert result.total_failed == 0
                                assert result.total_size == 768  # 512 + 256

    def test_upload_directory_not_found(self, uploader):
        """디렉토리를 찾을 수 없을 때 테스트"""
        with patch("pathlib.Path.exists", return_value=False):
            result = uploader.upload_directory("/test/nonexistent")

            assert result.success is False
            assert "디렉토리를 찾을 수 없습니다" in result.failed_files[0]["error"]

    def test_upload_directory_not_directory(self, uploader):
        """디렉토리가 아닐 때 테스트"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=False):
                result = uploader.upload_directory("/test/file.txt")

                assert result.success is False
                assert "디렉토리가 아닙니다" in result.failed_files[0]["error"]

    def test_upload_directory_empty(self, uploader):
        """빈 디렉토리 업로드 테스트"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=True):
                with patch("pathlib.Path.rglob", return_value=[]):
                    result = uploader.upload_directory("/test/empty")

                    assert result.success is True
                    assert result.total_uploaded == 0
                    assert result.total_failed == 0

    def test_upload_file_chunked_small_file(self, uploader):
        """작은 파일 청크 업로드 테스트 (일반 업로드 사용)"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1024  # 1KB (청크 크기보다 작음)

                with patch.object(uploader, "upload_file") as mock_upload:
                    mock_upload.return_value = Mock(success=True, uploaded_files=[{}])

                    result = uploader.upload_file_chunked("/test/small.txt")

                    assert result.success is True
                    mock_upload.assert_called_once_with("/test/small.txt", None, None)

    def test_upload_file_chunked_large_file(self, uploader):
        """대형 파일 청크 업로드 테스트"""
        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.stat") as mock_stat:
                    mock_stat.return_value.st_size = (
                        20 * 1024 * 1024
                    )  # 20MB (청크 크기보다 큼)

                    mock_run.return_value = Mock(
                        returncode=0, stdout="Chunked upload successful", stderr=""
                    )

                    result = uploader.upload_file_chunked("/test/large.bin")

                    assert result.success is True
                    assert result.total_size == 20 * 1024 * 1024
                    # 청크 업로드 명령어 확인
                    mock_run.assert_called_once()
                    cmd = mock_run.call_args[0][0]
                    assert "--chunk-size=10485760" in cmd  # 10MB

    def test_upload_file_chunked_custom_chunk_size(self, uploader):
        """사용자 정의 청크 크기 테스트"""
        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.stat") as mock_stat:
                    mock_stat.return_value.st_size = 15 * 1024 * 1024  # 15MB

                    mock_run.return_value = Mock(
                        returncode=0, stdout="Chunked upload successful", stderr=""
                    )

                    result = uploader.upload_file_chunked(
                        "/test/medium.bin", chunk_size=5 * 1024 * 1024
                    )

                    assert result.success is True
                    # 사용자 정의 청크 크기 확인
                    mock_run.assert_called_once()
                    cmd = mock_run.call_args[0][0]
                    assert "--chunk-size=5242880" in cmd  # 5MB

    def test_get_upload_progress(self, uploader):
        """업로드 진행 상태 가져오기 테스트"""
        # 진행 상태 추가
        progress = UploadProgress(
            upload_id="test_id",
            total_files=10,
            completed_files=5,
            total_bytes=1024,
            uploaded_bytes=512,
            current_file="/test/file.txt",
            speed_bps=1024.0,
            eta_seconds=0.5,
        )
        uploader.active_uploads["test_id"] = progress

        retrieved_progress = uploader.get_upload_progress("test_id")

        assert retrieved_progress is not None
        assert retrieved_progress.upload_id == "test_id"
        assert retrieved_progress.progress_percentage == 50.0
        assert retrieved_progress.file_progress_percentage == 50.0

    def test_get_upload_progress_not_found(self, uploader):
        """존재하지 않는 업로드 진행 상태 가져오기 테스트"""
        progress = uploader.get_upload_progress("nonexistent_id")
        assert progress is None

    def test_cancel_upload(self, uploader):
        """업로드 취소 테스트"""
        # 진행 상태 추가
        progress = UploadProgress(
            upload_id="test_id",
            total_files=1,
            completed_files=0,
            total_bytes=1024,
            uploaded_bytes=0,
            current_file="/test/file.txt",
            speed_bps=0.0,
            eta_seconds=0.0,
        )
        uploader.active_uploads["test_id"] = progress

        # 취소
        result = uploader.cancel_upload("test_id")
        assert result is True

        # 확인
        assert uploader.get_upload_progress("test_id") is None

    def test_cancel_upload_not_found(self, uploader):
        """존재하지 않는 업로드 취소 테스트"""
        result = uploader.cancel_upload("nonexistent_id")
        assert result is False

    def test_execute_jf_command_success(self, uploader):
        """jf-cli 명령어 실행 성공 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

            result = uploader._execute_jf_command(["jf", "rt", "ping"])

            assert result.returncode == 0
            assert result.stdout == "Success"
            mock_run.assert_called_once_with(
                ["jf", "rt", "ping"], capture_output=True, text=True, timeout=300
            )

    def test_execute_jf_command_failure(self, uploader):
        """jf-cli 명령어 실행 실패 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Error occurred"
            )

            result = uploader._execute_jf_command(["jf", "rt", "ping"])

            assert result.returncode == 1
            assert result.stderr == "Error occurred"

    def test_execute_jf_command_timeout(self, uploader):
        """jf-cli 명령어 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("jf", 30)

            with pytest.raises(JFrogUploadError):
                uploader._execute_jf_command(["jf", "rt", "ping"])

    def test_execute_jf_command_custom_timeout(self, uploader):
        """사용자 정의 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("jf", 60)

            with pytest.raises(JFrogUploadError):
                uploader._execute_jf_command(["jf", "rt", "ping"], timeout=60)


class TestUploadProgress:
    """UploadProgress 데이터클래스 테스트"""

    def test_upload_progress_creation(self):
        """UploadProgress 생성 테스트"""
        progress = UploadProgress(
            upload_id="test_id",
            total_files=10,
            completed_files=5,
            total_bytes=1024,
            uploaded_bytes=512,
            current_file="/test/file.txt",
            speed_bps=1024.0,
            eta_seconds=0.5,
        )

        assert progress.upload_id == "test_id"
        assert progress.total_files == 10
        assert progress.completed_files == 5
        assert progress.total_bytes == 1024
        assert progress.uploaded_bytes == 512
        assert progress.current_file == "/test/file.txt"
        assert progress.speed_bps == 1024.0
        assert progress.eta_seconds == 0.5

    def test_progress_percentage(self):
        """진행률 계산 테스트"""
        progress = UploadProgress(
            upload_id="test_id",
            total_files=10,
            completed_files=5,
            total_bytes=1000,
            uploaded_bytes=250,
            current_file="/test/file.txt",
            speed_bps=100.0,
            eta_seconds=7.5,
        )

        assert progress.progress_percentage == 25.0  # 250/1000 * 100
        assert progress.file_progress_percentage == 50.0  # 5/10 * 100

    def test_progress_percentage_zero_total(self):
        """전체 크기가 0일 때 진행률 테스트"""
        progress = UploadProgress(
            upload_id="test_id",
            total_files=0,
            completed_files=0,
            total_bytes=0,
            uploaded_bytes=0,
            current_file="",
            speed_bps=0.0,
            eta_seconds=0.0,
        )

        assert progress.progress_percentage == 0.0
        assert progress.file_progress_percentage == 0.0


class TestUploadResult:
    """UploadResult 데이터클래스 테스트"""

    def test_upload_result_creation(self):
        """UploadResult 생성 테스트"""
        result = UploadResult(
            success=True,
            uploaded_files=[{"local_path": "/test/file.txt"}],
            failed_files=[],
            total_uploaded=1,
            total_failed=0,
            total_size=1024,
            upload_time=5.5,
        )

        assert result.success is True
        assert len(result.uploaded_files) == 1
        assert len(result.failed_files) == 0
        assert result.total_uploaded == 1
        assert result.total_failed == 0
        assert result.total_size == 1024
        assert result.upload_time == 5.5

    def test_upload_result_defaults(self):
        """UploadResult 기본값 테스트"""
        result = UploadResult(
            success=False,
            uploaded_files=[],
            failed_files=[],
            total_uploaded=0,
            total_failed=0,
            total_size=0,
            upload_time=0.0,
        )

        assert result.success is False
        assert result.uploaded_files == []
        assert result.failed_files == []
        assert result.total_uploaded == 0
        assert result.total_failed == 0
        assert result.total_size == 0
        assert result.upload_time == 0.0
