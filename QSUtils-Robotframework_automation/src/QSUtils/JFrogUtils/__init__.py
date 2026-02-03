#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrogUtils - JFrog Artifactory 파일 업로드 유틸리티 패키지

QSUtils 프로젝트에 JFrog Artifactory 파일 업로드 기능을 제공합니다.
jfrog-cli를 래핑하여 사용하기 쉬운 Python 인터페이스를 제공하며,
자동 인증 상태 확인과 권한 확인 기능을 포함합니다.

주요 기능:
- JFrog Artifactory에 파일/디렉토리 업로드
- 기존 jf-cli 인증 상태 확인
- 리포지토리 접근 및 업로드 권한 확인
- 사용자 친화적인 에러 처리 및 가이드

사용 예제:
    from QSUtils.JFrogUtils import JFrogManager

    jfrog = JFrogManager()
    result = jfrog.upload_file("/path/to/file.txt")
    if result.success:
        print(f"업로드 성공: {result.data['url']}")
    else:
        print(f"업로드 실패: {result.message}")
"""

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.JFrogManager import JFrogManager
from QSUtils.JFrogUtils.exceptions import (
    JFrogUtilsError,
    JFrogNotInstalledError,
    JFrogLoginRequiredError,
    JFrogAuthenticationError,
    JFrogConfigurationError,
    JFrogRepositoryNotFoundError,
    JFrogPermissionDeniedError,
    JFrogAccessDeniedError,
)

__version__ = "1.0.0"
__author__ = "WaLyong Cho"

__all__ = [
    "JFrogManager",
    "JFrogConfig",
    "JFrogUtilsError",
    "JFrogNotInstalledError",
    "JFrogLoginRequiredError",
    "JFrogAuthenticationError",
    "JFrogConfigurationError",
    "JFrogRepositoryNotFoundError",
    "JFrogPermissionDeniedError",
    "JFrogAccessDeniedError",
]
