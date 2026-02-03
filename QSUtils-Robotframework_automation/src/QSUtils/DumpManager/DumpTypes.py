# -*- coding: utf-8 -*-
"""
Dump Manager Type Definitions
Dump 관련 열거형 및 타입 정의
"""

from enum import Enum


class DumpState(Enum):
    """Dump 추출 상태 열거형"""

    IDLE = "idle"  # 대기 상태
    STARTING = "starting"  # 시작 중
    EXTRACTING = "extracting"  # 추출 중
    VERIFYING = "verifying"  # 결과 검증 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    TIMEOUT = "timeout"  # 타임아웃


class DumpMode(Enum):
    """Dump 추출 모드 열거형"""

    DIALOG = "dialog"  # 다이얼로그 표시 모드 (default)
    HEADLESS = "headless"  # headless 모드 (다이얼로그 없음)


class DumpTriggeredBy(Enum):
    """Dump 추출 트리거 열거형"""

    MANUAL = "manual"  # 사용자 직접 클릭
    CRASH_MONITOR = "crash_monitor"  # CrashMonitorService에 의한 자동 추출
    QS_FAILED = "qs_failed"  # AutoReboot의 QS 실패로 인한 추출
