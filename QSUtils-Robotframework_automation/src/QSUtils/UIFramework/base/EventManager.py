#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event Manager for QSMonitor
이벤트 기반 통신을 관리하는 클래스
"""

from enum import Enum
from typing import Dict, List, Callable

from QSUtils.Utils.Logger import LOGD


class EventManager:
    """
    이벤트 기반 통신을 관리하는 클래스
    - 이벤트 핸들러 등록/해제
    - 이벤트 발생 및 핸들러 호출
    - 준비 알림 기능 (EventManager 준비 시 자기 등록 유도)
    """

    def __init__(self):
        """EventManager 초기화"""
        # 내부적으로는 이벤트 문자열 값을 키로 사용하여 여러 Enum 타입 간의 충돌 방지
        # 예: CommonEventType.REBOOT_REQUESTED.value == "reboot_requested"
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._is_ready = False
        self._ready_listeners: List[Callable] = []  # 준비 알림을 받을 컴포넌트들

    def register_event_handler(self, event_type: Enum, handler: Callable) -> None:
        """
        이벤트 핸들러 등록

        Args:
            event_type: 이벤트 타입 (Enum만 허용)
            handler: 이벤트 핸들러 함수
        """
        # Enum 타입에서 문자열 값으로 변환
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")

        event_type_str = str(event_type.value)

        if event_type_str not in self._event_handlers:
            self._event_handlers[event_type_str] = []

        if handler not in self._event_handlers[event_type_str]:
            self._event_handlers[event_type_str].append(handler)
            LOGD(f"EventManager: Registered handler for event '{event_type_str}'")
        else:
            LOGD(
                f"EventManager: Handler already registered for event '{event_type_str}'"
            )

    def unregister_event_handler(self, event_type: Enum, handler: Callable) -> None:
        """
        이벤트 핸들러 해제

        Args:
            event_type: 이벤트 타입 (Enum만 허용)
            handler: 해제할 핸들러 함수
        """
        # Enum 타입에서 문자열 값으로 변환
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")

        event_type_str = str(event_type.value)

        if event_type_str in self._event_handlers:
            try:
                self._event_handlers[event_type_str].remove(handler)
                LOGD(f"EventManager: Unregistered handler for event '{event_type_str}'")

                # 핸들러가 없으면 이벤트 타입도 제거
                if not self._event_handlers[event_type_str]:
                    del self._event_handlers[event_type_str]
            except ValueError:
                LOGD(f"EventManager: Handler not found for event '{event_type_str}'")

    def emit_event(self, event_type: Enum, args=None) -> None:
        """
        이벤트 발생 및 핸들러 호출

        Args:
            event_type: 이벤트 타입 (Enum만 허용)
            args: 이벤트 데이터를 담은 딕셔너리
        """
        # Enum 타입에서 문자열 값으로 변환
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")

        event_type_str = str(event_type.value)

        # 인자 구조 유효성 검사 (개발 모드에서만)
        if __debug__ and args is not None:
            # validate_args 메서드가 있는 경우에만 유효성 검사 수행
            if hasattr(event_type, "validate_args") and callable(
                getattr(event_type, "validate_args")
            ):
                if not event_type.validate_args(args):
                    LOGD(
                        f"EventManager: Invalid args structure for event '{event_type_str}': {args}"
                    )

        if event_type_str not in self._event_handlers:
            LOGD(f"EventManager: No handlers registered for event '{event_type_str}'")
            return

        # args가 None이면 빈 딕셔너리로 처리
        if args is None:
            args = {}
        elif not isinstance(args, dict):
            LOGD(
                f"EventManager: Warning: 'args' should be a dictionary, got {type(args)}"
            )
            args = {}

        LOGD(f"EventManager: Emitting event '{event_type_str}' with args={args}")

        # 등록된 모든 핸들러 호출
        for handler in self._event_handlers[event_type_str][
            :
        ]:  # 복사본으로 순회 (호출 중 핸들러 삭제 대비)
            try:
                handler(args)
            except Exception as e:
                LOGD(
                    f"EventManager: Error in handler for event '{event_type_str}': {e}"
                )

    def get_registered_events(self) -> List[str]:
        """
        등록된 이벤트 타입 목록 반환

        Returns:
            List[str]: 등록된 이벤트 타입 목록
        """
        return list(self._event_handlers.keys())

    def get_handler_count(self, event_type: Enum) -> int:
        """
        특정 이벤트 타입에 등록된 핸들러 수 반환

        Args:
            event_type: 이벤트 타입 (Enum만 허용)

        Returns:
            int: 핸들러 수
        """
        # Enum 타입에서 문자열 값으로 변환
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")

        event_type_str = str(event_type.value)
        return len(self._event_handlers.get(event_type_str, []))

    def clear_all_handlers(self) -> None:
        """모든 이벤트 핸들러 제거"""
        self._event_handlers.clear()
        LOGD("EventManager: Cleared all event handlers")

    def clear_event_handlers(self, event_type: Enum) -> None:
        """
        특정 이벤트 타입의 모든 핸들러 제거

        Args:
            event_type: 이벤트 타입 (Enum만 허용)
        """
        # Enum 타입에서 문자열 값으로 변환
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")

        event_type_str = str(event_type.value)

        if event_type_str in self._event_handlers:
            del self._event_handlers[event_type_str]
            LOGD(f"EventManager: Cleared all handlers for event '{event_type_str}'")

    def set_ready(self) -> None:
        """
        EventManager가 준비되었음을 알림
        모든 준비 알림 리스너에게 알림을 보내 자기 등록을 유도
        """
        if not self._is_ready:
            self._is_ready = True
            LOGD("EventManager: EventManager is now ready, notifying listeners")
            self._notify_ready_listeners()
        else:
            LOGD("EventManager: EventManager is already ready")

    def _notify_ready_listeners(self) -> None:
        """
        준비된 컴포넌트들에게 알림
        각 리스너를 호출하여 Event 핸들러 등록을 유도
        """
        LOGD(f"EventManager: Notifying {len(self._ready_listeners)} ready listeners")

        for listener in self._ready_listeners:
            try:
                listener()
                LOGD("EventManager: Successfully notified ready listener")
            except Exception as e:
                LOGD(f"EventManager: Error notifying ready listener: {e}")

        # 알림 완료 후 리스너 목록 정리 (선택적)
        self._ready_listeners.clear()
        LOGD("EventManager: Cleared ready listeners list after notification")

    def add_ready_listener(self, listener: Callable) -> None:
        """
        EventManager 준비 알림 리스너 등록

        Args:
            listener: EventManager 준비 시 호출될 함수
        """
        if self._is_ready:
            # 이미 준비된 상태면 즉시 호출
            LOGD(
                "EventManager: EventManager already ready, calling listener immediately"
            )
            try:
                listener()
            except Exception as e:
                LOGD(f"EventManager: Error calling immediate ready listener: {e}")
        else:
            # 아직 준비되지 않았으면 리스너 목록에 추가
            self._ready_listeners.append(listener)
            LOGD(
                f"EventManager: Added ready listener (total: {len(self._ready_listeners)})"
            )

    def is_ready(self) -> bool:
        """
        EventManager가 준비되었는지 확인

        Returns:
            bool: 준비 상태
        """
        return self._is_ready
