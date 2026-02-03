#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Log File Manager
로그 파일 관리를 전담하는 클래스
"""

from pathlib import Path
from typing import Optional

from QSUtils.Utils.FileUtils import ensure_directory_exists
from QSUtils.Utils.Logger import LOGI, LOGE, LOGD


class LogFileManager:
    """
    로그 파일의 생성, 관리, 쓰기 작업을 담당하는 클래스
    """

    def __init__(self, log_file_path: Path):
        """
        LogFileManager 초기화

        Args:
            log_file_path: 로그 파일 경로
        """
        self.log_file_path = Path(log_file_path)
        self.log_file: Optional[object] = None

    def initialize_file(self, append_mode: bool = False) -> bool:
        """
        로그 파일 초기화 및 디렉토리 생성

        Args:
            append_mode: 기존 파일에 추가 모드로 열지 여부

        Returns:
            bool: 성공 여부
        """
        try:
            # 로그 디렉토리 생성 확인
            if not ensure_directory_exists(self.log_file_path.parent):
                LOGE(f"Failed to create log directory: {self.log_file_path.parent}")
                return False

            # 파일 열기 모드 결정
            mode = "a" if append_mode else "w"
            self.log_file = open(
                self.log_file_path, mode, encoding="utf-8", buffering=1
            )  # line buffering
            LOGD(
                f"Log file initialized: {self.log_file_path}, append mode: {append_mode}"
            )
            return True

        except Exception as e:
            LOGE(f"Failed to initialize log file: {str(e)}")
            return False

    def write_line(self, text: str) -> bool:
        """
        로그 파일에 한 줄 쓰기

        Args:
            text: 쓸 텍스트

        Returns:
            bool: 성공 여부
        """
        if not self.log_file:
            LOGE("Log file not initialized")
            return False

        try:
            self.log_file.write(text)
            self.log_file.flush()  # 즉시 디스크에 쓰기
            return True
        except Exception as e:
            LOGE(f"Failed to write to log file: {str(e)}")
            return False

    def close_file(self) -> None:
        """
        로그 파일 닫기
        """
        if self.log_file:
            try:
                self.log_file.close()
                LOGI(f"Log file closed: {self.log_file_path}")
            except Exception as e:
                LOGE(f"Failed to close log file: {str(e)}")
            finally:
                self.log_file = None

    def get_file_path(self) -> str:
        """
        로그 파일 경로 반환

        Returns:
            str: 로그 파일 경로
        """
        return str(self.log_file_path)

    def is_file_open(self) -> bool:
        """
        파일이 열려있는지 확인

        Returns:
            bool: 파일 열림 여부
        """
        return self.log_file is not None
