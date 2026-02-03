#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common Event Type Definitions
UIFramework에서 공통으로 사용하는 이벤트 타입을 Enum으로 정의하여 타입 안정성과 코드 완성도를 향상시킵니다.
"""

from typing import Dict, TYPE_CHECKING, Any, cast

from QSUtils.UIFramework.base.BaseEventType import BaseEventType

if TYPE_CHECKING:
    pass


class CommonEventType(BaseEventType):
    """UIFramework 공통 이벤트 타입 Enum"""

    # Device 연결 관련 이벤트
    DEVICE_CONNECTED = "device_connected"
    DEVICE_DISCONNECTED = "device_disconnected"
    DEVICE_CONNECTION_CHANGED = "device_connection_changed"

    # Session 관련 이벤트
    SESSION_STATE_CHANGED = "session_state_changed"

    # Reboot 관련 이벤트
    REBOOT_REQUESTED = "reboot_requested"
    REBOOT_COMPLETED = "reboot_completed"

    # Dump 관련 이벤트
    DUMP_REQUESTED = "dump_requested"
    UNIFIED_DUMP_REQUESTED = "unified_dump_requested"
    DUMP_COMPLETED = "dump_completed"
    DUMP_STARTED = "dump_started"
    DUMP_PROGRESS = "dump_progress"
    DUMP_PROGRESS_UPDATED = "dump_progress_updated"  # New
    DUMP_STATUS_CHANGED = "dump_status_changed"  # New
    DUMP_ERROR = "dump_error"

    # Status 관련 이벤트
    STATUS_UPDATE_REQUESTED = "status_update_requested"  # New

    def get_expected_args(self) -> Dict[str, Any]:
        """이 이벤트 타입이 예상하는 인자 구조 반환"""
        expected_args = {
            # Device 연결 관련 이벤트
            CommonEventType.DEVICE_CONNECTED: {},
            CommonEventType.DEVICE_DISCONNECTED: {},
            CommonEventType.DEVICE_CONNECTION_CHANGED: {
                "connected": bool,
                "device_serial": str,
                "connection_type": str,  # usb | wifi | network
            },
            # Session 관련 이벤트
            CommonEventType.SESSION_STATE_CHANGED: {
                "state": str,  # running | stopped | paused
                "manual": bool,
                "previous_state": str,
            },
            # Reboot 관련 이벤트
            CommonEventType.REBOOT_REQUESTED: {"sync_before_reboot": bool},
            CommonEventType.REBOOT_COMPLETED: {"result": object},
            # Dump 관련 이벤트
            CommonEventType.DUMP_REQUESTED: {
                "triggered_by": str  # DumpTriggeredBy enum value
            },
            CommonEventType.UNIFIED_DUMP_REQUESTED: {
                "triggered_by": str,  # DumpTriggeredBy enum value
                "request_device_id": (str, type(None)),  # Optional requesting device ID
                "upload_enabled": (
                    bool,
                    type(None),
                ),  # Optional upload enabled flag (from Dialog)
                "issue_dir": (str, type(None)),  # Optional override issue directory
            },
            CommonEventType.DUMP_COMPLETED: {
                "triggered_by": (str, type(None)),  # DumpTriggeredBy enum value or None
                "success": bool,
                "upload_enabled": (bool, type(None)),  # Optional upload enabled flag
                "dump_path": (str, type(None)),  # Optional dump path
            },
            CommonEventType.DUMP_STARTED: {
                "triggered_by": (str, type(None))  # DumpTriggeredBy enum value or None
            },
            CommonEventType.DUMP_PROGRESS: {"message": str},
            CommonEventType.DUMP_PROGRESS_UPDATED: {
                "progress": int,  # 0-100%
                "stage": str,
                "message": str,
                "dump_id": str,
            },
            CommonEventType.DUMP_STATUS_CHANGED: {
                "status": str,  # in_progress | completed | failed | cancelled
                "dump_id": str,
                "triggered_by": str,
                "error_message": (str, type(None)),
            },
            CommonEventType.DUMP_ERROR: {"error_message": str},
            # Status 관련 이벤트
            CommonEventType.STATUS_UPDATE_REQUESTED: {},
        }
        return cast(Dict[str, Any], expected_args.get(self, {}))
