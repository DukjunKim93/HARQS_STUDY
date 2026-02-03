#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""JFrogPermissionChecker 단위 테스트"""

import pytest
import subprocess
import tempfile
import os
import json
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.JFrogPermissionChecker import (
    JFrogPermissionChecker,
    JFrogRepositoryInfo,
)
from QSUtils.JFrogUtils.exceptions import (
    JFrogRepositoryNotFoundError,
    JFrogPermissionDeniedError,
    JFrogAccessDeniedError,
    JFrogNetworkError,
    JFrogConfigurationError,
)


class TestJFrogPermissionChecker:
    """JFrogPermissionChecker 클래스 테스트"""

    @pytest.fixture
    def config(self):
        """JFrogConfig fixture"""
        return JFrogConfig()

    @pytest.fixture
    def permission_checker(self, config):
        """JFrogPermissionChecker fixture"""
        return JFrogPermissionChecker(config)

    def test_initialization(self, config):
        """JFrogPermissionChecker 초기화 테스트"""
        checker = JFrogPermissionChecker(config)
        assert checker.config == config
        assert checker.logger is not None
        assert checker.auth_manager is not None

    def test_check_repository_exists_success(self, permission_checker):
        """리포지토리 존재 확인 성공 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout='{"key": "test-repo"}', stderr=""
            )

            result = permission_checker.check_repository_exists("test-repo")

            assert result is True
            mock_run.assert_called_once_with(
                ["jf", "rt", "curl", "-XGET", "/api/repositories/test-repo"],
                capture_output=True,
                text=True,
                timeout=30,
            )

    def test_check_repository_exists_failure(self, permission_checker):
        """리포지토리 존재 확인 실패 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Repository not found"
            )

            result = permission_checker.check_repository_exists("test-repo")

            assert result is False

    def test_check_repository_exists_timeout(self, permission_checker):
        """리포지토리 존재 확인 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("jf", 30)

            result = permission_checker.check_repository_exists("test-repo")

            assert result is False

    def test_check_repository_exists_default_repo(self, permission_checker):
        """리포지토리 존재 확인 - 기본 리포지토리 사용 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"key": "oneos-qsymphony-issues-generic-local"}',
                stderr="",
            )

            result = permission_checker.check_repository_exists()

            assert result is True
            mock_run.assert_called_once_with(
                [
                    "jf",
                    "rt",
                    "curl",
                    "-XGET",
                    "/api/repositories/oneos-qsymphony-issues-generic-local",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

    def test_get_repository_info_success(self, permission_checker):
        """리포지토리 정보 가져오기 성공 테스트"""
        repo_data = {
            "key": "test-repo",
            "rclass": "local",
            "packageType": "generic",
            "description": "Test repository",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps(repo_data), stderr=""
            )

            result = permission_checker.get_repository_info("test-repo")

            assert result is not None
            assert result.repo_key == "test-repo"
            assert result.repo_type == "local"
            assert result.package_type == "generic"
            assert result.description == "Test repository"

    def test_get_repository_info_failure(self, permission_checker):
        """리포지토리 정보 가져오기 실패 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Repository not found"
            )

            result = permission_checker.get_repository_info("test-repo")

            assert result is None

    def test_get_repository_info_json_error(self, permission_checker):
        """리포지토리 정보 가져오기 JSON 파싱 실패 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="invalid json", stderr="")

            result = permission_checker.get_repository_info("test-repo")

            assert result is None

    def test_get_repository_info_timeout(self, permission_checker):
        """리포지토리 정보 가져오기 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("jf", 30)

            result = permission_checker.get_repository_info("test-repo")

            assert result is None

    def test_test_upload_permission_success(self, permission_checker):
        """업로드 권한 테스트 성공 테스트"""
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            with patch("subprocess.run") as mock_run:
                with patch("os.unlink") as mock_unlink:
                    # Mock temporary file
                    mock_file = Mock()
                    mock_file.name = "/tmp/test_file.txt"
                    mock_temp_file.return_value.__enter__.return_value = mock_file

                    # Mock upload and delete commands
                    mock_run.side_effect = [
                        Mock(
                            returncode=0, stdout="Upload successful", stderr=""
                        ),  # upload
                        Mock(
                            returncode=0, stdout="Delete successful", stderr=""
                        ),  # delete
                    ]

                    result = permission_checker.test_upload_permission("test-repo")

                    assert result is True
                    assert mock_run.call_count == 2
                    mock_unlink.assert_called_once_with("/tmp/test_file.txt")

    def test_test_upload_permission_upload_failure(self, permission_checker):
        """업로드 권한 테스트 업로드 실패 테스트"""
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            with patch("subprocess.run") as mock_run:
                with patch("os.unlink") as mock_unlink:
                    # Mock temporary file
                    mock_file = Mock()
                    mock_file.name = "/tmp/test_file.txt"
                    mock_temp_file.return_value.__enter__.return_value = mock_file

                    # Mock upload failure
                    mock_run.return_value = Mock(
                        returncode=1, stdout="", stderr="Permission denied"
                    )

                    result = permission_checker.test_upload_permission("test-repo")

                    assert result is False
                    mock_unlink.assert_called_once_with("/tmp/test_file.txt")

    def test_test_upload_permission_timeout(self, permission_checker):
        """업로드 권한 테스트 타임아웃 테스트"""
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            with patch("subprocess.run") as mock_run:
                with patch("os.unlink") as mock_unlink:
                    # Mock temporary file
                    mock_file = Mock()
                    mock_file.name = "/tmp/test_file.txt"
                    mock_temp_file.return_value.__enter__.return_value = mock_file

                    # Mock timeout
                    mock_run.side_effect = subprocess.TimeoutExpired("jf", 60)

                    result = permission_checker.test_upload_permission("test-repo")

                    assert result is False
                    mock_unlink.assert_called_once_with("/tmp/test_file.txt")

    def test_test_upload_permission_default_repo(self, permission_checker):
        """업로드 권한 테스트 - 기본 리포지토리 사용 테스트"""
        with patch("tempfile.NamedTemporaryFile") as mock_temp_file:
            with patch("subprocess.run") as mock_run:
                with patch("os.unlink") as mock_unlink:
                    # Mock temporary file
                    mock_file = Mock()
                    mock_file.name = "/tmp/test_file.txt"
                    mock_temp_file.return_value.__enter__.return_value = mock_file

                    # Mock upload and delete commands
                    mock_run.side_effect = [
                        Mock(
                            returncode=0, stdout="Upload successful", stderr=""
                        ),  # upload
                        Mock(
                            returncode=0, stdout="Delete successful", stderr=""
                        ),  # delete
                    ]

                    result = permission_checker.test_upload_permission()

                    assert result is True
                    # Check that default repo is used by verifying the call was made
                    # The actual target_path is constructed inside the method, so we just verify the call happened
                    assert mock_run.call_count == 2

    def test_check_read_permission_success(self, permission_checker):
        """읽기 권한 확인 성공 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout='{"files": []}', stderr=""
            )

            result = permission_checker.check_read_permission("test-repo")

            assert result is True
            mock_run.assert_called_once_with(
                ["jf", "rt", "curl", "-XGET", "/api/storage/test-repo"],
                capture_output=True,
                text=True,
                timeout=30,
            )

    def test_check_read_permission_failure(self, permission_checker):
        """읽기 권한 확인 실패 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Access denied"
            )

            result = permission_checker.check_read_permission("test-repo")

            assert result is False

    def test_check_read_permission_timeout(self, permission_checker):
        """읽기 권한 확인 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("jf", 30)

            result = permission_checker.check_read_permission("test-repo")

            assert result is False

    def test_check_permissions_success(self, permission_checker):
        """종합 권한 확인 성공 테스트"""
        with patch.object(
            permission_checker, "check_repository_exists", return_value=True
        ):
            with patch.object(
                permission_checker, "get_repository_info"
            ) as mock_get_info:
                with patch.object(
                    permission_checker, "check_read_permission", return_value=True
                ):
                    with patch.object(
                        permission_checker, "test_upload_permission", return_value=True
                    ):
                        mock_get_info.return_value = JFrogRepositoryInfo(
                            repo_key="test-repo",
                            repo_type="local",
                            package_type="generic",
                            description="Test repo",
                        )

                        result = permission_checker.check_permissions("test-repo")

                        assert result["repository"] == "test-repo"
                        assert result["exists"] is True
                        assert result["read_permission"] is True
                        assert result["upload_permission"] is True
                        assert result["repository_info"] is not None
                        assert result["repository_info"].repo_key == "test-repo"
                        assert len(result["errors"]) == 0

    def test_check_permissions_repo_not_exists(self, permission_checker):
        """종합 권한 확인 - 리포지토리 없음 테스트"""
        with patch.object(
            permission_checker, "check_repository_exists", return_value=False
        ):
            result = permission_checker.check_permissions("test-repo")

            assert result["repository"] == "test-repo"
            assert result["exists"] is False
            assert result["read_permission"] is False
            assert result["upload_permission"] is False
            assert result["repository_info"] is None
            assert "리포지토리를 찾을 수 없습니다: test-repo" in result["errors"]

    def test_check_permissions_read_permission_denied(self, permission_checker):
        """종합 권한 확인 - 읽기 권한 없음 테스트"""
        with patch.object(
            permission_checker, "check_repository_exists", return_value=True
        ):
            with patch.object(
                permission_checker, "get_repository_info"
            ) as mock_get_info:
                with patch.object(
                    permission_checker, "check_read_permission", return_value=False
                ):
                    with patch.object(
                        permission_checker, "test_upload_permission", return_value=True
                    ):
                        mock_get_info.return_value = JFrogRepositoryInfo(
                            repo_key="test-repo",
                            repo_type="local",
                            package_type="generic",
                            description="Test repo",
                        )

                        result = permission_checker.check_permissions("test-repo")

                        assert result["exists"] is True
                        assert result["read_permission"] is False
                        assert result["upload_permission"] is True
                        assert (
                            "리포지토리 읽기 권한이 없습니다: test-repo"
                            in result["errors"]
                        )

    def test_check_permissions_upload_permission_denied(self, permission_checker):
        """종합 권한 확인 - 업로드 권한 없음 테스트"""
        with patch.object(
            permission_checker, "check_repository_exists", return_value=True
        ):
            with patch.object(
                permission_checker, "get_repository_info"
            ) as mock_get_info:
                with patch.object(
                    permission_checker, "check_read_permission", return_value=True
                ):
                    with patch.object(
                        permission_checker, "test_upload_permission", return_value=False
                    ):
                        mock_get_info.return_value = JFrogRepositoryInfo(
                            repo_key="test-repo",
                            repo_type="local",
                            package_type="generic",
                            description="Test repo",
                        )

                        result = permission_checker.check_permissions("test-repo")

                        assert result["exists"] is True
                        assert result["read_permission"] is True
                        assert result["upload_permission"] is False
                        assert (
                            "리포지토리 업로드 권한이 없습니다: test-repo"
                            in result["errors"]
                        )

    def test_verify_upload_permissions_success(self, permission_checker):
        """업로드 권한 확인 성공 테스트"""
        with patch.object(
            permission_checker, "check_repository_exists", return_value=True
        ):
            with patch.object(
                permission_checker, "test_upload_permission", return_value=True
            ):
                result = permission_checker.verify_upload_permissions("test-repo")

                assert result is True

    def test_verify_upload_permissions_repo_not_exists(self, permission_checker):
        """업로드 권한 확인 - 리포지토리 없음 테스트"""
        with patch.object(
            permission_checker, "check_repository_exists", return_value=False
        ):
            with pytest.raises(JFrogRepositoryNotFoundError) as exc_info:
                permission_checker.verify_upload_permissions("test-repo")

            assert "test-repo" in str(exc_info.value)

    def test_verify_upload_permissions_permission_denied(self, permission_checker):
        """업로드 권한 확인 - 권한 없음 테스트"""
        with patch.object(
            permission_checker, "check_repository_exists", return_value=True
        ):
            with patch.object(
                permission_checker, "test_upload_permission", return_value=False
            ):
                with pytest.raises(JFrogPermissionDeniedError) as exc_info:
                    permission_checker.verify_upload_permissions("test-repo")

            assert "test-repo" in str(exc_info.value)
            assert "업로드" in str(exc_info.value)

    def test_get_permission_status_success(self, permission_checker):
        """전체 권한 상태 정보 가져오기 성공 테스트"""
        auth_status = {"authenticated": True, "server_accessible": True, "errors": []}

        perm_result = {
            "repository": "test-repo",
            "exists": True,
            "read_permission": True,
            "upload_permission": True,
            "repository_info": None,
            "errors": [],
        }

        with patch.object(
            permission_checker.auth_manager,
            "get_authentication_status",
            return_value=auth_status,
        ):
            with patch.object(
                permission_checker, "check_permissions", return_value=perm_result
            ):
                result = permission_checker.get_permission_status("test-repo")

                assert result["repository"] == "test-repo"
                assert result["authenticated"] is True
                assert result["server_accessible"] is True
                assert result["permissions"] == perm_result
                assert len(result["errors"]) == 0

    def test_get_permission_status_not_authenticated(self, permission_checker):
        """전체 권한 상태 정보 가져오기 - 인증되지 않음 테스트"""
        auth_status = {
            "authenticated": False,
            "server_accessible": False,
            "errors": ["Authentication failed"],
        }

        with patch.object(
            permission_checker.auth_manager,
            "get_authentication_status",
            return_value=auth_status,
        ):
            result = permission_checker.get_permission_status("test-repo")

            assert result["authenticated"] is False
            assert result["server_accessible"] is False
            assert result["permissions"] == {}
            assert result["errors"] == ["Authentication failed"]

    def test_get_permission_status_exception(self, permission_checker):
        """전체 권한 상태 정보 가져오기 - 예외 발생 테스트"""
        with patch.object(
            permission_checker.auth_manager,
            "get_authentication_status",
            side_effect=Exception("Test error"),
        ):
            result = permission_checker.get_permission_status("test-repo")

            assert result["repository"] == "test-repo"
            assert result["authenticated"] is False
            assert result["server_accessible"] is False
            assert result["permissions"] == {}
            assert "권한 상태 확인 중 오류: Test error" in result["errors"]


class TestJFrogRepositoryInfo:
    """JFrogRepositoryInfo 데이터클래스 테스트"""

    def test_repository_info_creation(self):
        """JFrogRepositoryInfo 생성 테스트"""
        info = JFrogRepositoryInfo(
            repo_key="test-repo",
            repo_type="local",
            package_type="generic",
            description="Test repository",
            url="https://example.com/artifactory/test-repo",
        )

        assert info.repo_key == "test-repo"
        assert info.repo_type == "local"
        assert info.package_type == "generic"
        assert info.description == "Test repository"
        assert info.url == "https://example.com/artifactory/test-repo"

    def test_repository_info_defaults(self):
        """JFrogRepositoryInfo 기본값 테스트"""
        info = JFrogRepositoryInfo(
            repo_key="test-repo",
            repo_type="local",
            package_type="generic",
            description="Test repository",
        )

        assert info.url is None
