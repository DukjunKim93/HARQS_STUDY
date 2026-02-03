# -*- coding: utf-8 -*-
"""
Global Event Type Definitions for QSMonitor
전역(앱 스코프)에서 사용하는 이벤트 타입을 정의합니다.
"""

from typing import Dict, Any, cast

from QSUtils.UIFramework.base.BaseEventType import BaseEventType


class GlobalEventType(BaseEventType):
    """QSMonitor 전역 이벤트 타입 Enum"""

    # 전역 덤프 관련 이벤트
    GLOBAL_DUMP_REQUESTED = "global_dump_requested"
    UNIFIED_DUMP_REQUESTED = "unified_dump_requested"
    GLOBAL_DUMP_PROGRESS = "global_dump_progress"
    GLOBAL_DUMP_COMPLETED = "global_dump_completed"

    # JFrog 업로드 관련 이벤트
    JFROG_UPLOAD_STARTED = "jfrog_upload_started"
    JFROG_UPLOAD_COMPLETED = "jfrog_upload_completed"

    def get_expected_args(self) -> Dict[str, Any]:
        """이 이벤트 타입이 예상하는 인자 구조 반환"""
        expected_args = {
            GlobalEventType.GLOBAL_DUMP_REQUESTED: {
                "triggered_by": str,  # ex) "qs_failed"
                "request_device_id": str,  # 요청을 유발한 디바이스(시리얼)
            },
            GlobalEventType.UNIFIED_DUMP_REQUESTED: {
                "triggered_by": str,  # DumpTriggeredBy enum value
                "request_device_id": (str, type(None)),  # Optional requesting device ID
                "upload_enabled": (
                    bool,
                    type(None),
                ),  # Optional upload enabled flag (from Dialog)
                "issue_dir": (str, type(None)),  # Optional override issue directory
            },
            GlobalEventType.GLOBAL_DUMP_PROGRESS: {
                "issue_id": str,
                "completed": int,
                "total": int,
            },
            GlobalEventType.GLOBAL_DUMP_COMPLETED: {
                "issue_id": str,
                "success_count": int,
                "fail_count": int,
                "issue_dir": str,
            },
            GlobalEventType.JFROG_UPLOAD_STARTED: {
                "issue_id": str,
                "device_serial": (str, type(None)),
                "show_dialog": (bool, type(None)),
                "issue_root": (str, type(None)),
                "targets": (list, type(None)),
                "triggered_by": (str, type(None)),
            },
            GlobalEventType.JFROG_UPLOAD_COMPLETED: {
                "issue_id": str,
                "success": bool,
                "message": str,
                "upload_info": (dict, type(None)),
                "device_serial": (str, type(None)),
                "device_serials": (list, type(None)),
                "uploaded_files": (list, type(None)),
                "jfrog_links": (dict, type(None)),
                "manifest_path": (str, type(None)),
                "upload_id": (str, type(None)),
            },
        }
        return cast(Dict[str, Any], expected_args.get(self, {}))
