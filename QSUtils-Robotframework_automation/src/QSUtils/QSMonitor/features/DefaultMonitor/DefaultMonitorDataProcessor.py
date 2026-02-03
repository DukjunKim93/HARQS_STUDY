# -*- coding: utf-8 -*-
"""
DefaultMonitorDataProcessor - Q-Symphony, ACM, Multiroom 상태 데이터 처리 및 이벤트 발생 담당 클래스
"""

from __future__ import annotations

from typing import Any, Optional

from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.QSMonitor.features.base.BaseDataProcessor import BaseDataProcessor
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.Utils.Logger import LOGD, LOGI
from QSUtils.command.cmd_get_preference_data import PreferenceDataCommandHandler
from QSUtils.command.cmd_pp_symphony import SymphonyStatusCommandHandler
from QSUtils.command.cmd_pp_symphony_group import SymphonyGroupCommandHandler
from QSUtils.command.cmd_pp_symphony_volume_add import SymphonyVolumeAddCommandHandler


class DefaultMonitorDataProcessor(BaseDataProcessor):
    """
    Q-Symphony, ACM, Multiroom 상태 데이터 처리 및 이벤트 발생 담당 클래스

    DeviceWidget에서 데이터 처리 로직을 분리하여 책임을 명확히 분리하고
    중복 코드를 제거하기 위한 클래스
    """

    def __init__(self, event_manager: EventManager):
        """
        DefaultMonitorDataProcessor 초기화

        Args:
            event_manager: 이벤트 발생을 위한 EventManager 인스턴스
        """
        self._previous_symphony_state = None
        self._current_symphony_states = None
        self.current_acm_service_state = None
        self.current_qs_state = None

        self._symphony_success_conditions = {
            "qs_state": "On",
            "acm_service_state": "PLAY",
        }
        super().__init__(event_manager)

    def reset_state_variables(self):
        """모든 상태 변수를 초기값으로 리셋"""
        self.current_qs_state = "Off"
        self.current_acm_service_state = "N/A"
        self._current_symphony_states = {
            "qs_state": "Unknown",
            "acm_service_state": "Unknown",
        }
        self._previous_symphony_state = "Unknown"

    def process_command_result(self, handler, result):
        """
        Command 실행 결과를 처리하는 메인 메서드

        Args:
            handler: Command 핸들러 인스턴스
            result: Command 실행 결과
        """
        LOGD(
            f"DefaultMonitorDataProcessor: Processing command result from {handler.__class__.__name__}"
        )

        if result is None:
            LOGD(f"DefaultMonitorDataProcessor: Result is None, skipping processing")
            return

        # 핸들러 타입에 따라 적절한 처리 메서드 호출
        # isinstance 대신 __class__.__name__을 직접 비교하여 TypeError 방지
        if getattr(handler, "__class__", None):
            handler_name = handler.__class__.__name__

            if handler_name == "PreferenceDataCommandHandler":
                self.process_preference_data(result)
            elif handler_name == "SymphonyStatusCommandHandler":
                self.process_symphony_status(result)
            elif handler_name == "SymphonyGroupCommandHandler":
                self.process_symphony_group(result)
            elif handler_name == "SymphonyVolumeAddCommandHandler":
                self.process_symphony_volume_add(result)
            else:
                LOGD(
                    f"DefaultMonitorDataProcessor: Unknown handler type: {handler_name}"
                )

    def process_symphony_volume_add(self, actual_data: Optional[Any]):
        """
        Symphony 볼륨 조정 정보 처리

        Args:
            actual_data: 볼륨 데이터
        """
        LOGD(
            f"DefaultMonitorDataProcessor: Processing symphony volume add data: {actual_data}"
        )

        if isinstance(actual_data, int):
            # Event 발생
            self.event_manager.emit_event(
                QSMonitorEventType.SYMPHONY_VOLUME_UPDATED, {"volume": actual_data}
            )

    def process_symphony_group(self, actual_data: Optional[Any]):
        """
        Symphony 그룹 모드 처리

        Args:
            actual_data: 그룹 모드 데이터
        """
        LOGD(
            f"DefaultMonitorDataProcessor: Processing symphony group data: {actual_data}"
        )

        if isinstance(actual_data, str):
            # Event 발생
            self.event_manager.emit_event(
                QSMonitorEventType.SYMPHONY_GROUP_UPDATED, {"group_mode": actual_data}
            )

    def process_symphony_status(self, actual_data: Optional[Any]):
        """
        Symphony 상태 정보 처리

        Args:
            actual_data: Symphony 상태 데이터
        """
        LOGD(
            f"DefaultMonitorDataProcessor: Processing symphony status data: {actual_data}"
        )

        if isinstance(actual_data, dict):
            qs_state = actual_data.get("qs_state", "Error")
            sound_mode = actual_data.get("sound_mode", "Error")
            mode_type_val = actual_data.get("mode_type", "Error")

            # mode_type 값을 "Normal" 또는 "Lite"로 변환
            if mode_type_val == "Symphony":
                mode_type_display = "Normal"
            elif mode_type_val == "Symphony Lite":
                mode_type_display = "Lite"
            else:
                mode_type_display = mode_type_val

            # 상태 캐싱
            self.current_qs_state = qs_state

            # _current_symphony_states 직접 업데이트 (중요!)
            self._current_symphony_states["qs_state"] = qs_state
            LOGD(
                f"DefaultMonitorDataProcessor: Updated _current_symphony_states['qs_state'] to {qs_state}"
            )

            # Event 발생
            self.event_manager.emit_event(
                QSMonitorEventType.SYMPHONY_STATUS_UPDATED,
                {
                    "qs_state": qs_state,
                    "sound_mode": sound_mode,
                    "mode_type_display": mode_type_display,
                },
            )

            # Q-Symphony 상태 변경 Event 발생 (내부용)
            self.event_manager.emit_event(
                QSMonitorEventType.QS_STATE_CHANGED,
                {
                    "qs_state": qs_state,
                    "acm_service_state": self.current_acm_service_state,
                },
            )

            # 상태 변경 체크 및 이벤트 발생 (직접 호출)
            self._check_and_emit_symphony_state_change()

    def process_preference_data(self, actual_data: Optional[Any]):
        """
        Preference 데이터 처리 (ACM, Multiroom 상태)

        Args:
            actual_data: Preference 데이터
        """
        LOGD(f"DefaultMonitorDataProcessor: Processing preference data: {actual_data}")

        if isinstance(actual_data, dict):
            acm_service_state = actual_data.get("acm_service_state", "Error")
            multiroom_grouptype = actual_data.get("multiroom_grouptype", "Error")
            multiroom_mode = actual_data.get("multiroom_mode", "Error")

            # 상태 캐싱
            try:
                self.current_acm_service_state = acm_service_state
            except Exception:
                self.current_acm_service_state = "N/A"

            # _current_symphony_states 직접 업데이트 (중요!)
            self._current_symphony_states["acm_service_state"] = acm_service_state
            LOGD(
                f"DefaultMonitorDataProcessor: Updated _current_symphony_states['acm_service_state'] to {acm_service_state}"
            )

            # Event 발생
            self.event_manager.emit_event(
                QSMonitorEventType.PREFERENCE_DATA_UPDATED,
                {
                    "acm_service_state": acm_service_state,
                    "multiroom_grouptype": multiroom_grouptype,
                    "multiroom_mode": multiroom_mode,
                },
            )

            # ACM 상태 변경 Event 발생 (내부용)
            self.event_manager.emit_event(
                QSMonitorEventType.ACM_STATE_CHANGED,
                {
                    "qs_state": self.current_qs_state,
                    "acm_service_state": self.current_acm_service_state,
                },
            )

            # 상태 변경 체크 및 이벤트 발생 (직접 호출)
            self._check_and_emit_symphony_state_change()

    def is_symphony_success(self):
        """
        Q-Symphony 성공 조건이 모두 만족되는지 확인하는 공용 메서드

        Returns:
            bool: 모든 조건이 만족되면 True, 아니면 False
        """
        for condition_name, expected_value in self._symphony_success_conditions.items():
            current_value = self._current_symphony_states.get(condition_name, "Unknown")
            if current_value != expected_value:
                LOGD(
                    f"DefaultMonitorDataProcessor: Symphony condition not met - {condition_name}: {current_value} (expected: {expected_value})"
                )
                return False

        return True

    def _check_and_emit_symphony_state_change(self):
        """Symphony 상태 변경을 체크하고 상태 변경 시 Event 발생"""
        # 현재 상태 확인
        current_state = "On" if self.is_symphony_success() else "Off"

        # 상태 변경 확인
        if self._previous_symphony_state != current_state:
            LOGI(
                f"DefaultMonitorDataProcessor: Symphony state changed from {self._previous_symphony_state} to {current_state}"
            )

            # 이전 상태 업데이트
            self._previous_symphony_state = current_state

            # 상태 변경 이벤트 발생
            self.event_manager.emit_event(
                QSMonitorEventType.SYMPHONY_GROUP_STATE_CHANGED,
                {"state": current_state},
            )

    def register_with_command_handler(self, command_handler):
        """
        CommandHandler에 자신을 등록

        Args:
            command_handler: CommandHandler 인스턴스
        """

        # 각 커맨드 클래스 등록
        command_handler.register_class_handler(PreferenceDataCommandHandler, self)
        command_handler.register_class_handler(SymphonyStatusCommandHandler, self)
        command_handler.register_class_handler(SymphonyGroupCommandHandler, self)
        command_handler.register_class_handler(SymphonyVolumeAddCommandHandler, self)

        LOGD(f"DefaultMonitorDataProcessor: Registered with CommandHandler")

    def setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        LOGD("DefaultMonitorDataProcessor: Setting up event handlers")

        # 내부 상태 변경 이벤트 핸들러 등록
        self.event_manager.register_event_handler(
            QSMonitorEventType.QS_STATE_CHANGED, self._on_qs_state_changed_for_success
        )
        self.event_manager.register_event_handler(
            QSMonitorEventType.ACM_STATE_CHANGED, self._on_acm_state_changed_for_success
        )
        LOGD("DefaultMonitorDataProcessor: Internal signal handlers connected")

    def _on_qs_state_changed_for_success(self, args):
        """Q-Symphony 상태 변경 signal handler - 상태 업데이트 및 조건 체크"""
        qs_state = args.get("qs_state", "Unknown")
        LOGD(
            f"DefaultMonitorDataProcessor: QS state changed signal received - QS: {qs_state}"
        )

        # 상태 업데이트
        self._current_symphony_states["qs_state"] = qs_state

        # 상태 변경 체크 및 이벤트 발생
        self._check_and_emit_symphony_state_change()

    def _on_acm_state_changed_for_success(self, args):
        """ACM 상태 변경 signal handler - 상태 업데이트 및 조건 체크"""
        acm_state = args.get("acm_service_state", "Unknown")
        LOGD(
            f"DefaultMonitorDataProcessor: ACM state changed signal received - ACM: {acm_state}"
        )

        # 상태 업데이트
        self._current_symphony_states["acm_service_state"] = acm_state

        # 상태 변경 체크 및 이벤트 발생
        self._check_and_emit_symphony_state_change()

    def get_current_states(self):
        """
        현재 상태 정보 반환

        Returns:
            dict: 현재 상태 정보 딕셔너리
        """
        return {
            "qs_state": self.current_qs_state,
            "acm_service_state": self.current_acm_service_state,
            "symphony_states": self._current_symphony_states.copy(),
        }
