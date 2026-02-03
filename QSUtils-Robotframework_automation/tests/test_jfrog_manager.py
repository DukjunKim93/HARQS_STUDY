#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""JFrogManager 단위 테스트"""

from unittest.mock import Mock, patch

import pytest

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.JFrogManager import JFrogManager, JFrogOperationResult
from QSUtils.JFrogUtils.exceptions import (
    JFrogConfigurationError,
)


class TestJFrogManager:
    """JFrogManager 클래스 테스트"""

    @pytest.fixture
    def config(self):
        """JFrogConfig fixture"""
        return JFrogConfig()

    @pytest.fixture
    def manager(self, config):
        """JFrogManager fixture"""
        return JFrogManager(config)

    def test_initialization(self, config):
        """JFrogManager 초기화 테스트"""
        manager = JFrogManager(config)
        assert manager.config == config
        assert manager.logger is not None
        assert manager.auth_manager is not None
        assert manager.permission_checker is not None
        assert manager.uploader is not None

    def test_initialization_invalid_config(self):
        """잘못된 설정으로 초기화 테스트"""
        invalid_config = JFrogConfig(server_url="")  # 빈 서버 URL
        with pytest.raises(JFrogConfigurationError):
            JFrogManager(invalid_config)

    def test_initialization_default_config(self):
        """기본 설정으로 초기화 테스트"""
        manager = JFrogManager()
        assert manager.config is not None
        assert manager.config.server_url == "https://bart.sec.samsung.net/artifactory"

    def test_verify_setup_success(self, manager):
        """설정 확인 성공 테스트"""
        with patch.object(manager, "_check_jf_cli_installed", return_value=True):
            with patch.object(manager, "_check_authentication") as mock_auth:
                with patch.object(manager, "_check_permissions") as mock_perm:
                    mock_auth.return_value = JFrogOperationResult(success=True)
                    mock_perm.return_value = JFrogOperationResult(success=True)

                    result = manager.verify_setup()

                    assert result.success is True
                    assert "JFrog 설정 확인 완료" in result.message
                    assert result.data["server_url"] == manager.config.server_url
                    assert result.data["repository"] == manager.config.default_repo

    def test_verify_setup_jf_not_installed(self, manager):
        """jf-cli 설치되지 않았을 때 테스트"""
        with patch.object(manager, "_check_jf_cli_installed", return_value=False):
            result = manager.verify_setup()

            assert result.success is False
            assert "jf-cli가 설치되지 않았습니다" in result.message

    def test_verify_setup_auth_failure(self, manager):
        """인증 실패 테스트"""
        with patch.object(manager, "_check_jf_cli_installed", return_value=True):
            with patch.object(manager, "_check_authentication") as mock_auth:
                mock_auth.return_value = JFrogOperationResult(
                    success=False, message="인증 실패"
                )

                result = manager.verify_setup()

                assert result.success is False
                assert result.message == "인증 실패"

    def test_verify_setup_permission_failure(self, manager):
        """권한 확인 실패 테스트"""
        with patch.object(manager, "_check_jf_cli_installed", return_value=True):
            with patch.object(manager, "_check_authentication") as mock_auth:
                with patch.object(manager, "_check_permissions") as mock_perm:
                    mock_auth.return_value = JFrogOperationResult(success=True)
                    mock_perm.return_value = JFrogOperationResult(
                        success=False, message="권한 없음"
                    )

                    result = manager.verify_setup()

                    assert result.success is False
                    assert result.message == "권한 없음"

    def test_verify_setup_skip_permissions(self, manager):
        """권한 확인 건너뛰기 테스트"""
        manager.config.check_permissions = False

        with patch.object(manager, "_check_jf_cli_installed", return_value=True):
            with patch.object(manager, "_check_authentication") as mock_auth:
                mock_auth.return_value = JFrogOperationResult(success=True)

                result = manager.verify_setup()

                assert result.success is True
                # 권한 확인은 호출되지 않아야 함
                # (이 부분은 mock 호출 횟수로 확인할 수 있음)

    def test_check_permissions_success(self, manager):
        """권한 확인 성공 테스트"""
        with patch.object(manager, "_check_permissions") as mock_check:
            mock_check.return_value = JFrogOperationResult(success=True)

            result = manager.check_permissions()

            assert result.success is True
            mock_check.assert_called_once()

    def test_check_permissions_failure(self, manager):
        """권한 확인 실패 테스트"""
        with patch.object(manager, "_check_permissions") as mock_check:
            mock_check.return_value = JFrogOperationResult(
                success=False, message="권한 없음"
            )

            result = manager.check_permissions()

            assert result.success is False
            assert result.message == "권한 없음"

    def test_upload_file_success(self, manager):
        """단일 파일 업로드 성공 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        with patch.object(
                            manager.uploader, "upload_file"
                        ) as mock_upload:
                            mock_verify.return_value = JFrogOperationResult(
                                success=True
                            )
                            mock_stat.return_value.st_size = 1024

                            mock_upload.return_value = Mock(
                                success=True,
                                uploaded_files=[
                                    {
                                        "local_path": "/test/file.txt",
                                        "target_path": "target.txt",
                                        "url": "https://test.com/target.txt",
                                        "size": 1024,
                                    }
                                ],
                                total_uploaded=1,
                                total_failed=0,
                                total_size=1024,
                                upload_time=2.5,
                            )

                            result = manager.upload_file("/test/file.txt", "target.txt")

                            assert result.success is True
                            assert "파일 업로드 성공" in result.message
                            assert result.data["total_uploaded"] == 1
                            assert result.data["total_size"] == 1024

    def test_upload_file_setup_failure(self, manager):
        """설정 확인 실패로 업로드 실패 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            mock_verify.return_value = JFrogOperationResult(
                success=False, message="설정 오류"
            )

            result = manager.upload_file("/test/file.txt")

            assert result.success is False
            assert result.message == "설정 오류"

    def test_upload_file_not_found(self, manager):
        """파일을 찾을 수 없을 때 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=False):
                mock_verify.return_value = JFrogOperationResult(success=True)

                result = manager.upload_file("/test/nonexistent.txt")

                assert result.success is False
                assert "파일을 찾을 수 없습니다" in result.message

    def test_upload_file_uploader_failure(self, manager):
        """업로더 실패 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch.object(manager.uploader, "upload_file") as mock_upload:
                        mock_verify.return_value = JFrogOperationResult(success=True)

                        mock_upload.return_value = Mock(
                            success=False,
                            failed_files=[
                                {
                                    "local_path": "/test/file.txt",
                                    "target_path": "target.txt",
                                    "error": "Permission denied",
                                }
                            ],
                            total_uploaded=0,
                            total_failed=1,
                            total_size=0,
                            upload_time=0.0,
                        )

                        result = manager.upload_file("/test/file.txt", "target.txt")

                        assert result.success is False
                        assert "Permission denied" in result.message

    def test_upload_file_default_target(self, manager):
        """타겟 경로 기본값 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        with patch("pathlib.Path.name", "file.txt"):
                            with patch.object(
                                manager.uploader, "upload_file"
                            ) as mock_upload:
                                mock_verify.return_value = JFrogOperationResult(
                                    success=True
                                )
                                mock_stat.return_value.st_size = 1024

                                mock_upload.return_value = Mock(
                                    success=True,
                                    uploaded_files=[{"target_path": "file.txt"}],
                                    total_uploaded=1,
                                    total_failed=0,
                                    total_size=1024,
                                    upload_time=2.5,
                                )

                                result = manager.upload_file("/test/file.txt")

                                assert result.success is True
                                # 타겟 경로가 파일명으로 설정되었는지 확인
                                mock_upload.assert_called_once_with(
                                    "/test/file.txt", "file.txt", None
                                )

    def test_upload_directory_success(self, manager):
        """디렉토리 업로드 성공 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_dir", return_value=True):
                    with patch.object(
                        manager.uploader, "upload_directory"
                    ) as mock_upload:
                        mock_verify.return_value = JFrogOperationResult(success=True)

                        mock_upload.return_value = Mock(
                            success=True,
                            uploaded_files=[
                                {"local_path": "/test/dir/file1.txt"},
                                {"local_path": "/test/dir/file2.txt"},
                            ],
                            total_uploaded=2,
                            total_failed=0,
                            total_size=1536,
                            upload_time=5.0,
                        )

                        result = manager.upload_directory("/test/dir", "target")

                        assert result.success is True
                        assert "디렉토리 업로드 성공" in result.message
                        assert result.data["total_uploaded"] == 2
                        assert result.data["total_size"] == 1536

    def test_upload_directory_not_found(self, manager):
        """디렉토리를 찾을 수 없을 때 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=False):
                mock_verify.return_value = JFrogOperationResult(success=True)

                result = manager.upload_directory("/test/nonexistent")

                assert result.success is False
                assert "디렉토리를 찾을 수 없습니다" in result.message

    def test_upload_directory_not_directory(self, manager):
        """디렉토리가 아닐 때 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_dir", return_value=False):
                    mock_verify.return_value = JFrogOperationResult(success=True)

                    result = manager.upload_directory("/test/file.txt")

                    assert result.success is False
                    assert "디렉토리를 찾을 수 없습니다" in result.message

    def test_upload_directory_default_target(self, manager):
        """디렉토리 타겟 경로 기본값 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_dir", return_value=True):
                    with patch("pathlib.Path.name", "test_dir"):
                        with patch.object(
                            manager.uploader, "upload_directory"
                        ) as mock_upload:
                            mock_verify.return_value = JFrogOperationResult(
                                success=True
                            )

                            mock_upload.return_value = Mock(
                                success=True,
                                uploaded_files=[],
                                total_uploaded=0,
                                total_failed=0,
                                total_size=0,
                                upload_time=0.0,
                            )

                            result = manager.upload_directory("/test/test_dir")

                            assert result.success is True
                            # 타겟 경로가 디렉토리명으로 설정되었는지 확인
                            mock_upload.assert_called_once_with(
                                "/test/test_dir", "test_dir", None
                            )

    def test_upload_file_with_dialog_success(self, manager):
        """Dialog와 함께 파일 업로드 성공 테스트 - Qt Mock으로 완전히 격리"""
        # JFrogManager의 Dialog 관련 메서드를 Mock으로 처리
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch.object(manager, "_create_upload_dialog") as mock_create_dialog:
                # 파일 시스템 접근도 Mock으로 처리
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_file", return_value=True):
                        mock_verify.return_value = JFrogOperationResult(success=True)

                        # Mock Dialog 객체 생성
                        mock_dialog = Mock()
                        mock_dialog.get_result.return_value = {
                            "total_uploaded": 1,
                            "uploaded_files": [{"local_path": "/test/file.txt"}],
                            "cancelled": False,
                        }
                        mock_create_dialog.return_value = mock_dialog

                        result = manager.upload_file_with_dialog(
                            "/test/file.txt", "target.txt", "test-repo", None
                        )

                        assert result.success is True
                        assert "파일 업로드 성공" in result.message
                        mock_create_dialog.assert_called_once()
                        mock_dialog.start_file_upload.assert_called_once_with(
                            "/test/file.txt", "target.txt", "test-repo"
                        )
                        mock_dialog.exec_.assert_called_once()

    def test_upload_file_with_dialog_cancelled(self, manager):
        """Dialog와 함께 파일 업로드 취소 테스트 - Qt Mock으로 완전히 격리"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch.object(manager, "_create_upload_dialog") as mock_create_dialog:
                # 파일 시스템 접근도 Mock으로 처리
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_file", return_value=True):
                        mock_verify.return_value = JFrogOperationResult(success=True)

                        mock_dialog = Mock()
                        mock_dialog.get_result.return_value = {
                            "total_uploaded": 0,
                            "cancelled": True,
                        }
                        mock_create_dialog.return_value = mock_dialog

                        result = manager.upload_file_with_dialog("/test/file.txt")

                        assert result.success is False
                        assert "업로드가 취소되었습니다" in result.message

    def test_upload_file_with_dialog_setup_failure(self, manager):
        """Dialog와 함께 파일 업로드 설정 실패 테스트"""
        with patch.object(manager, "verify_setup") as mock_verify:
            mock_verify.return_value = JFrogOperationResult(
                success=False, message="설정 오류"
            )

            result = manager.upload_file_with_dialog("/test/file.txt")

            assert result.success is False
            assert result.message == "설정 오류"

    def test_upload_directory_with_dialog_success(self, manager):
        """Dialog와 함께 디렉토리 업로드 성공 테스트 - Qt Mock으로 완전히 격리"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch.object(manager, "_create_upload_dialog") as mock_create_dialog:
                # 파일 시스템 접근도 Mock으로 처리
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_dir", return_value=True):
                        mock_verify.return_value = JFrogOperationResult(success=True)

                        mock_dialog = Mock()
                        mock_dialog.get_result.return_value = {
                            "total_uploaded": 2,
                            "uploaded_files": [
                                {"local_path": "/test/dir/file1.txt"},
                                {"local_path": "/test/dir/file2.txt"},
                            ],
                            "cancelled": False,
                        }
                        mock_create_dialog.return_value = mock_dialog

                        result = manager.upload_directory_with_dialog(
                            "/test/dir", "target", "test-repo", None
                        )

                        assert result.success is True
                        assert "디렉토리 업로드 성공" in result.message
                        mock_create_dialog.assert_called_once()
                        mock_dialog.start_directory_upload.assert_called_once_with(
                            "/test/dir", "target", "test-repo"
                        )
                        mock_dialog.exec_.assert_called_once()

    def test_upload_directory_with_dialog_failure(self, manager):
        """Dialog와 함께 디렉토리 업로드 실패 테스트 - Qt Mock으로 완전히 격리"""
        with patch.object(manager, "verify_setup") as mock_verify:
            with patch.object(manager, "_create_upload_dialog") as mock_create_dialog:
                # 파일 시스템 접근도 Mock으로 처리
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_dir", return_value=True):
                        mock_verify.return_value = JFrogOperationResult(success=True)

                        mock_dialog = Mock()
                        mock_dialog.get_result.return_value = {
                            "total_uploaded": 0,
                            "failed_files": [{"error": "Permission denied"}],
                            "cancelled": False,
                        }
                        mock_create_dialog.return_value = mock_dialog

                        result = manager.upload_directory_with_dialog("/test/dir")

                        assert result.success is False
                        assert "Permission denied" in result.message

    def test_check_jf_cli_installed(self, manager):
        """jf-cli 설치 확인 테스트"""
        with patch.object(manager.auth_manager, "check_jf_cli_installed") as mock_check:
            mock_check.return_value = True

            result = manager._check_jf_cli_installed()

            assert result is True
            mock_check.assert_called_once()

    def test_check_authentication_success(self, manager):
        """인증 확인 성공 테스트"""
        with patch.object(
            manager.auth_manager, "get_authentication_status"
        ) as mock_auth:
            mock_auth.return_value = {
                "jf_cli_installed": True,
                "server_configured": True,
                "authenticated": True,
            }

            result = manager._check_authentication()

            assert result.success is True
            assert "인증 상태 확인 완료" in result.message

    def test_check_authentication_not_installed(self, manager):
        """jf-cli 설치되지 않았을 때 인증 확인 테스트"""
        with patch.object(
            manager.auth_manager, "get_authentication_status"
        ) as mock_auth:
            mock_auth.return_value = {
                "jf_cli_installed": False,
                "server_configured": False,
                "authenticated": False,
            }

            result = manager._check_authentication()

            assert result.success is False
            assert "jf-cli가 설치되지 않았습니다" in result.message

    def test_check_authentication_not_configured(self, manager):
        """서버 설정되지 않았을 때 인증 확인 테스트"""
        with patch.object(
            manager.auth_manager, "get_authentication_status"
        ) as mock_auth:
            mock_auth.return_value = {
                "jf_cli_installed": True,
                "server_configured": False,
                "authenticated": False,
            }

            result = manager._check_authentication()

            assert result.success is False
            assert "JFrog에 먼저 로그인이 필요합니다" in result.message

    def test_check_authentication_failed(self, manager):
        """인증 실패 테스트"""
        with patch.object(
            manager.auth_manager, "get_authentication_status"
        ) as mock_auth:
            mock_auth.return_value = {
                "jf_cli_installed": True,
                "server_configured": True,
                "authenticated": False,
            }

            result = manager._check_authentication()

            assert result.success is False
            assert "JFrog 인증에 실패했습니다" in result.message

    def test_check_permissions_success(self, manager):
        """권한 확인 성공 테스트"""
        with patch.object(
            manager.permission_checker, "get_permission_status"
        ) as mock_perm:
            mock_perm.return_value = {
                "authenticated": True,
                "permissions": {
                    "exists": True,
                    "upload_permission": True,
                    "repository": "test-repo",
                },
            }

            result = manager._check_permissions()

            assert result.success is True
            assert "리포지토리 권한 확인 완료" in result.message

    def test_check_permissions_not_authenticated(self, manager):
        """인증되지 않았을 때 권한 확인 테스트"""
        with patch.object(
            manager.permission_checker, "get_permission_status"
        ) as mock_perm:
            mock_perm.return_value = {"authenticated": False, "permissions": {}}

            result = manager._check_permissions()

            assert result.success is False
            assert "JFrog 인증이 필요합니다" in result.message

    def test_check_permissions_repo_not_exists(self, manager):
        """리포지토리가 없을 때 권한 확인 테스트"""
        with patch.object(
            manager.permission_checker, "get_permission_status"
        ) as mock_perm:
            mock_perm.return_value = {
                "authenticated": True,
                "permissions": {
                    "exists": False,
                    "upload_permission": False,
                    "repository": "test-repo",
                },
            }

            result = manager._check_permissions()

            assert result.success is False
            assert "리포지토리를 찾을 수 없습니다" in result.message

    def test_check_permissions_no_upload_permission(self, manager):
        """업로드 권한이 없을 때 테스트"""
        with patch.object(
            manager.permission_checker, "get_permission_status"
        ) as mock_perm:
            mock_perm.return_value = {
                "authenticated": True,
                "permissions": {
                    "exists": True,
                    "upload_permission": False,
                    "repository": "test-repo",
                },
            }

            result = manager._check_permissions()

            assert result.success is False
            assert "업로드 권한이 없습니다" in result.message


class TestJFrogOperationResult:
    """JFrogOperationResult 데이터클래스 테스트"""

    def test_operation_result_creation(self):
        """JFrogOperationResult 생성 테스트"""
        result = JFrogOperationResult(
            success=True, message="성공", data={"key": "value"}, error=None
        )

        assert result.success is True
        assert result.message == "성공"
        assert result.data["key"] == "value"
        assert result.error is None

    def test_operation_result_defaults(self):
        """JFrogOperationResult 기본값 테스트"""
        result = JFrogOperationResult(success=False)

        assert result.success is False
        assert result.message == ""
        assert result.data == {}
        assert result.error is None

    def test_operation_result_post_init(self):
        """JFrogOperationResult post_init 테스트"""
        result = JFrogOperationResult(success=True, data=None)

        assert result.data == {}
