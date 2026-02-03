#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""JFrogAuthManager 단위 테스트"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.JFrogAuthManager import JFrogAuthManager, JFrogServerConfig
from QSUtils.JFrogUtils.exceptions import (
    JFrogNotInstalledError,
    JFrogConfigurationError,
    JFrogNetworkError,
)


class TestJFrogAuthManager:
    """JFrogAuthManager 클래스 테스트"""

    @pytest.fixture
    def config(self):
        """JFrogConfig fixture"""
        return JFrogConfig()

    @pytest.fixture
    def auth_manager(self, config):
        """JFrogAuthManager fixture"""
        return JFrogAuthManager(config)

    def test_initialization(self, config):
        """JFrogAuthManager 초기화 테스트"""
        auth_manager = JFrogAuthManager(config)
        assert auth_manager.config == config
        assert auth_manager.logger is not None

    def test_check_jf_cli_installed_success(self, auth_manager):
        """jf-cli 설치 확인 성공 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="jf version 2.0.0", stderr=""
            )

            result = auth_manager.check_jf_cli_installed()

            assert result is True
            mock_run.assert_called_once_with(
                ["jf", "--version"], capture_output=True, text=True, timeout=10
            )

    def test_check_jf_cli_installed_not_found(self, auth_manager):
        """jf-cli 설치 확인 - 명령어 없음 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = auth_manager.check_jf_cli_installed()

            assert result is False

    def test_check_jf_cli_installed_timeout(self, auth_manager):
        """jf-cli 설치 확인 - 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("jf", 10)

            result = auth_manager.check_jf_cli_installed()

            assert result is False

    def test_check_jf_cli_installed_return_code_nonzero(self, auth_manager):
        """jf-cli 설치 확인 - 반환 코드 비정상 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Command not found"
            )

            result = auth_manager.check_jf_cli_installed()

            assert result is False

    def test_get_server_configs_success(self, auth_manager):
        """서버 설정 정보 가져오기 성공 테스트"""
        config_output = """Server ID: bart.sec.samsung.net
JFrog Platform URL:		https://bart.sec.samsung.net/
Artifactory URL:		https://bart.sec.samsung.net/artifactory/
Distribution URL:		https://bart.sec.samsung.net/distribution/
Xray URL:			https://bart.sec.samsung.net/xray/
Mission Control URL:		https://bart.sec.samsung.net/mc/
Pipelines URL:			https://bart.sec.samsung.net/pipelines/
User:				walyong.cho
Access token:			***
Refresh token:			***
Default:			true"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=config_output, stderr="")

            configs = auth_manager.get_server_configs()

            assert "bart.sec.samsung.net" in configs
            config = configs["bart.sec.samsung.net"]
            assert config.server_id == "bart.sec.samsung.net"
            assert config.url == "https://bart.sec.samsung.net/"
            assert config.artifactory_url == "https://bart.sec.samsung.net/artifactory/"
            assert config.user == "walyong.cho"
            assert config.is_default is True
            assert config.access_token is None  # ***는 None로 처리됨

    def test_get_server_configs_command_failure(self, auth_manager):
        """서버 설정 정보 가져오기 - 명령어 실패 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Configuration error"
            )

            with pytest.raises(JFrogConfigurationError):
                auth_manager.get_server_configs()

    def test_get_server_configs_timeout(self, auth_manager):
        """서버 설정 정보 가져오기 - 타임아웃 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("jf", 30)

            with pytest.raises(JFrogNetworkError):
                auth_manager.get_server_configs()

    def test_get_server_configs_jf_not_installed(self, auth_manager):
        """서버 설정 정보 가져오기 - jf-cli 미설치 테스트"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with pytest.raises(JFrogNotInstalledError):
                auth_manager.get_server_configs()

    def test_get_target_server_config_found(self, auth_manager):
        """대상 서버 설정 정보 찾기 성공 테스트"""
        mock_configs = {
            "bart.sec.samsung.net": JFrogServerConfig(
                server_id="bart.sec.samsung.net",
                url="https://bart.sec.samsung.net/",
                artifactory_url="https://bart.sec.samsung.net/artifactory/",
                user="test_user",
                is_default=True,
            )
        }

        with patch.object(
            auth_manager, "get_server_configs", return_value=mock_configs
        ):
            result = auth_manager.get_target_server_config()

            assert result is not None
            assert result.server_id == "bart.sec.samsung.net"
            assert result.user == "test_user"

    def test_get_target_server_config_not_found(self, auth_manager):
        """대상 서버 설정 정보 찾기 실패 테스트"""
        mock_configs = {
            "other.server.com": JFrogServerConfig(
                server_id="other.server.com",
                url="https://other.server.com/",
                artifactory_url="https://other.server.com/artifactory/",
                user="other_user",
                is_default=False,
            )
        }

        with patch.object(
            auth_manager, "get_server_configs", return_value=mock_configs
        ):
            result = auth_manager.get_target_server_config()

            assert result is None

    def test_verify_authentication_success(self, auth_manager):
        """인증 상태 확인 성공 테스트"""
        mock_server_config = JFrogServerConfig(
            server_id="bart.sec.samsung.net",
            url="https://bart.sec.samsung.net/",
            artifactory_url="https://bart.sec.samsung.net/artifactory/",
            user="test_user",
            is_default=True,
        )

        with patch.object(
            auth_manager, "get_target_server_config", return_value=mock_server_config
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="OK", stderr="")

                result = auth_manager.verify_authentication()

                assert result is True
                mock_run.assert_called_once_with(
                    ["jf", "rt", "ping"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

    def test_verify_authentication_no_server_config(self, auth_manager):
        """인증 상태 확인 - 서버 설정 없음 테스트"""
        with patch.object(auth_manager, "get_target_server_config", return_value=None):
            result = auth_manager.verify_authentication()

            assert result is False

    def test_verify_authentication_ping_failure(self, auth_manager):
        """인증 상태 확인 - ping 실패 테스트"""
        mock_server_config = JFrogServerConfig(
            server_id="bart.sec.samsung.net",
            url="https://bart.sec.samsung.net/",
            artifactory_url="https://bart.sec.samsung.net/artifactory/",
            user="test_user",
            is_default=True,
        )

        with patch.object(
            auth_manager, "get_target_server_config", return_value=mock_server_config
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=1, stdout="", stderr="Authentication failed"
                )

                result = auth_manager.verify_authentication()

                assert result is False

    def test_verify_authentication_timeout(self, auth_manager):
        """인증 상태 확인 - 타임아웃 테스트"""
        mock_server_config = JFrogServerConfig(
            server_id="bart.sec.samsung.net",
            url="https://bart.sec.samsung.net/",
            artifactory_url="https://bart.sec.samsung.net/artifactory/",
            user="test_user",
            is_default=True,
        )

        with patch.object(
            auth_manager, "get_target_server_config", return_value=mock_server_config
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("jf", 30)

                result = auth_manager.verify_authentication()

                assert result is False

    def test_check_server_access_success(self, auth_manager):
        """서버 접근 확인 성공 테스트"""
        mock_server_config = JFrogServerConfig(
            server_id="bart.sec.samsung.net",
            url="https://bart.sec.samsung.net/",
            artifactory_url="https://bart.sec.samsung.net/artifactory/",
            user="test_user",
            is_default=True,
        )

        with patch.object(
            auth_manager, "get_target_server_config", return_value=mock_server_config
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0, stdout='{"version": "1.0.0"}', stderr=""
                )

                result = auth_manager.check_server_access()

                assert result is True
                mock_run.assert_called_once_with(
                    ["jf", "rt", "curl", "-XGET", "/api/system/version"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

    def test_check_server_access_no_server_config(self, auth_manager):
        """서버 접근 확인 - 서버 설정 없음 테스트"""
        with patch.object(auth_manager, "get_target_server_config", return_value=None):
            result = auth_manager.check_server_access()

            assert result is False

    def test_check_server_access_failure(self, auth_manager):
        """서버 접근 확인 실패 테스트"""
        mock_server_config = JFrogServerConfig(
            server_id="bart.sec.samsung.net",
            url="https://bart.sec.samsung.net/",
            artifactory_url="https://bart.sec.samsung.net/artifactory/",
            user="test_user",
            is_default=True,
        )

        with patch.object(
            auth_manager, "get_target_server_config", return_value=mock_server_config
        ):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=1, stdout="", stderr="Access denied"
                )

                result = auth_manager.check_server_access()

                assert result is False

    def test_parse_config_show_output_single_server(self, auth_manager):
        """config show 출력 파싱 - 단일 서버 테스트"""
        output = """Server ID: test.server.com
JFrog Platform URL:		https://test.server.com/
Artifactory URL:		https://test.server.com/artifactory/
User:				testuser
Default:			false"""

        configs = auth_manager._parse_config_show_output(output)

        assert "test.server.com" in configs
        config = configs["test.server.com"]
        assert config.server_id == "test.server.com"
        assert config.url == "https://test.server.com/"
        assert config.artifactory_url == "https://test.server.com/artifactory/"
        assert config.user == "testuser"
        assert config.is_default is False

    def test_parse_config_show_output_multiple_servers(self, auth_manager):
        """config show 출력 파싱 - 여러 서버 테스트"""
        output = """Server ID: server1.com
JFrog Platform URL:		https://server1.com/
Artifactory URL:		https://server1.com/artifactory/
User:				user1
Default:			true
Server ID: server2.com
JFrog Platform URL:		https://server2.com/
Artifactory URL:		https://server2.com/artifactory/
User:				user2
Default:			false"""

        configs = auth_manager._parse_config_show_output(output)

        assert len(configs) == 2
        assert "server1.com" in configs
        assert "server2.com" in configs
        assert configs["server1.com"].is_default is True
        assert configs["server2.com"].is_default is False

    def test_parse_config_show_output_empty(self, auth_manager):
        """config show 출력 파싱 - 빈 출력 테스트"""
        output = ""

        configs = auth_manager._parse_config_show_output(output)

        assert len(configs) == 0

    def test_get_authentication_status_full_success(self, auth_manager):
        """전체 인증 상태 정보 가져오기 - 완전 성공 테스트"""
        with patch.object(auth_manager, "check_jf_cli_installed", return_value=True):
            with patch.object(
                auth_manager, "get_target_server_config"
            ) as mock_get_config:
                mock_server_config = JFrogServerConfig(
                    server_id="bart.sec.samsung.net",
                    url="https://bart.sec.samsung.net/",
                    artifactory_url="https://bart.sec.samsung.net/artifactory/",
                    user="test_user",
                    is_default=True,
                )
                mock_get_config.return_value = mock_server_config

                with patch.object(
                    auth_manager, "verify_authentication", return_value=True
                ):
                    with patch.object(
                        auth_manager, "check_server_access", return_value=True
                    ):
                        status = auth_manager.get_authentication_status()

                        assert status["jf_cli_installed"] is True
                        assert status["server_configured"] is True
                        assert status["authenticated"] is True
                        assert status["server_accessible"] is True
                        assert status["server_info"] is not None
                        assert (
                            status["server_info"]["server_id"] == "bart.sec.samsung.net"
                        )
                        assert status["server_info"]["user"] == "test_user"
                        assert len(status["errors"]) == 0

    def test_get_authentication_status_jf_not_installed(self, auth_manager):
        """전체 인증 상태 정보 가져오기 - jf-cli 미설치 테스트"""
        with patch.object(auth_manager, "check_jf_cli_installed", return_value=False):
            status = auth_manager.get_authentication_status()

            assert status["jf_cli_installed"] is False
            assert status["server_configured"] is False
            assert status["authenticated"] is False
            assert status["server_accessible"] is False
            assert status["server_info"] is None
            assert "jf-cli가 설치되지 않았습니다." in status["errors"]

    def test_get_authentication_status_server_not_configured(self, auth_manager):
        """전체 인증 상태 정보 가져오기 - 서버 설정 없음 테스트"""
        with patch.object(auth_manager, "check_jf_cli_installed", return_value=True):
            with patch.object(
                auth_manager, "get_target_server_config", return_value=None
            ):
                status = auth_manager.get_authentication_status()

                assert status["jf_cli_installed"] is True
                assert status["server_configured"] is False
                assert status["authenticated"] is False
                assert status["server_accessible"] is False
                assert status["server_info"] is None
                assert "대상 서버 설정을 찾을 수 없습니다." in status["errors"]

    def test_get_authentication_status_authentication_failed(self, auth_manager):
        """전체 인증 상태 정보 가져오기 - 인증 실패 테스트"""
        with patch.object(auth_manager, "check_jf_cli_installed", return_value=True):
            with patch.object(
                auth_manager, "get_target_server_config"
            ) as mock_get_config:
                mock_server_config = JFrogServerConfig(
                    server_id="bart.sec.samsung.net",
                    url="https://bart.sec.samsung.net/",
                    artifactory_url="https://bart.sec.samsung.net/artifactory/",
                    user="test_user",
                    is_default=True,
                )
                mock_get_config.return_value = mock_server_config

                with patch.object(
                    auth_manager, "verify_authentication", return_value=False
                ):
                    status = auth_manager.get_authentication_status()

                    assert status["jf_cli_installed"] is True
                    assert status["server_configured"] is True
                    assert status["authenticated"] is False
                    assert status["server_accessible"] is False
                    assert status["server_info"] is not None
                    assert "JFrog 인증에 실패했습니다." in status["errors"]

    def test_get_authentication_status_exception(self, auth_manager):
        """전체 인증 상태 정보 가져오기 - 예외 발생 테스트"""
        with patch.object(
            auth_manager, "check_jf_cli_installed", side_effect=Exception("Test error")
        ):
            status = auth_manager.get_authentication_status()

            assert status["jf_cli_installed"] is False
            assert status["server_configured"] is False
            assert status["authenticated"] is False
            assert status["server_accessible"] is False
            assert status["server_info"] is None
            assert "인증 상태 확인 중 오류: Test error" in status["errors"]


class TestJFrogServerConfig:
    """JFrogServerConfig 데이터클래스 테스트"""

    def test_server_config_creation(self):
        """JFrogServerConfig 생성 테스트"""
        config = JFrogServerConfig(
            server_id="test.server.com",
            url="https://test.server.com/",
            artifactory_url="https://test.server.com/artifactory/",
            user="testuser",
            is_default=True,
            access_token="test_token",
            refresh_token="refresh_token",
        )

        assert config.server_id == "test.server.com"
        assert config.url == "https://test.server.com/"
        assert config.artifactory_url == "https://test.server.com/artifactory/"
        assert config.user == "testuser"
        assert config.is_default is True
        assert config.access_token == "test_token"
        assert config.refresh_token == "refresh_token"

    def test_server_config_defaults(self):
        """JFrogServerConfig 기본값 테스트"""
        config = JFrogServerConfig(
            server_id="test.server.com",
            url="https://test.server.com/",
            artifactory_url="https://test.server.com/artifactory/",
            user="testuser",
        )

        assert config.is_default is False
        assert config.access_token is None
        assert config.refresh_token is None
