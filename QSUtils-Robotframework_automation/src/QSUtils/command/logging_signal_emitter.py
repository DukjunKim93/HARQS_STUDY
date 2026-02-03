#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Signal Emitter
로깅 관련 시그널 발산을 전담하는 클래스
"""

from PySide6.QtCore import QObject, Signal


class LoggingSignalEmitter(QObject):
    """
    로깅 프로세스 상태 변경을 위한 시그널 발산 클래스
    """

    # 시그널 정의
    logging_started = Signal()
    logging_stopped = Signal()
    logging_error = Signal(str)
    log_line_data = Signal(str)  # 실시간 로그 라인 데이터용 시그널
    audio_log_data = Signal(str)  # ACM 오디오 로그용 시그널 (호환성 유지)

    def __init__(self):
        """
        LoggingSignalEmitter 초기화
        """
        super().__init__()

    def emit_logging_started(self) -> None:
        """로깅 시작 시그널 발산"""
        self.logging_started.emit()

    def emit_logging_stopped(self) -> None:
        """로깅 정지 시그널 발산"""
        self.logging_stopped.emit()

    def emit_logging_error(self, error_message: str) -> None:
        """
        로깅 에러 시그널 발산

        Args:
            error_message: 에러 메시지
        """
        self.logging_error.emit(error_message)

    def emit_log_line_data(self, log_data: str) -> None:
        """
        로그 라인 데이터 시그널 발산

        Args:
            log_data: 로그 데이터
        """
        self.log_line_data.emit(log_data)

    def emit_audio_log_data(self, audio_data: str) -> None:
        """
        오디오 로그 데이터 시그널 발산

        Args:
            audio_data: 오디오 로그 데이터
        """
        self.audio_log_data.emit(audio_data)
