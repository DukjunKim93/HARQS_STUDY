# -*- coding: utf-8 -*-
"""
Crash Monitor Service for QSMonitor
Core dump monitoring service with built-in timer and callback system.
"""

from __future__ import annotations

from typing import Dict, List, Union

from PySide6.QtCore import QObject, QTimer

from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.DumpManager import DumpTriggeredBy
from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.Utils.DateTimeUtils import TimestampGenerator
from QSUtils.Utils.Logger import LOGD, LOGI, LOGW
from QSUtils.command.cmd_coredump_monitor import CoredumpMonitorCommandHandler


class CrashMonitorService(QObject):
    """Crash(코어덤프) 모니터링을 담당하는 자율적인 서비스 클래스 - 내장 타이머"""

    def __init__(self, adb_device: ADBDevice, event_manager, parent=None):
        super().__init__(parent)
        self.adb_device = adb_device
        self.event_manager = event_manager
        self.coredump_handler = CoredumpMonitorCommandHandler(adb_device)

        # 내장 타이머
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_timeout)

        self.is_monitoring = False
        self.monitoring_interval = 5000  # 기본 5초
        self.is_dump_in_progress = False  # dump 진행 상태 플래그

        # dump 이벤트 핸들러 직접 등록
        self._setup_dump_event_handlers()

    def _setup_dump_event_handlers(self):
        """dump 이벤트 핸들러 직접 등록"""
        if self.event_manager:
            self.event_manager.register_event_handler(
                CommonEventType.DUMP_STARTED, self._on_dump_started
            )
            self.event_manager.register_event_handler(
                CommonEventType.DUMP_COMPLETED, self._on_dump_completed
            )
            self.event_manager.register_event_handler(
                CommonEventType.DUMP_ERROR, self._on_dump_error
            )
            LOGI("CrashMonitorService: Dump event handlers registered")
        else:
            LOGW(
                "CrashMonitorService: No EventManager available, dump event handlers not registered"
            )

    def set_monitoring_interval(self, interval_ms: int):
        """모니터링 간격 설정 (밀리초)"""
        self.monitoring_interval = interval_ms
        if self.is_monitoring:
            self.timer.setInterval(interval_ms)

    def start_monitoring(self):
        """crash 모니터링 시작"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.timer.setInterval(self.monitoring_interval)
        self.timer.start()

        LOGI(
            f"CrashMonitorService: Crash monitoring started with interval {self.monitoring_interval}ms"
        )

    def stop_monitoring(self):
        """crash 모니터링 중지"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.timer.stop()

        LOGI("CrashMonitorService: Crash monitoring stopped")

    def _on_timer_timeout(self):
        """내장 타이머 타임아웃 핸들러"""
        try:
            self._check_and_handle_crash_files()
        except Exception as e:
            LOGD(f"CrashMonitorService: Error in crash monitoring timer: {str(e)}")

    def _check_and_handle_crash_files(self):
        """crash 파일 확인 및 처리"""
        try:
            if not getattr(self.adb_device, "is_connected", False):
                return

            # dump 진행 중이면 crash 감지 스킵
            if self.is_dump_in_progress:
                LOGD("CrashMonitorService: Crash monitoring paused during dump process")
                return

            result = self.coredump_handler.execute()

            # CommandResult에서 실제 데이터 추출
            if result and result.success:
                actual_data = result.data
                if (
                    actual_data
                    and isinstance(actual_data, list)
                    and len(actual_data) > 0
                ):
                    # crash 정보 구성
                    LOGI(f"CrashMonitorService: Detected crash files! {actual_data}")
                    self._on_crash_detected(
                        {
                            "crash_files": actual_data,
                            "crash_count": len(actual_data),
                            "timestamp": TimestampGenerator.get_iso_timestamp(),
                            "device_serial": self.adb_device.serial,
                        }
                    )
            else:
                LOGI(
                    f"CrashMonitorService: Command execution failed: {result.error if result else 'No result'}"
                )

        except Exception as e:
            LOGD(f"CrashMonitorService: Error checking crash files: {str(e)}")

    def _on_crash_detected(self, crash_info: Dict[str, Union[List, int, str]]):
        """crash 감지 시 이벤트 발생 및 dump 요청"""
        LOGI(
            f"CrashMonitorService: Detected {len(crash_info.get('crash_files', []))} crash files: {crash_info.get('crash_files', [])}"
        )

        # 시스템 이벤트 발생
        self.event_manager.emit_event(QSMonitorEventType.CRASH_DETECTED, crash_info)

        # dump 요청 (Mode 설정 없음, 기존 Mode 유지)
        self._request_dump_extraction()

    def _request_dump_extraction(self):
        """dump 추출 요청"""
        try:
            # UNIFIED_DUMP_REQUESTED 이벤트 발생 (Mode 설정 없음, 기존 Mode 유지, triggered_by = CRASH_MONITOR)
            self.event_manager.emit_event(
                CommonEventType.UNIFIED_DUMP_REQUESTED,
                {"triggered_by": DumpTriggeredBy.CRASH_MONITOR.value},
            )

            LOGI("CrashMonitorService: Dump requested due to crash detection")

        except Exception as e:
            LOGD(f"CrashMonitorService: Error requesting dump extraction: {e}")

    def check_immediately(self):
        """즉시 crash 파일 확인 (수동 확인용)"""
        if self.is_monitoring:
            self._check_and_handle_crash_files()

    def _on_dump_started(self, args: Dict):
        """dump 시작 시 crash 모니터링 일시 중지"""
        self.is_dump_in_progress = True
        if self.is_monitoring:
            self.timer.stop()  # 타이머 일시 중지
            LOGI("CrashMonitorService: Crash monitoring paused during dump process")

    def _on_dump_completed(self, args: Dict):
        """dump 완료 시 crash 모니터링 재개"""
        self.is_dump_in_progress = False
        if self.is_monitoring:
            self.timer.start()  # 타이머 재개
            LOGI("CrashMonitorService: Crash monitoring resumed after dump completion")

    def _on_dump_error(self, args: Dict):
        """dump 에러 시에도 crash 모니터링 재개"""
        self.is_dump_in_progress = False
        if self.is_monitoring:
            self.timer.start()  # 타이머 재개
            LOGI("CrashMonitorService: Crash monitoring resumed after dump error")
