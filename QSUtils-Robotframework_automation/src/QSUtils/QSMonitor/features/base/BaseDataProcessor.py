# -*- coding: utf-8 -*-
"""
BaseDataProcessor - 모든 DataProcessor 클래스의 공통 기능을 제공하는 추상 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.Utils.Logger import LOGD


class BaseDataProcessor(ABC):
    """
    모든 DataProcessor 클래스의 공통 기능을 제공하는 추상 베이스 클래스

    공통 초기화, 상태 관리, 이벤트 핸들러 설정 등의 기능을 제공하여
    중복 코드를 제거하고 일관된 인터페이스를 보장합니다.
    """

    def __init__(self, event_manager: EventManager):
        """
        BaseDataProcessor 초기화

        Args:
            event_manager: 이벤트 발생을 위한 EventManager 인스턴스
        """
        self.event_manager = event_manager
        self.reset_state_variables()

    @abstractmethod
    def process_command_result(self, handler, result: Any):
        """
        Command 실행 결과를 처리하는 추상 메서드

        Args:
            handler: Command 핸들러 인스턴스
            result: Command 실행 결과
        """
        pass

    @abstractmethod
    def register_with_command_handler(self, command_handler: CommandHandler):
        """
        CommandHandler에 자신을 등록하는 추상 메서드

        Args:
            command_handler: CommandHandler 인스턴스
        """
        pass

    @abstractmethod
    def get_current_states(self) -> Dict[str, Any]:
        """
        현재 상태 정보를 반환하는 추상 메서드

        Returns:
            dict: 현재 상태 정보 딕셔너리
        """
        pass

    @abstractmethod
    def reset_state_variables(self):
        pass

    def setup_event_handlers(self):
        """
        이벤트 핸들러를 설정하는 기본 구현

        하위 클래스에서 필요시 오버라이드하여 특정 이벤트 핸들러를 등록할 수 있습니다.
        """
        LOGD(f"{self.__class__.__name__}: Setting up event handlers")
        LOGD(f"{self.__class__.__name__}: Event handlers setup completed")

    def _emit_event(self, event_type, data: Dict[str, Any]):
        """
        이벤트를 발생시키는 헬퍼 메서드

        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
        """
        self.event_manager.emit_event(event_type, data)
        LOGD(f"{self.__class__.__name__}: Emitted event {event_type} with data {data}")
