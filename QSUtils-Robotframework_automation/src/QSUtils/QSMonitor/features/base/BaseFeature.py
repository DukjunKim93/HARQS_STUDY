# -*- coding: utf-8 -*-
"""
BaseFeature - 모든 Feature 클래스의 공통 기능을 제공하는 추상 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from QSUtils.QSMonitor.features.base.BaseDataProcessor import BaseDataProcessor
from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.Utils.Logger import LOGD


class BaseFeature(ABC):
    """
    모든 Feature 클래스의 공통 기능을 제공하는 추상 베이스 클래스

    DataProcessor 공유 관리, 위젯 생성, 이벤트 핸들러 설정, CommandHandler 등록 등의
    공통 로직을 제공하여 중복 코드를 제거하고 일관된 인터페이스를 보장합니다.
    """

    # 클래스 변수: DataProcessor 공유를 위한 딕셔너리
    _shared_data_processors = {}

    def __init__(
        self, parent, device_context: DeviceContext, command_handler: CommandHandler
    ):
        """
        BaseFeature 초기화

        Args:
            parent: 부모 위젯 (DeviceWidget)
            device_context: DeviceContext 인스턴스
            command_handler: CommandHandler 인스턴스 (필수)
        """
        self.parent = parent
        self.device_context = device_context
        self.event_manager = device_context.event_manager
        self.command_handler = command_handler

        # EventManager를 키로 사용하여 DataProcessor 공유 또는 생성
        self.data_processor = self._get_or_create_data_processor(self.event_manager)

        # Widget은 각 인스턴스마다 생성
        self.widget = self._create_widget(parent, self.event_manager)

        # Check for session-based activation pattern
        apply_session_state = getattr(self.widget, "apply_session_state", None)

        if not callable(apply_session_state):
            raise TypeError(
                f"{self.__class__.__name__}: widget({type(self.widget).__name__}) must implement "
                f"`apply_session_state(enabled: bool)`"
            )

        # 이벤트 핸들러 자동 설정 (DataProcessor는 한 번만 설정)
        self._setup_event_handlers_if_needed()

        # CommandHandler에 자동 등록 (DataProcessor는 한 번만 등록)
        self._register_with_command_handler_if_needed()

        # DeviceContext에 command handlers 등록
        self._register_command_handlers()

    @abstractmethod
    def _create_data_processor(self, event_manager: EventManager) -> BaseDataProcessor:
        """
        DataProcessor 인스턴스를 생성하는 추상 메서드

        Args:
            event_manager: EventManager 인스턴스

        Returns:
            BaseDataProcessor: 생성된 DataProcessor 인스턴스
        """
        raise NotImplementedError("Subclasses must implement _create_data_processor")

    @abstractmethod
    def _create_widget(self, parent, event_manager: EventManager):
        """
        Widget 인스턴스를 생성하는 추상 메서드

        Args:
            parent: 부모 위젯
            event_manager: EventManager 인스턴스

        Returns:
            QWidget: 생성된 Widget 인스턴스
        """
        raise NotImplementedError("Subclasses must implement _create_widget")

    def _get_or_create_data_processor(
        self, event_manager: EventManager
    ) -> BaseDataProcessor:
        """
        EventManager를 키로 사용하여 DataProcessor를 공유하거나 생성

        Args:
            event_manager: EventManager 인스턴스

        Returns:
            BaseDataProcessor: 공유되거나 새로 생성된 DataProcessor 인스턴스
        """
        event_manager_id = id(event_manager)
        feature_name = self.__class__.__name__

        # Feature별로 다른 키 사용
        processor_key = f"{feature_name}_{event_manager_id}"

        if processor_key not in self._shared_data_processors:
            self._shared_data_processors[processor_key] = self._create_data_processor(
                event_manager
            )
            LOGD(
                f"{feature_name}: Created new shared DataProcessor for "
                f"EventManager {event_manager_id}"
            )
        else:
            LOGD(
                f"{feature_name}: Reusing shared DataProcessor for "
                f"EventManager {event_manager_id}"
            )

        return self._shared_data_processors[processor_key]

    def reset_state_variables(self):
        """모든 상태 변수를 초기값으로 리셋"""
        self.data_processor.reset_state_variables()

    def process_command_result(self, handler, result: Any):
        """
        Command 실행 결과를 처리하는 메서드

        Args:
            handler: Command 핸들러 인스턴스
            result: Command 실행 결과
        """
        self.data_processor.process_command_result(handler, result)

    def setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        self.data_processor.setup_event_handlers()
        LOGD(f"{self.__class__.__name__}: DataProcessor event handlers setup completed")

    def register_with_command_handler(self, command_handler: CommandHandler):
        """
        CommandHandler에 자신을 등록

        Args:
            command_handler: CommandHandler 인스턴스
        """
        self.data_processor.register_with_command_handler(command_handler)
        LOGD(f"{self.__class__.__name__}: Registered with CommandHandler")

    def get_widget(self):
        """
        Widget 인스턴스 반환

        Returns:
            QWidget: UI 위젯 인스턴스
        """
        return self.widget

    def apply_session_state(self, enabled: bool):
        """
        세션 상태를 UI 요소들에 적용

        Args:
            enabled: 세션 활성화 여부
        """
        self.widget.apply_session_state(enabled)

    def get_current_states(self) -> Dict[str, Any]:
        """
        현재 상태 정보 반환

        Returns:
            dict: 현재 상태 정보 딕셔너리
        """
        return self.data_processor.get_current_states()

    @classmethod
    def get_required_command_handlers(cls):
        """
        이 Feature가 필요한 command handler 클래스 목록 반환

        Returns:
            list: command handler 클래스 목록 (기본값: 빈 리스트)

        Note:
            하위 호환성을 위해 기본 구현을 제공합니다.
            향후 추상 메서드로 전환 예정입니다.
        """
        # 기본 구현: 하위 호환성을 위해 빈 리스트 반환
        return []

    @classmethod
    def get_command_handlers(cls):
        """
        이 Feature가 필요한 command handler 클래스 목록 반환 (상속 가능)

        Returns:
            list: command handler 클래스 목록
        """
        # 기본적으로 get_required_command_handlers를 호출하지만
        # 하위 클래스에서 오버라이드하여 추가적인 handlers를 포함할 수 있음
        return cls.get_required_command_handlers()

    def _setup_event_handlers_if_needed(self):
        """이벤트 핸들러 설정 (DataProcessor는 한 번만 설정)"""
        event_manager_id = id(self.event_manager)
        feature_name = self.__class__.__name__
        setup_key = f"event_handlers_setup_{feature_name}_{event_manager_id}"

        if not hasattr(self.__class__, setup_key):
            self.data_processor.setup_event_handlers()
            setattr(self.__class__, setup_key, True)
            LOGD(
                f"{feature_name}: Event handlers setup completed for "
                f"EventManager {event_manager_id}"
            )
        else:
            LOGD(
                f"{feature_name}: Event handlers already setup for "
                f"EventManager {event_manager_id}"
            )

    def _register_with_command_handler_if_needed(self):
        """CommandHandler에 등록 (DataProcessor는 한 번만 등록)"""
        command_handler_id = id(self.command_handler)
        feature_name = self.__class__.__name__
        setup_key = f"command_handler_registered_{feature_name}_{command_handler_id}"

        if not hasattr(self.__class__, setup_key):
            self.data_processor.register_with_command_handler(self.command_handler)

            # 기본 핸들러 등록 (하위 클래스에서 필요시 오버라이드 가능)
            self._register_default_handler_if_needed()

            setattr(self.__class__, setup_key, True)
            LOGD(
                f"{feature_name}: CommandHandler registration completed for "
                f"CommandHandler {command_handler_id}"
            )
        else:
            LOGD(
                f"{feature_name}: CommandHandler already registered for "
                f"CommandHandler {command_handler_id}"
            )

    def _register_default_handler_if_needed(self):
        """
        기본 핸들러 등록 (하위 클래스에서 필요시 오버라이드 가능)

        DefaultMonitorFeature에서만 기본 핸들러가 필요하므로 기본 구현은 비어있음
        """
        # 기본 구현은 비어있음 - 하위 클래스에서 필요시 오버라이드
        pass

    def _register_command_handlers(self):
        """
        DeviceContext의 FeatureRegistry에 이 Feature가 필요한 command handlers 등록
        """
        try:
            command_handlers = self.get_command_handlers()
            feature_name = self.__class__.__name__

            # FeatureRegistry에 직접 등록
            self.device_context.feature_registry.register_feature(
                feature_name, self.__class__, command_handlers
            )

            LOGD(
                f"{self.__class__.__name__}: Registered {len(command_handlers)} command handlers with FeatureRegistry"
            )
        except Exception as e:
            LOGD(
                f"{self.__class__.__name__}: Failed to register command handlers with FeatureRegistry: {e}"
            )

    @classmethod
    def cleanup_shared_resources(cls):
        """공유 리소스 정리 (테스트나 재초기화 시 사용)"""
        cls._shared_data_processors.clear()

        # 설정 플래그 정리
        attrs_to_remove = [
            attr
            for attr in dir(cls)
            if attr.startswith(("event_handlers_setup_", "command_handler_registered_"))
        ]
        for attr in attrs_to_remove:
            delattr(cls, attr)

        LOGD(f"{cls.__name__}: Cleaned up all shared resources")
