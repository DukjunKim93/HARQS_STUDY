# -*- coding: utf-8 -*-
"""
QSMonitor Event Type Definitions
이벤트 타입을 Enum으로 정의하여 타입 안정성과 코드 완성도를 향상시킵니다.
"""

from typing import Dict, TYPE_CHECKING

from QSUtils.UIFramework.base.BaseEventType import BaseEventType

if TYPE_CHECKING:
    pass


class QSMonitorEventType(BaseEventType):
    """QSMonitor 이벤트 타입 Enum"""

    # Symphony 상태 관련 이벤트
    SYMPHONY_STATUS_UPDATED = "symphony_status_updated"
    SYMPHONY_GROUP_UPDATED = "symphony_group_updated"
    SYMPHONY_VOLUME_UPDATED = "symphony_volume_updated"
    QS_STATE_CHANGED = "qs_state_changed"
    ACM_STATE_CHANGED = "acm_state_changed"
    SYMPHONY_GROUP_STATE_CHANGED = "symphony_group_state_changed"

    # Preference 데이터 관련 이벤트
    PREFERENCE_DATA_UPDATED = "preference_data_updated"

    # AutoReboot 관련 이벤트
    AUTO_REBOOT_STATUS_CHANGED = "auto_reboot_status_changed"

    # Crash 관련 이벤트
    CRASH_DETECTED = "crash_detected"

    # 네트워크 관련 이벤트
    NETWORK_INTERFACE_UPDATED = "network_interface_updated"

    # 스피커 그리드 관련 이벤트
    SPEAKER_GRID_UPDATED = "speaker_grid_updated"

    def get_expected_args(self) -> Dict[str, type]:
        """이 이벤트 타입이 예상하는 인자 구조 반환"""
        expected_args = {
            # Symphony 상태 관련 이벤트
            QSMonitorEventType.SYMPHONY_STATUS_UPDATED: {
                "qs_state": str,
                "sound_mode": str,
                "mode_type_display": str,
            },
            QSMonitorEventType.SYMPHONY_GROUP_UPDATED: {"group_mode": str},
            QSMonitorEventType.SYMPHONY_VOLUME_UPDATED: {
                "volume": (int, type(None))  # int 또는 None
            },
            QSMonitorEventType.QS_STATE_CHANGED: {
                "qs_state": str,
                "acm_service_state": str,
            },
            QSMonitorEventType.ACM_STATE_CHANGED: {
                "qs_state": str,
                "acm_service_state": str,
            },
            QSMonitorEventType.SYMPHONY_GROUP_STATE_CHANGED: {"state": str},
            # Preference 데이터 관련 이벤트
            QSMonitorEventType.PREFERENCE_DATA_UPDATED: {
                "acm_service_state": str,
                "multiroom_grouptype": str,
                "multiroom_mode": str,
            },
            QSMonitorEventType.AUTO_REBOOT_STATUS_CHANGED: {
                "status": str,
                "is_running": bool,
            },
            # Crash 관련 이벤트
            QSMonitorEventType.CRASH_DETECTED: {"crash_info": dict},
            # 네트워크 관련 이벤트
            QSMonitorEventType.NETWORK_INTERFACE_UPDATED: {
                "ipv4": str,
                "ipv6": str,
                "flags": list,
            },
            # 스피커 그리드 관련 이벤트
            QSMonitorEventType.SPEAKER_GRID_UPDATED: {"update_type": str, "data": dict},
        }
        return expected_args.get(self, {})


class SpeakerGridUpdateEvent:
    """스피커 그리드 업데이트 이벤트 클래스"""

    def __init__(self, update_type: str, data: dict):
        self.update_type = update_type
        self.data = data

    def __str__(self):
        return f"SpeakerGridUpdateEvent(update_type={self.update_type})"
