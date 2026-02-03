#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrogUtils 예외 정의

JFrog Artifactory 관련 작업에서 발생할 수 있는 모든 예외를 정의합니다.
"""


class JFrogUtilsError(Exception):
    """JFrogUtils의 기본 예외 클래스"""

    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self):
        if self.details:
            return f"{self.message} (상세: {self.details})"
        return self.message


class JFrogNotInstalledError(JFrogUtilsError):
    """jf-cli가 설치되지 않은 경우 발생하는 예외"""

    def __init__(self, details: str = None):
        message = (
            "jf-cli가 설치되지 않았습니다. JFrog 공식 문서를 참조하여 설치해주세요."
        )
        super().__init__(message, details)


class JFrogLoginRequiredError(JFrogUtilsError):
    """JFrog에 로그인이 필요한 경우 발생하는 예외"""

    def __init__(self, details: str = None):
        message = (
            "JFrog에 먼저 로그인이 필요합니다. 'jf c add'와 'jf rt login'을 실행하세요."
        )
        super().__init__(message, details)


class JFrogAuthenticationError(JFrogUtilsError):
    """JFrog 인증에 실패한 경우 발생하는 예외"""

    def __init__(self, details: str = None):
        message = "JFrog 인증에 실패했습니다. 인증 정보를 확인하세요."
        super().__init__(message, details)


class JFrogConfigurationError(JFrogUtilsError):
    """JFrog 설정에 오류가 있는 경우 발생하는 예외"""

    def __init__(self, details: str = None):
        message = "JFrog 설정에 오류가 있습니다. 설정을 확인하세요."
        super().__init__(message, details)


class JFrogRepositoryNotFoundError(JFrogUtilsError):
    """리포지토리를 찾을 수 없는 경우 발생하는 예외"""

    def __init__(self, repository: str, details: str = None):
        message = f"리포지토리를 찾을 수 없습니다: {repository}"
        super().__init__(message, details)
        self.repository = repository


class JFrogPermissionDeniedError(JFrogUtilsError):
    """리포지토리 접근 또는 업로드 권한이 없는 경우 발생하는 예외"""

    def __init__(self, repository: str, operation: str = "접근", details: str = None):
        message = f"리포지토리에 {operation} 권한이 없습니다: {repository}. 관리자에게 문의하세요."
        super().__init__(message, details)
        self.repository = repository
        self.operation = operation


class JFrogAccessDeniedError(JFrogUtilsError):
    """JFrog 서버 접근이 거부된 경우 발생하는 예외"""

    def __init__(self, server_url: str, details: str = None):
        message = f"JFrog 서버 접근이 거부되었습니다: {server_url}"
        super().__init__(message, details)
        self.server_url = server_url


class JFrogUploadError(JFrogUtilsError):
    """파일 업로드 중 오류가 발생한 경우"""

    def __init__(self, file_path: str, details: str = None):
        message = f"파일 업로드에 실패했습니다: {file_path}"
        super().__init__(message, details)
        self.file_path = file_path


class JFrogNetworkError(JFrogUtilsError):
    """네트워크 관련 오류가 발생한 경우"""

    def __init__(self, details: str = None):
        message = (
            "JFrog 서버와의 네트워크 연결에 문제가 있습니다. 네트워크를 확인하세요."
        )
        super().__init__(message, details)
