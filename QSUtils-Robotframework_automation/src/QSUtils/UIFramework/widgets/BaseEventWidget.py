#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Event Widget for QSMonitor

이벤트 기반 통신을 지원하는 위젯의 기본 클래스
"""

from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

from PySide6.QtWidgets import QWidget

from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.Utils.Logger import LOGD


class UIElementGroup(Enum):
    """UI 요소 활성화 그룹"""

    ALWAYS_ENABLED = "always_enabled"  # 항상 활성화
    ALWAYS_DISABLED = "always_disabled"  # 항상 비활성화 (읽기 전용)
    SESSION_SYNC = "session_sync"  # 세션 상태와 같이 enable/disable
    SESSION_INVERSE = "session_inverse"  # 세션 상태와 반대로 enable/disable


# TypeVar for QWidget subclasses
T = TypeVar("T", bound=QWidget)


class BaseEventWidget(QWidget):
    """
    이벤트 기반 통신을 지원하는 위젯의 기본 클래스
    - EventManager를 통한 이벤트 기반 통신
    - UI 업데이트를 위한 기본 구조 제공
    """

    def __init__(
        self, parent, event_manager: EventManager, group_name: str = "BaseEventWidget"
    ):
        """
        BaseEventWidget 초기화

        Args:
            parent: 부모 위젯 (일반적으로 DeviceWidget 또는 AutoRebootTab)
            event_manager: EventManager 인스턴스
            group_name: 그룹 이름 (로깅용)
        """
        super().__init__(parent)
        self.parent = parent
        self.event_manager = event_manager
        self.group_name = group_name
        self.ui_elements: Dict[str, Any] = {}
        self.ui_element_groups: Dict[str, UIElementGroup] = {}  # 새로운 그룹 정보 저장
        self._event_handlers_registered = False

        # EventManager 준비 알림 리스너 등록
        self._register_as_ready_listener()

        LOGD(f"{self.group_name}: BaseEventWidget initialized")

    def _setup_event_handlers(self):
        """
        이벤트 핸들러 설정
        서브클래스에서 필요한 이벤트 핸들러를 등록
        """
        LOGD(f"{self.group_name}: Setting up event handlers (base implementation)")
        # 서브클래스에서 오버라이드하여 구현

    def _register_as_ready_listener(self):
        """EventManager 준비 알림 리스너로 등록"""
        if hasattr(self.parent, "event_manager") and self.parent.event_manager:
            self.parent.event_manager.add_ready_listener(self._on_event_manager_ready)
            LOGD(f"{self.group_name}: Registered as EventManager ready listener")
        else:
            LOGD(
                f"{self.group_name}: EventManager not available for ready listener registration"
            )

    def _on_event_manager_ready(self):
        """EventManager 준비 알림 수신 시 Event 핸들러 등록"""
        if not self._event_handlers_registered:
            self.register_event_handlers()
            LOGD(
                f"{self.group_name}: EventManager ready notification received, registering event handlers"
            )

    def register_event_handlers(self):
        """Event 핸들러 등록 - 서브클래스에서 구체적인 등록 로직 구현"""
        if self._event_handlers_registered:
            return

        if hasattr(self.parent, "event_manager") and self.parent.event_manager:
            self._register_specific_event_handlers(self.parent.event_manager)
            self._event_handlers_registered = True
            LOGD(f"{self.group_name}: Event handlers registered successfully")
        else:
            LOGD(
                f"{self.group_name}: EventManager not available, deferring registration"
            )

    @abstractmethod
    def _register_specific_event_handlers(self, event_manager: EventManager):
        """구체적인 Event 핸들러 등록 로직 - 서브클래스에서 구현"""
        pass

    @abstractmethod
    def update_ui(self, data: Any) -> None:
        """
        UI 업데이트 메서드 (추상 메서드)
        서브클래스에서 반드시 구현해야 함

        Args:
            data: UI 업데이트에 필요한 데이터
        """
        pass

    def update_ui_element(self, element_name: str, value: Any) -> None:
        """
        특정 UI 요소 업데이트

        Args:
            element_name: UI 요소 이름
            value: 업데이트할 값
        """
        if element_name in self.ui_elements:
            element = self.ui_elements[element_name]
            try:
                # 위젯 타입에 따른 업데이트
                if hasattr(element, "setText"):
                    element.setText(str(value))
                elif hasattr(element, "setChecked"):
                    if isinstance(value, bool):
                        element.setChecked(value)
                    else:
                        element.setText(str(value))
                elif hasattr(element, "setValue"):
                    element.setValue(value)
                else:
                    # 기본 처리
                    element.setText(str(value))

                LOGD(
                    f"{self.group_name}: Updated UI element '{element_name}' with value: {value}"
                )
            except Exception as e:
                LOGD(
                    f"{self.group_name}: Error updating UI element '{element_name}': {e}"
                )
        else:
            LOGD(f"{self.group_name}: UI element '{element_name}' not found")

    def register_ui_element(self, element_name: str, element: Any) -> None:
        """
        UI 요소 등록

        Args:
            element_name: UI 요소 이름
            element: UI 요소 객체
        """
        self.ui_elements[element_name] = element
        LOGD(f"{self.group_name}: Registered UI element '{element_name}'")

    def get_ui_element(self, element_name: str) -> Optional[Any]:
        """
        UI 요소 가져오기

        Args:
            element_name: UI 요소 이름

        Returns:
            UI 요소 객체 또는 None
        """
        return self.ui_elements.get(element_name)

    def create_widget(
        self,
        widget_class: Type[T],
        element_name: str,
        group: UIElementGroup,
        *args,
        **kwargs,
    ) -> T:
        """
        UI 요소 생성과 동시에 그룹 등록 및 ui_elements에 저장

        Args:
            widget_class: 위젯 클래스 (QWidget 하위 클래스)
            element_name: UI 요소 이름
            group: UI 요소 그룹
            *args: 위젯 생성자 인자
            **kwargs: 위젯 생성자 키워드 인자

        Returns:
            생성된 위젯 객체 (타입 안정성 보장)
        """
        widget = widget_class(*args, **kwargs)
        self.ui_elements[element_name] = widget
        self.register_ui_element_with_group(element_name, widget, group)
        LOGD(
            f"{self.group_name}: Created and registered UI element '{element_name}' "
            f"({widget_class.__name__}) with group '{group.value}'"
        )
        return widget

    def register_ui_element_with_group(
        self, element_name: str, element: Any, group: UIElementGroup
    ) -> None:
        """
        UI 요소를 그룹 정보와 함께 등록 (새로운 기능)

        Args:
            element_name: UI 요소 이름
            element: UI 요소 객체
            group: UI 요소 그룹
        """
        self.ui_elements[element_name] = element
        self.ui_element_groups[element_name] = group
        LOGD(
            f"{self.group_name}: Registered UI element '{element_name}' with group '{group.value}'"
        )

    def apply_session_state(self, session_enabled: bool) -> None:
        """
        세션 상태를 UI 요소들에 적용 (그룹 기반 활성화)

        Args:
            session_enabled: 세션 활성화 여부
        """
        for element_name, element in self.ui_elements.items():
            try:
                if hasattr(element, "setEnabled"):
                    # 그룹 정보가 있는 경우에만 그룹 기반 동작
                    if element_name in self.ui_element_groups:
                        group = self.ui_element_groups[element_name]
                        if group == UIElementGroup.ALWAYS_ENABLED:
                            element.setEnabled(True)
                        elif group == UIElementGroup.ALWAYS_DISABLED:
                            element.setEnabled(False)
                        elif group == UIElementGroup.SESSION_SYNC:
                            element.setEnabled(session_enabled)
                        elif group == UIElementGroup.SESSION_INVERSE:
                            element.setEnabled(not session_enabled)

                        LOGD(
                            f"{self.group_name}: Set UI element '{element_name}' (group: {group.value}) "
                            f"to {'enabled' if element.isEnabled() else 'disabled'}"
                        )
                    else:
                        # 그룹 정보가 없는 경우 기존 방식대로 동작
                        element.setEnabled(session_enabled)
                        LOGD(
                            f"{self.group_name}: Set UI element '{element_name}' (no group) "
                            f"to {'enabled' if element.isEnabled() else 'disabled'}"
                        )
            except Exception as e:
                LOGD(
                    f"{self.group_name}: Error setting enabled state for '{element_name}': {e}"
                )

    def emit_event(self, event_type: str, *args, **kwargs) -> None:
        """
        이벤트 발생 (EventManager 위임)

        Args:
            event_type: 이벤트 타입
            *args: 핸들러에 전달할 위치 인자
            **kwargs: 핸들러에 전달할 키워드 인자
        """
        self.event_manager.emit_event(event_type, *args, **kwargs)

    def register_event_handler(self, event_type: str, handler) -> None:
        """
        이벤트 핸들러 등록 (EventManager 위임)

        Args:
            event_type: 이벤트 타입
            handler: 이벤트 핸들러 함수
        """
        self.event_manager.register_event_handler(event_type, handler)

    def unregister_event_handler(self, event_type: str, handler) -> None:
        """
        이벤트 핸들러 해제 (EventManager 위임)

        Args:
            event_type: 이벤트 타입
            handler: 해제할 핸들러 함수
        """
        self.event_manager.unregister_event_handler(event_type, handler)

    def cleanup(self) -> None:
        """
        리소스 정리
        서브클래스에서 필요한 정리 작업을 수행
        """
        # 등록된 이벤트 핸들러 정리
        LOGD(f"{self.group_name}: Cleaning up event handlers")
        # EventManager에서 이 그룹의 핸들러들을 정리하는 로직이 필요할 수 있음
        # 현재는 각 그룹이 자신의 핸들러를 직접 관리하도록 함
