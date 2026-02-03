#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JFrog 메니저
JFrog Artifactory와의 모든 상호작용을 관리하는 메인 클래스입니다.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict

from QSUtils.JFrogUtils.JFrogAuthManager import JFrogAuthManager
from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.JFrogPermissionChecker import JFrogPermissionChecker
from QSUtils.JFrogUtils.JFrogUploadDialog import JFrogUploadDialog
from QSUtils.JFrogUtils.JFrogUploader import JFrogUploader
from QSUtils.JFrogUtils.exceptions import (
    JFrogNotInstalledError,
    JFrogLoginRequiredError,
    JFrogAuthenticationError,
    JFrogConfigurationError,
    JFrogRepositoryNotFoundError,
    JFrogPermissionDeniedError,
    JFrogUploadError,
)
from QSUtils.Utils.Logger import get_logger


@dataclass
class JFrogOperationResult:
    """JFrog 작업 결과 데이터 클래스"""

    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class JFrogManager:
    """JFrog Artifactory 관리 메인 클래스"""

    def __init__(self, config: Optional[JFrogConfig] = None):
        """
        JFrogManager 초기화
        Args:
            config: JFrog 설정 객체 (없으면 기본 설정 사용)
        """
        self.config = config or JFrogConfig()
        self.logger = get_logger()

        self.auth_manager = JFrogAuthManager(self.config)
        self.permission_checker = JFrogPermissionChecker(self.config)
        self.uploader = JFrogUploader(self.config)

        # 설정 유효성 검증
        if not self.config.is_valid():
            errors = self.config.validate()
            raise JFrogConfigurationError(f"설정 오류: {'; '.join(errors)}")

        self.logger.info(f"JFrogManager 초기화 완료: {self.config}")

    def verify_setup(self) -> JFrogOperationResult:
        """
        전체 설정 확인 (jf-cli 설치, 인증, 권한)
        Returns:
            JFrogOperationResult: 확인 결과
        """
        try:
            # 1. jf-cli 설치 확인
            if not self._check_jf_cli_installed():
                return JFrogOperationResult(
                    success=False,
                    message="jf-cli가 설치되지 않았습니다. JFrog 공식 문서를 참조하여 설치해주세요.",
                    error=JFrogNotInstalledError(),
                )

            # 2. 인증 상태 확인
            auth_result = self._check_authentication()
            if not auth_result.success:
                return auth_result

            # 3. 권한 확인
            if self.config.check_permissions:
                perm_result = self._check_permissions()
                if not perm_result.success:
                    return perm_result

            return JFrogOperationResult(
                success=True,
                message="JFrog 설정 확인 완료",
                data={
                    "server_url": self.config.server_url,
                    "repository": self.config.default_repo,
                    "authenticated": True,
                },
            )
        except Exception as e:
            self.logger.error(f"설정 확인 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"설정 확인 중 오류 발생: {str(e)}",
                error=e,
            )

    def check_permissions(self) -> JFrogOperationResult:
        """
        권한만 확인
        Returns:
            JFrogOperationResult: 권한 확인 결과
        """
        try:
            return self._check_permissions()
        except Exception as e:
            self.logger.error(f"권한 확인 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"권한 확인 중 오류 발생: {str(e)}",
                error=e,
            )

    def _create_upload_dialog(self, parent=None):
        """
        업로드 Dialog 생성 (테스트를 위한 분리된 메서드)
        Args:
            parent: 부모 위젯
        Returns:
            JFrogUploadDialog: 생성된 Dialog 객체
        """
        return JFrogUploadDialog(self.config, parent)

    def upload_file_with_dialog(
        self, local_path: str, target_path: str = None, repo: str = None, parent=None
    ) -> JFrogOperationResult:
        """
        Dialog와 함께 단일 파일 업로드
        Args:
            local_path: 업로드할 로컬 파일 경로
            target_path: 타겟 경로 (없으면 파일명 사용)
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
            parent: 부모 위젯
        Returns:
            JFrogOperationResult: 업로드 결과
        """
        try:
            # 전체 설정 확인
            setup_result = self.verify_setup()
            if not setup_result.success:
                return setup_result

            # Dialog 생성 및 실행
            dialog = self._create_upload_dialog(parent)
            dialog.start_file_upload(local_path, target_path, repo)

            # Dialog 실행 (모달)
            dialog.exec_()

            # 결과 반환
            result_data = dialog.get_result()
            if result_data:
                if result_data.get("cancelled", False):
                    return JFrogOperationResult(
                        success=False,
                        message="업로드가 취소되었습니다",
                        data=result_data,
                    )
                elif result_data.get("total_uploaded", 0) > 0:
                    return JFrogOperationResult(
                        success=True,
                        message=f"파일 업로드 성공: {local_path}",
                        data=result_data,
                    )
                else:
                    error_msg = "업로드 실패"
                    if result_data.get("failed_files"):
                        error_msg = result_data["failed_files"][0].get(
                            "error", "알 수 없는 오류"
                        )
                    return JFrogOperationResult(
                        success=False,
                        message=f"파일 업로드 실패: {error_msg}",
                        data=result_data,
                    )
            else:
                return JFrogOperationResult(
                    success=False, message="업로드 결과를 가져올 수 없습니다"
                )
        except Exception as e:
            self.logger.error(f"Dialog 파일 업로드 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"Dialog 파일 업로드 중 오류 발생: {str(e)}",
                error=e,
            )

    def upload_directory_with_dialog(
        self, local_path: str, target_path: str = None, repo: str = None, parent=None
    ) -> JFrogOperationResult:
        """
        Dialog와 함께 디렉토리 업로드
        Args:
            local_path: 업로드할 로컬 디렉토리 경로
            target_path: 타겟 경로 (없으면 디렉토리명 사용)
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
            parent: 부모 위젯
        Returns:
            JFrogOperationResult: 업로드 결과
        """
        try:
            # 전체 설정 확인
            setup_result = self.verify_setup()
            if not setup_result.success:
                return setup_result

            # Dialog 생성 및 실행
            dialog = self._create_upload_dialog(parent)
            dialog.start_directory_upload(local_path, target_path, repo)

            # Dialog 실행 (모달)
            dialog.exec_()

            # 결과 반환
            result_data = dialog.get_result()
            if result_data:
                if result_data.get("cancelled", False):
                    return JFrogOperationResult(
                        success=False,
                        message="업로드가 취소되었습니다",
                        data=result_data,
                    )
                elif result_data.get("total_uploaded", 0) > 0:
                    return JFrogOperationResult(
                        success=True,
                        message=f"디렉토리 업로드 성공: {local_path}",
                        data=result_data,
                    )
                else:
                    error_msg = "업로드 실패"
                    if result_data.get("failed_files"):
                        error_msg = result_data["failed_files"][0].get(
                            "error", "알 수 없는 오류"
                        )
                    return JFrogOperationResult(
                        success=False,
                        message=f"디렉토리 업로드 실패: {error_msg}",
                        data=result_data,
                    )
            else:
                return JFrogOperationResult(
                    success=False, message="업로드 결과를 가져올 수 없습니다"
                )
        except Exception as e:
            self.logger.error(f"Dialog 디렉토리 업로드 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"Dialog 디렉토리 업로드 중 오류 발생: {str(e)}",
                error=e,
            )

    def upload_file(
        self, local_path: str, target_path: str = None, repo: str = None
    ) -> JFrogOperationResult:
        """
        단일 파일 업로드
        Args:
            local_path: 업로드할 로컬 파일 경로
            target_path: 타겟 경로 (없으면 파일명 사용)
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
        Returns:
            JFrogOperationResult: 업로드 결과
        """
        try:
            # 전체 설정 확인
            setup_result = self.verify_setup()
            if not setup_result.success:
                return setup_result

            # 파일 존재 확인
            local_file = Path(local_path)
            if not local_file.exists():
                return JFrogOperationResult(
                    success=False,
                    message=f"파일을 찾을 수 없습니다: {local_path}",
                    error=JFrogUploadError(local_path),
                )

            # 타겟 경로 설정
            if not target_path:
                target_path = local_file.name

            # 리포지토리 설정
            target_repo = repo or self.config.default_repo
            upload_target = f"{target_repo}/{target_path.lstrip('/')}"

            self.logger.info(f"파일 업로드 시작: {local_path} -> {upload_target}")

            # 실제 업로드 실행
            result = self.uploader.upload_file(local_path, target_path, repo)

            if result.success:
                return JFrogOperationResult(
                    success=True,
                    message=f"파일 업로드 성공: {local_path}",
                    data={
                        "uploaded_files": result.uploaded_files,
                        "total_uploaded": result.total_uploaded,
                        "total_size": result.total_size,
                        "upload_time": result.upload_time,
                    },
                )
            else:
                error_msg = (
                    result.failed_files[0]["error"]
                    if result.failed_files
                    else "알 수 없는 오류"
                )
                return JFrogOperationResult(
                    success=False,
                    message=f"파일 업로드 실패: {error_msg}",
                    error=JFrogUploadError(error_msg),
                    data={
                        "failed_files": result.failed_files,
                        "total_failed": result.total_failed,
                    },
                )
        except Exception as e:
            self.logger.error(f"파일 업로드 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"파일 업로드 중 오류 발생: {str(e)}",
                error=e,
            )

    def upload_directory(
        self, local_path: str, target_path: str = None, repo: str = None
    ) -> JFrogOperationResult:
        """
        디렉토리 업로드
        Args:
            local_path: 업로드할 로컬 디렉토리 경로
            target_path: 타겟 경로 (없으면 디렉토리명 사용)
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
        Returns:
            JFrogOperationResult: 업로드 결과
        """
        try:
            # 전체 설정 확인
            setup_result = self.verify_setup()
            if not setup_result.success:
                return setup_result

            # 디렉토리 존재 확인
            local_dir = Path(local_path)
            if not local_dir.exists() or not local_dir.is_dir():
                return JFrogOperationResult(
                    success=False,
                    message=f"디렉토리를 찾을 수 없습니다: {local_path}",
                    error=JFrogUploadError(local_path),
                )

            # 타겟 경로 설정
            if not target_path:
                target_path = local_dir.name

            # 리포지토리 설정
            target_repo = repo or self.config.default_repo
            upload_target = f"{target_repo}/{target_path.lstrip('/')}/"

            self.logger.info(f"디렉토리 업로드 시작: {local_path} -> {upload_target}")

            # 실제 업로드 실행
            result = self.uploader.upload_directory(local_path, target_path, repo)

            if result.success:
                return JFrogOperationResult(
                    success=True,
                    message=f"디렉토리 업로드 성공: {local_path}",
                    data={
                        "uploaded_files": result.uploaded_files,
                        "total_uploaded": result.total_uploaded,
                        "total_size": result.total_size,
                        "upload_time": result.upload_time,
                    },
                )
            else:
                error_msg = (
                    result.failed_files[0]["error"]
                    if result.failed_files
                    else "알 수 없는 오류"
                )
                return JFrogOperationResult(
                    success=False,
                    message=f"디렉토리 업로드 실패: {error_msg}",
                    error=JFrogUploadError(error_msg),
                    data={
                        "failed_files": result.failed_files,
                        "total_failed": result.total_failed,
                    },
                )
        except Exception as e:
            self.logger.error(f"디렉토리 업로드 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"디렉토리 업로드 중 오류 발생: {str(e)}",
                error=e,
            )

    def _check_jf_cli_installed(self) -> bool:
        """
        jf-cli 설치 확인
        Returns:
            bool: 설치되어 있으면 True
        """
        return self.auth_manager.check_jf_cli_installed()

    def _check_authentication(self) -> JFrogOperationResult:
        """
        인증 상태 확인
        Returns:
            JFrogOperationResult: 인증 확인 결과
        """
        try:
            # 인증 상태 전체 확인
            auth_status = self.auth_manager.get_authentication_status()

            if not auth_status["jf_cli_installed"]:
                return JFrogOperationResult(
                    success=False,
                    message="jf-cli가 설치되지 않았습니다. JFrog 공식 문서를 참조하여 설치해주세요.",
                    error=JFrogNotInstalledError(),
                )

            if not auth_status["server_configured"]:
                return JFrogOperationResult(
                    success=False,
                    message="JFrog에 먼저 로그인이 필요합니다. 'jf c add'와 'jf rt login'을 실행하세요.",
                    error=JFrogLoginRequiredError(),
                )

            if not auth_status["authenticated"]:
                return JFrogOperationResult(
                    success=False,
                    message="JFrog 인증에 실패했습니다. 인증 정보를 확인하세요.",
                    error=JFrogAuthenticationError(),
                )

            return JFrogOperationResult(
                success=True,
                message="인증 상태 확인 완료",
                data=auth_status,
            )
        except Exception as e:
            self.logger.error(f"인증 확인 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"인증 확인 중 오류 발생: {str(e)}",
                error=e,
            )

    def _check_permissions(self) -> JFrogOperationResult:
        """
        리포지토리 권한 확인
        Returns:
            JFrogOperationResult: 권한 확인 결과
        """
        try:
            # 권한 상태 확인
            perm_status = self.permission_checker.get_permission_status()

            if not perm_status["authenticated"]:
                return JFrogOperationResult(
                    success=False,
                    message="JFrog 인증이 필요합니다.",
                    error=JFrogLoginRequiredError(),
                )

            # 권한 확인 결과 검증
            permissions = perm_status["permissions"]

            if not permissions.get("exists", False):
                return JFrogOperationResult(
                    success=False,
                    message=f"리포지토리를 찾을 수 없습니다: {permissions['repository']}",
                    error=JFrogRepositoryNotFoundError(permissions["repository"]),
                )

            if not permissions.get("upload_permission", False):
                return JFrogOperationResult(
                    success=False,
                    message=f"리포지토리에 업로드 권한이 없습니다: {permissions['repository']}. 관리자에게 문의하세요.",
                    error=JFrogPermissionDeniedError(
                        permissions["repository"], "업로드"
                    ),
                )

            return JFrogOperationResult(
                success=True,
                message=f"리포지토리 권한 확인 완료: {permissions['repository']}",
                data=perm_status,
            )
        except Exception as e:
            self.logger.error(f"권한 확인 중 오류 발생: {e}")
            return JFrogOperationResult(
                success=False,
                message=f"권한 확인 중 오류 발생: {str(e)}",
                error=e,
            )
