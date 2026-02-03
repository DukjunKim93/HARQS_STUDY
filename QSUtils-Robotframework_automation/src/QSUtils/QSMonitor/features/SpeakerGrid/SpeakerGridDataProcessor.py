# -*- coding: utf-8 -*-
"""
SpeakerGridDataProcessor - 스피커 그리드 상태 데이터 처리 및 이벤트 발생 담당 클래스
"""

from typing import Any, Dict

from QSUtils.QSMonitor.features.base.BaseDataProcessor import BaseDataProcessor
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.Utils import LOGD, LOGE
from QSUtils.command.cmd_pp_speaker_remap import SpeakerRemapCommandHandler
from QSUtils.command.cmd_pp_surround_speaker_remap import (
    SurroundSpeakerRemapCommandHandler,
)


class SpeakerGridDataProcessor(BaseDataProcessor):
    """스피커 그리드 상태 데이터 처리를 담당하는 클래스"""

    def __init__(self, event_manager: EventManager):
        # 스피커 그리드 상태 저장
        self.speaker_remap_states = {}
        self.surround_speaker_states = {}
        super().__init__(event_manager)

    def process_command_result(self, handler, result):
        """커맨드 실행 결과 처리"""
        try:
            handler_name = handler.__class__.__name__

            if handler_name == "SpeakerRemapCommandHandler":
                self._process_speaker_remap_result(result)
            elif handler_name == "SurroundSpeakerRemapCommandHandler":
                self._process_surround_speaker_result(result)
            else:
                LOGD(f"SpeakerGridDataProcessor: Unknown handler {handler_name}")

        except Exception as e:
            LOGE(f"SpeakerGridDataProcessor: Error processing command result: {e}")

    def _process_speaker_remap_result(self, result):
        """스피커 리맵핑 결과 처리"""
        try:
            # 원시 데이터(int)가 직접 전달된 경우
            if isinstance(result, int):
                position_id = result
                self.speaker_remap_states = {"position_id": position_id}

                # 이벤트 발생
                from QSUtils.QSMonitor.core.Events import QSMonitorEventType

                self.event_manager.emit_event(
                    QSMonitorEventType.SPEAKER_GRID_UPDATED,
                    {"update_type": "speaker_remap", "data": self.speaker_remap_states},
                )

                LOGD(
                    f"SpeakerGridDataProcessor: Speaker remap updated: {self.speaker_remap_states}"
                )
            else:
                LOGE(
                    f"SpeakerGridDataProcessor: Invalid speaker remap data type: {type(result)}"
                )

        except Exception as e:
            LOGE(
                f"SpeakerGridDataProcessor: Error processing speaker remap result: {e}"
            )

    def _process_surround_speaker_result(self, result):
        """서라운드 스피커 결과 처리"""
        try:
            # 원시 데이터(list)가 직접 전달된 경우
            if isinstance(result, list):
                self.surround_speaker_states = result

                # 이벤트 발생
                from QSUtils.QSMonitor.core.Events import QSMonitorEventType

                self.event_manager.emit_event(
                    QSMonitorEventType.SPEAKER_GRID_UPDATED,
                    {
                        "update_type": "surround_speaker",
                        "data": self.surround_speaker_states,
                    },
                )

                LOGD(
                    f"SpeakerGridDataProcessor: Surround speaker updated: {self.surround_speaker_states}"
                )
            else:
                LOGE(
                    f"SpeakerGridDataProcessor: Invalid surround speaker data type: {type(result)}"
                )

        except Exception as e:
            LOGE(
                f"SpeakerGridDataProcessor: Error processing surround speaker result: {e}"
            )

    def get_speaker_remap_states(self):
        """현재 스피커 리맵핑 상태 반환"""
        return self.speaker_remap_states.copy()

    def get_surround_speaker_states(self):
        """현재 서라운드 스피커 상태 반환"""
        return self.surround_speaker_states.copy()

    def reset_state_variables(self):
        """상태 변수 초기화"""
        self.speaker_remap_states.clear()
        self.surround_speaker_states.clear()
        LOGD("SpeakerGridDataProcessor: State variables reset")

    def get_current_states(self) -> Dict[str, Any]:
        """
        현재 상태 정보 반환

        Returns:
            dict: 현재 상태 정보 딕셔너리
        """
        return {
            "speaker_remap_states": self.speaker_remap_states.copy(),
            "surround_speaker_states": self.surround_speaker_states.copy(),
        }

    def register_with_command_handler(self, command_handler):
        """CommandHandler에 자신을 등록"""

        command_handler.register_class_handler(SpeakerRemapCommandHandler, self)
        command_handler.register_class_handler(SurroundSpeakerRemapCommandHandler, self)

        LOGD("SpeakerGridDataProcessor: Registered with CommandHandler")

    def setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        LOGD("SpeakerGridDataProcessor: Setting up event handlers")
        # SpeakerGridDataProcessor는 특별히 처리할 이벤트 핸들러가 없음
        # 필요한 경우 여기에 이벤트 핸들러 등록
        LOGD("SpeakerGridDataProcessor: Event handlers setup completed")
