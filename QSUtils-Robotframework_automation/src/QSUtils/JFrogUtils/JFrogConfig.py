#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrog 설정 관리

JFrog Artifactory 연결을 위한 설정 정보를 관리합니다.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

# 기본 설정 상수
DEFAULT_JFROG_SETTINGS = {
    "jfrog_server_url": "https://bart.sec.samsung.net/artifactory",
    "jfrog_default_repo": "oneos-qsymphony-issues-generic-local",
    "jfrog_server_name": "qsutils-server",
}


@dataclass
class JFrogConfig:
    """JFrog Artifactory 설정 정보"""

    # 고정된 서버 정보
    server_url: str = "https://bart.sec.samsung.net/artifactory"
    default_repo: str = "oneos-qsymphony-issues-generic-local"
    # server_name: jf-cli 설정에 저장될 서버 구성 이름
    server_name: str = "qsutils-server"

    # 인증 정보 (참고용 - 실제 인증은 jf-cli 설정 파일에서 확인)
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    access_token: Optional[str] = None

    # 동작 설정
    auto_login: bool = True  # 자동 로그인 시도 (현재는 사용하지 않음)
    check_permissions: bool = True  # 권한 확인 수행
    interactive_fallback: bool = True  # 대화형 로그인 폴백 (현재는 사용하지 않음)

    # 업로드 설정
    upload_timeout: int = 300  # 업로드 타임아웃 (초)
    chunk_size: int = 1024 * 1024  # 청크 크기 (1MB)
    max_retries: int = 3  # 최대 재시도 횟수

    # 로깅 설정
    verbose: bool = False  # 상세 로깅
    log_commands: bool = False  # jf-cli 명령어 로깅

    # 임시 파일 설정
    temp_dir: Optional[Path] = field(default_factory=lambda: Path("/tmp"))
    cleanup_temp: bool = True  # 임시 파일 자동 정리

    def __post_init__(self):
        """초기화 후 처리"""
        # temp_dir을 Path 객체로 변환
        if isinstance(self.temp_dir, str):
            self.temp_dir = Path(self.temp_dir)

    @classmethod
    def from_settings(cls, settings_manager=None) -> "JFrogConfig":
        """
        설정 관리자에서 JFrog 설정을 로드하여 JFrogConfig 객체 생성

        Args:
            settings_manager: 설정 관리자 객체

        Returns:
            JFrogConfig: 설정이 적용된 JFrogConfig 객체
        """
        config = cls()

        if settings_manager:
            try:
                # 설정에서 JFrog 관련 설정 로드
                upload_settings = settings_manager.get("dump.upload_settings", {})

                # 설정 적용 (기본값과 병합)
                config.server_url = upload_settings.get(
                    "jfrog_server_url", DEFAULT_JFROG_SETTINGS["jfrog_server_url"]
                )
                config.default_repo = upload_settings.get(
                    "jfrog_default_repo", DEFAULT_JFROG_SETTINGS["jfrog_default_repo"]
                )
                config.server_name = upload_settings.get(
                    "jfrog_server_name", DEFAULT_JFROG_SETTINGS["jfrog_server_name"]
                )

            except Exception as e:
                # 설정 로드 실패 시 기본값 사용
                config.server_url = DEFAULT_JFROG_SETTINGS["jfrog_server_url"]
                config.default_repo = DEFAULT_JFROG_SETTINGS["jfrog_default_repo"]
                config.server_name = DEFAULT_JFROG_SETTINGS["jfrog_server_name"]

        return config

    def update_from_settings(self, settings_manager=None) -> None:
        """
        설정 관리자에서 설정을 로드하여 현재 객체 업데이트

        Args:
            settings_manager: 설정 관리자 객체
        """
        if settings_manager:
            try:
                # 설정에서 JFrog 관련 설정 로드
                upload_settings = settings_manager.get("dump.upload_settings", {})

                # 설정 업데이트
                self.server_url = upload_settings.get(
                    "jfrog_server_url", self.server_url
                )
                self.default_repo = upload_settings.get(
                    "jfrog_default_repo", self.default_repo
                )
                self.server_name = upload_settings.get(
                    "jfrog_server_name", self.server_name
                )

            except Exception as e:
                # 설정 로드 실패 시 무시 (현재 값 유지)
                pass

    @property
    def artifactory_url(self) -> str:
        """Artifactory URL 반환"""
        return self.server_url.rstrip("/")

    @property
    def server_id(self) -> str:
        """서버 ID 반환 (server_name과 동일)"""
        return self.server_name

    def validate(self) -> List[str]:
        """
        설정 유효성 검증

        Returns:
            List[str]: 오류 메시지 목록 (없으면 빈 리스트)
        """
        errors = []

        # 서버 URL 확인
        if not self.server_url:
            errors.append("서버 URL이 설정되지 않았습니다.")
        elif not self.server_url.startswith(("http://", "https://")):
            errors.append("서버 URL은 http:// 또는 https://로 시작해야 합니다.")

        # 기본 리포지토리 확인
        if not self.default_repo:
            errors.append("기본 리포지토리가 설정되지 않았습니다.")

        # 서버 이름 확인
        if not self.server_name:
            errors.append("서버 이름이 설정되지 않았습니다.")

        # 타임아웃 확인
        if self.upload_timeout <= 0:
            errors.append("업로드 타임아웃은 0보다 커야 합니다.")

        # 청크 크기 확인
        if self.chunk_size <= 0:
            errors.append("청크 크기는 0보다 커야 합니다.")

        # 최대 재시도 횟수 확인
        if self.max_retries < 0:
            errors.append("최대 재시도 횟수는 0 이상이어야 합니다.")

        # 임시 디렉토리 확인
        if self.temp_dir and not self.temp_dir.exists():
            try:
                self.temp_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"임시 디렉토리를 생성할 수 없습니다: {e}")

        return errors

    def is_valid(self) -> bool:
        """
        설정이 유효한지 확인

        Returns:
            bool: 유효하면 True, 아니면 False
        """
        return len(self.validate()) == 0

    def get_server_config_command(self) -> str:
        """
        서버 설정 추가 명령어 생성

        Returns:
            str: jf c add 명령어
        """
        return (
            f"jf c add {self.server_name} "
            f"--url={self.server_url} "
            f"--user={self.username or '<username>'} "
            f"--password={'<password>' if self.password else '<password>'}"
        )

    def get_upload_target(self, target_path: str = None) -> str:
        """
        업로드 대상 경로 생성

        Args:
            target_path: 타겟 경로 (없으면 기본 경로 사용)

        Returns:
            str: 업로드 대상 경로
        """
        if target_path:
            return f"{self.default_repo}/{target_path.lstrip('/')}"
        return self.default_repo

    def __str__(self) -> str:
        """설정 정보 문자열 반환"""
        return (
            f"JFrogConfig("
            f"server_url={self.server_url}, "
            f"default_repo={self.default_repo}, "
            f"server_name={self.server_name}, "
            f"check_permissions={self.check_permissions}"
            f")"
        )
