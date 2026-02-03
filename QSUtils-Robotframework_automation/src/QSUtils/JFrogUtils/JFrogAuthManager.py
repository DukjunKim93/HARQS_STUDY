#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrog 인증 관리

jf-cli 설치 확인 및 인증 상태를 관리합니다.
"""

import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.exceptions import (
    JFrogNotInstalledError,
    JFrogConfigurationError,
    JFrogNetworkError,
)
from QSUtils.Utils.Logger import get_logger


@dataclass
class JFrogServerConfig:
    """JFrog 서버 설정 정보"""

    server_id: str
    url: str
    artifactory_url: str
    user: str
    is_default: bool = False
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class JFrogAuthManager:
    """JFrog 인증 관리 클래스"""

    def __init__(self, config: JFrogConfig):
        """
        JFrogAuthManager 초기화

        Args:
            config: JFrog 설정 객체
        """
        self.config = config
        self.logger = get_logger()

    def check_jf_cli_installed(self) -> bool:
        """
        jf-cli 설치 확인

        Returns:
            bool: 설치되어 있으면 True
        """
        try:
            result = subprocess.run(
                ["jf", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.logger.info(f"jf-cli 설치 확인: {result.stdout.strip()}")
                return True
            else:
                self.logger.error(f"jf-cli 버전 확인 실패: {result.stderr}")
                return False
        except FileNotFoundError:
            self.logger.error("jf-cli 명령어를 찾을 수 없습니다.")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("jf-cli 버전 확인 타임아웃")
            return False
        except Exception as e:
            self.logger.error(f"jf-cli 설치 확인 중 오류 발생: {e}")
            return False

    def get_server_configs(self) -> Dict[str, JFrogServerConfig]:
        """
        `jf config show` 명령어로 서버 설정 정보 가져오기

        Returns:
            Dict[str, JFrogServerConfig]: 서버 ID를 키로 하는 서버 설정 정보
        """
        try:
            result = subprocess.run(
                ["jf", "config", "show"], capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self.logger.error(f"jf config show 실패: {result.stderr}")
                raise JFrogConfigurationError(f"설정 확인 실패: {result.stderr}")

            return self._parse_config_show_output(result.stdout)

        except subprocess.TimeoutExpired:
            self.logger.error("jf config show 타임아웃")
            raise JFrogNetworkError("jf config show 타임아웃")
        except FileNotFoundError:
            self.logger.error("jf-cli 명령어를 찾을 수 없습니다.")
            raise JFrogNotInstalledError()
        except Exception as e:
            self.logger.error(f"서버 설정 확인 중 오류 발생: {e}")
            raise JFrogConfigurationError(f"서버 설정 확인 중 오류: {str(e)}")

    def get_target_server_config(self) -> Optional[JFrogServerConfig]:
        """
        대상 서버(bart.sec.samsung.net) 설정 정보 가져오기

        Returns:
            Optional[JFrogServerConfig]: 대상 서버 설정 정보 (없으면 None)
        """
        configs = self.get_server_configs()

        # 서버 ID로 직접 확인
        target_server_id = "bart.sec.samsung.net"
        if target_server_id in configs:
            return configs[target_server_id]

        # URL로 확인
        for config in configs.values():
            if target_server_id in config.url:
                return config

        return None

    def verify_authentication(self) -> bool:
        """
        인증 상태 확인 (`jf rt ping`)
        Returns:
            bool: 인증되어 있으면 True
        """
        try:
            # 대상 서버 설정 확인
            server_config = self.get_target_server_config()
            if not server_config:
                self.logger.error("대상 서버 설정을 찾을 수 없습니다.")
                return False

            # 기본 ping 테스트 (서버 ID 지정 없이)
            # 최신 JFrog CLI 버전에서는 --server 플래그가 지원되지 않을 수 있음
            cmd = ["jf", "rt", "ping"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.logger.info("JFrog 인증 상태 확인 성공")
                return True
            else:
                self.logger.error(f"JFrog 인증 실패: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("jf rt ping 타임아웃")
            return False
        except Exception as e:
            self.logger.error(f"인증 확인 중 오류 발생: {e}")
            return False

    def check_server_access(self) -> bool:
        """
        대상 서버 접근 가능 여부 확인

        Returns:
            bool: 접근 가능하면 True
        """
        try:
            server_config = self.get_target_server_config()
            if not server_config:
                return False

            # Artifactory URL에 접근 테스트
            result = subprocess.run(
                ["jf", "rt", "curl", "-XGET", "/api/system/version"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"서버 접근 확인 중 오류 발생: {e}")
            return False

    def _parse_config_show_output(self, output: str) -> Dict[str, JFrogServerConfig]:
        """
        `jf config show` 출력 파싱

        Args:
            output: jf config show 명령어 출력

        Returns:
            Dict[str, JFrogServerConfig]: 파싱된 서버 설정 정보
        """
        configs = {}
        current_server = None

        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()

            # 새 서버 섹션 시작
            if line.startswith("Server ID:"):
                if current_server:
                    # 이전 서버 저장
                    configs[current_server.server_id] = current_server

                server_id = line.split(":", 1)[1].strip()
                current_server = JFrogServerConfig(
                    server_id=server_id, url="", artifactory_url="", user=""
                )

            # 서버 설정 정보 파싱
            elif current_server and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "JFrog Platform URL":
                    current_server.url = value
                elif key == "Artifactory URL":
                    current_server.artifactory_url = value
                elif key == "User":
                    current_server.user = value
                elif key == "Default":
                    current_server.is_default = value.lower() == "true"
                elif key == "Access token":
                    # 토큰은 ***로 마스킹되어 있으므로 있음만 표시
                    current_server.access_token = (
                        "***" if value and value != "***" else None
                    )
                elif key == "Refresh token":
                    current_server.refresh_token = (
                        "***" if value and value != "***" else None
                    )

        # 마지막 서버 저장
        if current_server:
            configs[current_server.server_id] = current_server

        self.logger.info(f"서버 설정 파싱 완료: {len(configs)}개 서버 발견")
        return configs

    def get_authentication_status(self) -> Dict[str, Any]:
        """
        전체 인증 상태 정보 가져오기

        Returns:
            Dict[str, Any]: 인증 상태 정보
        """
        status = {
            "jf_cli_installed": False,
            "server_configured": False,
            "authenticated": False,
            "server_accessible": False,
            "server_info": None,
            "errors": [],
        }

        try:
            # jf-cli 설치 확인
            status["jf_cli_installed"] = self.check_jf_cli_installed()
            if not status["jf_cli_installed"]:
                status["errors"].append("jf-cli가 설치되지 않았습니다.")
                return status

            # 서버 설정 확인
            server_config = self.get_target_server_config()
            if server_config:
                status["server_configured"] = True
                status["server_info"] = {
                    "server_id": server_config.server_id,
                    "url": server_config.url,
                    "artifactory_url": server_config.artifactory_url,
                    "user": server_config.user,
                    "is_default": server_config.is_default,
                }
            else:
                status["errors"].append("대상 서버 설정을 찾을 수 없습니다.")
                return status

            # 인증 확인
            status["authenticated"] = self.verify_authentication()
            if not status["authenticated"]:
                status["errors"].append("JFrog 인증에 실패했습니다.")
                return status

            # 서버 접근 확인
            status["server_accessible"] = self.check_server_access()
            if not status["server_accessible"]:
                status["errors"].append("JFrog 서버에 접근할 수 없습니다.")

        except Exception as e:
            status["errors"].append(f"인증 상태 확인 중 오류: {str(e)}")
            self.logger.error(f"인증 상태 확인 중 오류 발생: {e}")

        return status
