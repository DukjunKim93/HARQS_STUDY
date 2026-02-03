#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CommandHandler - 커맨드 핸들러 등록 및 라우팅을 담당하는 클래스
"""

from typing import Callable, Dict, Any, Optional

from QSUtils.Utils.Logger import LOGD


class CommandHandler:
    """
    커맨드 핸들러 등록 및 라우팅을 담당하는 클래스

    DeviceWidget에서 각 커맨드 타입별 처리 함수를 등록하고
    일관된 방식으로 커맨드를 라우팅하기 위한 클래스
    """

    def __init__(self):
        """CommandHandler 초기화"""
        self.handlers: Dict[str, Callable] = {}
        self.default_handler: Optional[Callable] = None
        self._registered_classes: set = set()  # 등록된 클래스 추적용

    def register_handler(self, command_class_name: str, handler_function: Callable):
        """
        커맨드 클래스 이름에 핸들러 함수 등록

        Args:
            command_class_name: 커맨드 클래스 이름 (예: 'NetworkInterfaceCommand')
            handler_function: 핸들러 함수 (handler, result)를 인자로 받음
        """
        self.handlers[command_class_name] = handler_function
        LOGD(f"CommandHandler: Registered handler for {command_class_name}")

    def register_class_handler(self, command_class: type, processor_instance):
        """
        커맨드 클래스와 프로세서 인스턴스를 직접 등록

        Args:
            command_class: 커맨드 클래스 타입
            processor_instance: 프로세서 인스턴스 (process_command_result 메서드를 가져야 함)
        """
        command_class_name = command_class.__name__

        # 중복 등록 확인
        if command_class_name in self._registered_classes:
            LOGD(
                f"CommandHandler: {command_class_name} already registered, skipping duplicate registration"
            )
            return

        if hasattr(processor_instance, "process_command_result"):
            self.handlers[command_class_name] = (
                processor_instance.process_command_result
            )
            self._registered_classes.add(command_class_name)
            LOGD(
                f"CommandHandler: Registered class handler for {command_class_name} -> {processor_instance.__class__.__name__}"
            )
        else:
            LOGD(
                f"CommandHandler: Processor {processor_instance.__class__.__name__} does not have process_command_result method"
            )

    def register_default_handler(self, handler_function: Callable):
        """
        기본 핸들러 등록 (등록된 핸들러가 없을 때 사용)

        Args:
            handler_function: 기본 핸들러 함수 (handler, result)를 인자로 받음
        """
        # 중복 등록 확인
        if self.default_handler is not None:
            LOGD(
                "CommandHandler: Default handler already registered, skipping duplicate registration"
            )
            return

        self.default_handler = handler_function
        LOGD("CommandHandler: Registered default handler")

    def handle_command(self, handler, result: Any) -> bool:
        """
        등록된 핸들러를 통해 커맨드 처리
        등록된 핸들러가 없는 경우에만 로깅하고 차단

        Args:
            handler: 커맨드 핸들러 인스턴스
            result: 커맨드 실행 결과

        Returns:
            bool: 핸들러가 성공적으로 실행되었으면 True, 없으면 False
        """
        if handler is None:
            LOGD("CommandHandler: Handler is None, cannot process")
            return False

        command_class_name = handler.__class__.__name__

        # 등록된 핸들러가 있는지 확인
        if command_class_name in self.handlers:
            LOGD(
                f"CommandHandler: Processing {command_class_name} with registered handler"
            )
            try:
                self.handlers[command_class_name](handler, result)
                return True
            except Exception as e:
                LOGD(f"CommandHandler: Error in handler for {command_class_name}: {e}")
                return False
        else:
            # 등록된 핸들러가 없는 경우 - 이것이 핵심 문제 해결
            LOGD(
                f"CommandHandler: No handler registered for {command_class_name} - blocking result"
            )
            LOGD(
                f"CommandHandler: This prevents unregistered command results from reaching processors"
            )
            return False

    def handle_with_default(self, handler, result: Any) -> bool:
        """
        등록된 핸들러로 처리하고, 없으면 기본 핸들러 사용

        Args:
            handler: 커맨드 핸들러 인스턴스
            result: 커맨드 실행 결과

        Returns:
            bool: 핸들러가 성공적으로 실행되었으면 True
        """
        # 먼저 등록된 핸들러로 시도
        if self.handle_command(handler, result):
            return True

        # 등록된 핸들러가 없으면 기본 핸들러 사용
        if self.default_handler:
            LOGD(
                f"CommandHandler: Using default handler for {handler.__class__.__name__}"
            )
            try:
                self.default_handler(handler, result)
                return True
            except Exception as e:
                LOGD(f"CommandHandler: Error in default handler: {e}")
                return False
        else:
            LOGD(
                f"CommandHandler: No handler and no default handler for {handler.__class__.__name__}"
            )
            return False

    def get_registered_handlers(self) -> Dict[str, str]:
        """
        등록된 핸들러 목록 반환

        Returns:
            dict: {command_class_name: handler_function_name}
        """
        return {
            class_name: handler.__name__
            for class_name, handler in self.handlers.items()
        }

    def clear_handlers(self):
        """모든 핸들러 제거"""
        self.handlers.clear()
        self.default_handler = None
        self._registered_classes.clear()
        LOGD("CommandHandler: All handlers cleared")
