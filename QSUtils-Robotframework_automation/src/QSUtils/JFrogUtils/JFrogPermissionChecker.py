#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrog 권한 확인

JFrog Artifactory 리포지토리 접근 및 업로드 권한을 확인합니다.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional, Dict, Any

from QSUtils.JFrogUtils.JFrogAuthManager import JFrogAuthManager
from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.exceptions import (
    JFrogRepositoryNotFoundError,
    JFrogPermissionDeniedError,
)
from QSUtils.Utils.Logger import get_logger


@dataclass
class JFrogRepositoryInfo:
    """JFrog 리포지토리 정보"""

    repo_key: str
    repo_type: str
    package_type: str
    description: str
    url: Optional[str] = None


class JFrogPermissionChecker:
    """JFrog 권한 확인 클래스"""

    def __init__(self, config: JFrogConfig):
        """
        JFrogPermissionChecker 초기화

        Args:
            config: JFrog 설정 객체
        """
        self.config = config
        self.logger = get_logger()
        self.auth_manager = JFrogAuthManager(config)

    def check_repository_exists(self, repo: str = None) -> bool:
        """
        리포지토리 존재 여부 확인

        Args:
            repo: 리포지토리 이름 (없으면 기본 리포지토리 사용)

        Returns:
            bool: 리포지토리가 존재하면 True
        """
        target_repo = repo or self.config.default_repo

        try:
            # 리포지토리 정보 조회
            result = subprocess.run(
                ["jf", "rt", "curl", "-XGET", f"/api/repositories/{target_repo}"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.logger.info(f"리포지토리 존재 확인: {target_repo}")
                return True
            else:
                self.logger.error(f"리포지토리 없음: {target_repo} - {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("리포지토리 존재 확인 타임아웃")
            return False
        except Exception as e:
            self.logger.error(f"리포지토리 존재 확인 중 오류 발생: {e}")
            return False

    def get_repository_info(self, repo: str = None) -> Optional[JFrogRepositoryInfo]:
        """
        리포지토리 정보 가져오기

        Args:
            repo: 리포지토리 이름 (없으면 기본 리포지토리 사용)

        Returns:
            Optional[JFrogRepositoryInfo]: 리포지토리 정보 (없으면 None)
        """
        target_repo = repo or self.config.default_repo

        try:
            result = subprocess.run(
                ["jf", "rt", "curl", "-XGET", f"/api/repositories/{target_repo}"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.logger.error(
                    f"리포지토리 정보 조회 실패: {target_repo} - {result.stderr}"
                )
                return None

            # JSON 응답 파싱 (간단한 파싱)
            import json

            repo_data = json.loads(result.stdout)

            return JFrogRepositoryInfo(
                repo_key=repo_data.get("key", ""),
                repo_type=repo_data.get("rclass", ""),
                package_type=repo_data.get("packageType", ""),
                description=repo_data.get("description", ""),
                url=repo_data.get("url"),
            )

        except subprocess.TimeoutExpired:
            self.logger.error("리포지토리 정보 조회 타임아웃")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"리포지토리 정보 JSON 파싱 실패: {e}")
            return None
        except Exception as e:
            self.logger.error(f"리포지토리 정보 조회 중 오류 발생: {e}")
            return None

    def test_upload_permission(self, repo: str = None) -> bool:
        """
        업로드 권한 테스트 (임시 파일 업로드/삭제)

        Args:
            repo: 리포지토리 이름 (없으면 기본 리포지토리 사용)

        Returns:
            bool: 업로드 권한이 있으면 True
        """
        target_repo = repo or self.config.default_repo

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write("JFrogUtils permission test")
            temp_file_path = temp_file.name

        try:
            target_path = f"{target_repo}/.permission_test_{os.getpid()}.txt"

            # 업로드 시도 (올바른 JFrog CLI 명령어 형식)
            self.logger.info(
                f"업로드 권한 테스트 시작: {temp_file_path} -> {target_path}"
            )
            upload_result = subprocess.run(
                ["jf", "rt", "upload", temp_file_path, target_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.logger.info(f"업로드 명령어 반환 코드: {upload_result.returncode}")
            if upload_result.stdout:
                self.logger.info(f"업로드 stdout: {upload_result.stdout}")
            if upload_result.stderr:
                self.logger.warning(f"업로드 stderr: {upload_result.stderr}")

            if upload_result.returncode != 0:
                self.logger.error(f"업로드 권한 테스트 실패: {upload_result.stderr}")
                return False

            self.logger.info(f"업로드 권한 테스트 성공: {target_path}")

            # 업로드된 파일 삭제 (quiet 모드로 interactive 방지)
            delete_result = subprocess.run(
                ["jf", "rt", "delete", "--quiet", target_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if delete_result.returncode != 0:
                self.logger.warning(f"테스트 파일 삭제 실패: {delete_result.stderr}")
                # 삭제 실패해도 업로드 권한은 있는 것으로 간주
                return True

            self.logger.info("테스트 파일 삭제 성공")
            return True

        except subprocess.TimeoutExpired:
            self.logger.error("업로드 권한 테스트 타임아웃")
            return False
        except Exception as e:
            self.logger.error(f"업로드 권한 테스트 중 오류 발생: {e}")
            return False
        finally:
            # 임시 파일 삭제
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    def check_read_permission(self, repo: str = None) -> bool:
        """
        읽기 권한 확인 (리포지토리 목록 조회)

        Args:
            repo: 리포지토리 이름 (없으면 기본 리포지토리 사용)

        Returns:
            bool: 읽기 권한이 있으면 True
        """
        target_repo = repo or self.config.default_repo

        try:
            result = subprocess.run(
                ["jf", "rt", "curl", "-XGET", f"/api/storage/{target_repo}"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.logger.info(f"읽기 권한 확인 성공: {target_repo}")
                return True
            else:
                self.logger.error(
                    f"읽기 권한 확인 실패: {target_repo} - {result.stderr}"
                )
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("읽기 권한 확인 타임아웃")
            return False
        except Exception as e:
            self.logger.error(f"읽기 권한 확인 중 오류 발생: {e}")
            return False

    def check_permissions(self, repo: str = None) -> Dict[str, Any]:
        """
        종합적인 권한 확인

        Args:
            repo: 리포지토리 이름 (없으면 기본 리포지토리 사용)

        Returns:
            Dict[str, Any]: 권한 확인 결과
        """
        target_repo = repo or self.config.default_repo

        result = {
            "repository": target_repo,
            "exists": False,
            "read_permission": False,
            "upload_permission": False,
            "repository_info": None,
            "errors": [],
        }

        try:
            # 1. 리포지토리 존재 확인
            result["exists"] = self.check_repository_exists(target_repo)
            if not result["exists"]:
                result["errors"].append(f"리포지토리를 찾을 수 없습니다: {target_repo}")
                return result

            # 2. 리포지토리 정보 가져오기
            result["repository_info"] = self.get_repository_info(target_repo)

            # 3. 읽기 권한 확인
            result["read_permission"] = self.check_read_permission(target_repo)
            if not result["read_permission"]:
                result["errors"].append(
                    f"리포지토리 읽기 권한이 없습니다: {target_repo}"
                )

            # 4. 업로드 권한 확인
            result["upload_permission"] = self.test_upload_permission(target_repo)
            if not result["upload_permission"]:
                result["errors"].append(
                    f"리포지토리 업로드 권한이 없습니다: {target_repo}"
                )

            # 성공 여부 확인
            if (
                result["exists"]
                and result["read_permission"]
                and result["upload_permission"]
            ):
                self.logger.info(f"리포지토리 권한 확인 완료: {target_repo}")
            else:
                self.logger.warning(f"리포지토리 권한 확인 실패: {target_repo}")

        except Exception as e:
            error_msg = f"권한 확인 중 오류 발생: {str(e)}"
            result["errors"].append(error_msg)
            self.logger.error(error_msg)

        return result

    def verify_upload_permissions(self, repo: str = None) -> bool:
        """
        업로드 권한만 확인 (간편한 메소드)

        Args:
            repo: 리포지토리 이름 (없으면 기본 리포지토리 사용)

        Returns:
            bool: 업로드 권한이 있으면 True

        Raises:
            JFrogRepositoryNotFoundError: 리포지토리가 없는 경우
            JFrogPermissionDeniedError: 업로드 권한이 없는 경우
            JFrogAccessDeniedError: 접근 권한이 없는 경우
        """
        target_repo = repo or self.config.default_repo

        # 리포지토리 존재 확인
        if not self.check_repository_exists(target_repo):
            raise JFrogRepositoryNotFoundError(target_repo)

        # 업로드 권한 테스트
        if not self.test_upload_permission(target_repo):
            raise JFrogPermissionDeniedError(target_repo, "업로드")

        return True

    def get_permission_status(self, repo: str = None) -> Dict[str, Any]:
        """
        전체 권한 상태 정보 가져오기

        Args:
            repo: 리포지토리 이름 (없으면 기본 리포지토리 사용)

        Returns:
            Dict[str, Any]: 권한 상태 정보
        """
        target_repo = repo or self.config.default_repo

        status = {
            "repository": target_repo,
            "authenticated": False,
            "server_accessible": False,
            "permissions": {},
            "errors": [],
        }

        try:
            # 1. 인증 상태 확인
            auth_status = self.auth_manager.get_authentication_status()
            status["authenticated"] = auth_status["authenticated"]
            status["server_accessible"] = auth_status["server_accessible"]

            if not status["authenticated"]:
                status["errors"].extend(auth_status["errors"])
                return status

            # 2. 권한 확인
            status["permissions"] = self.check_permissions(target_repo)

            if status["permissions"]["errors"]:
                status["errors"].extend(status["permissions"]["errors"])

        except Exception as e:
            error_msg = f"권한 상태 확인 중 오류: {str(e)}"
            status["errors"].append(error_msg)
            self.logger.error(error_msg)

        return status
