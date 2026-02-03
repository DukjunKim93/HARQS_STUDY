#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Event Type Definitions
이벤트 타입의 공통 기능을 제공하는 추상 기본 클래스입니다.
모든 이벤트 타입 Enum은 이 클래스를 상속받아 일관성을 유지합니다.
"""

from enum import Enum
from typing import Dict, Any

from QSUtils.Utils import LOGD


class BaseEventType(Enum):
    """이벤트 타입의 기본 클래스"""

    @property
    def value(self) -> str:
        """Enum 값을 문자열로 반환"""
        return super().value

    @classmethod
    def from_string(cls, value: str) -> "BaseEventType":
        """문자열로부터 Enum 값 생성"""
        for event_type in cls:
            if event_type.value == value:
                return event_type
        raise ValueError(f"Unknown event type: {value}")

    def get_expected_args(self) -> Dict[str, Any]:
        """
        이 이벤트 타입이 예상하는 인자 구조 반환
        하위 클래스에서 반드시 오버라이드해야 합니다.

        Returns:
            Dict[str, Any]: 인자 이름과 타입의 딕셔너리
                            값으로 type 또는 (type, ...) 튜플 허용
        """
        raise NotImplementedError("Subclasses must implement get_expected_args method")

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """
        이벤트 인자 구조 유효성 검사

        Args:
            args: 검증할 인자 딕셔너리

        Returns:
            bool: 유효성 검사 결과
        """
        expected_args = self.get_expected_args()

        if not expected_args:
            return True  # 인자 구조 제약이 없는 이벤트

        # 필수 인자 확인
        for arg_name, arg_type in expected_args.items():
            if arg_name not in args:
                LOGD(
                    f"EventManager: Missing required argument '{arg_name}' for event '{self.value}'"
                )
                return False

            # 타입 검사 (튜플인 경우 여러 타입 허용)
            arg_value = args[arg_name]
            if isinstance(arg_type, tuple):
                if not any(
                    arg_value is None
                    and allowed_type != bool
                    or isinstance(arg_value, allowed_type)
                    for allowed_type in arg_type
                ):
                    LOGD(
                        f"EventManager: Argument '{arg_name}' has invalid type {type(arg_value)}, expected one of {arg_type} for event '{self.value}'"
                    )
                    return False
            else:
                if not isinstance(arg_value, arg_type):
                    # None 허용 (bool 제외)
                    if arg_value is None and arg_type != bool:
                        continue
                    LOGD(
                        f"EventManager: Argument '{arg_name}' has invalid type {type(arg_value)}, expected {arg_type} for event '{self.value}'"
                    )
                    return False

        return True
