#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global Event Manager (App-wide Event Bus)
전역(앱 전체) 이벤트를 발행/구독하는 간단한 이벤트 버스 구현.

주의: 디바이스 로컬 작업은 각 DeviceContext의 EventManager를 통해 처리하고,
전역 버스는 코디네이터/서비스 수준의 라우팅에만 사용합니다.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, List, Optional

from QSUtils.Utils.Logger import LOGD


class GlobalEventManager:
    def __init__(self) -> None:
        # 내부적으로 문자열 키를 사용하여 서로 다른 Enum 간 충돌을 회피
        self._event_handlers: Dict[str, List[Callable]] = {}

    def register_event_handler(self, event_type: Enum, handler: Callable) -> None:
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")
        event_type_str = str(event_type.value)
        self._event_handlers.setdefault(event_type_str, [])
        if handler not in self._event_handlers[event_type_str]:
            self._event_handlers[event_type_str].append(handler)
            LOGD(f"GlobalEventManager: Registered handler for '{event_type_str}'")

    def unregister_event_handler(self, event_type: Enum, handler: Callable) -> None:
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")
        event_type_str = str(event_type.value)
        if event_type_str in self._event_handlers:
            try:
                self._event_handlers[event_type_str].remove(handler)
                if not self._event_handlers[event_type_str]:
                    del self._event_handlers[event_type_str]
                LOGD(f"GlobalEventManager: Unregistered handler for '{event_type_str}'")
            except ValueError:
                LOGD(f"GlobalEventManager: Handler not found for '{event_type_str}'")

    def emit_event(self, event_type: Enum, args: Optional[dict] = None) -> None:
        if not isinstance(event_type, Enum):
            raise TypeError("event_type must be an Enum type")
        event_type_str = str(event_type.value)
        if args is None:
            args = {}
        handlers = self._event_handlers.get(event_type_str, [])
        if not handlers:
            LOGD(f"GlobalEventManager: No handlers for '{event_type_str}'")
            return
        LOGD(
            f"GlobalEventManager: Emitting '{event_type_str}' to {len(handlers)} handler(s) with args={args}"
        )
        for handler in list(handlers):
            try:
                handler(args)
            except Exception as e:
                LOGD(
                    f"GlobalEventManager: Error in handler for '{event_type_str}': {e}"
                )


_global_event_bus: Optional[GlobalEventManager] = None


def get_global_event_bus() -> GlobalEventManager:
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = GlobalEventManager()
    return _global_event_bus
