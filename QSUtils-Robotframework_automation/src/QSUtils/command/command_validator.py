#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Validator
명령어 실행 전 검증을 전담하는 클래스
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List, Callable

from QSUtils.command.command_constants import CommandResult
from QSUtils.command.error_handler import CommandErrorHandler


class ValidationRule(Enum):
    """검증 규칙 타입"""

    REQUIRED = "required"  # 필수 값
    NOT_EMPTY = "not_empty"  # 비어있지 않음
    MIN_LENGTH = "min_length"  # 최소 길이
    MAX_LENGTH = "max_length"  # 최대 길이
    PATTERN = "pattern"  # 정규식 패턴
    ENUM_VALUE = "enum_value"  # Enum 값
    CUSTOM = "custom"  # 커스텀 검증


class ValidationResult:
    """검증 결과 클래스"""

    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message

    @property
    def is_failure(self) -> bool:
        """실패 여부"""
        return not self.is_valid

    def to_command_result(self) -> Optional[CommandResult]:
        """CommandResult로 변환"""
        if self.is_failure:
            return CommandResult.failure(self.error_message)
        return None


class ValidationRuleBuilder:
    """검증 규칙 빌더"""

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.rules: List[tuple] = []

    def required(self) -> "ValidationRuleBuilder":
        """필수 값 검증 추가"""
        self.rules.append((ValidationRule.REQUIRED, None))
        return self

    def not_empty(self) -> "ValidationRuleBuilder":
        """비어있지 않음 검증 추가"""
        self.rules.append((ValidationRule.NOT_EMPTY, None))
        return self

    def min_length(self, length: int) -> "ValidationRuleBuilder":
        """최소 길이 검증 추가"""
        self.rules.append((ValidationRule.MIN_LENGTH, length))
        return self

    def max_length(self, length: int) -> "ValidationRuleBuilder":
        """최대 길이 검증 추가"""
        self.rules.append((ValidationRule.MAX_LENGTH, length))
        return self

    def pattern(self, pattern: str) -> "ValidationRuleBuilder":
        """정규식 패턴 검증 추가"""
        self.rules.append((ValidationRule.PATTERN, pattern))
        return self

    def enum_value(self, enum_class: type) -> "ValidationRuleBuilder":
        """Enum 값 검증 추가"""
        self.rules.append((ValidationRule.ENUM_VALUE, enum_class))
        return self

    def custom(
        self, validator: Callable[[Any], ValidationResult]
    ) -> "ValidationRuleBuilder":
        """커스텀 검증 추가"""
        self.rules.append((ValidationRule.CUSTOM, validator))
        return self

    def build(self) -> List[tuple]:
        """규칙 리스트 반환"""
        return self.rules


class BaseCommandValidator(ABC):
    """
    명령어 실행 전 사전 검증을 담당하는 기본 클래스
    """

    # simple pluggable precheck registry: {command_name: [callable(device, shell_command, kwargs)->Optional[CommandResult]]}
    _precheck_registry: Dict[
        str, List[Callable[[Any, str, Dict[str, Any]], Optional[CommandResult]]]
    ] = {}

    @classmethod
    def register_precheck(
        cls,
        command_name: str,
        precheck: Callable[[Any, str, Dict[str, Any]], Optional[CommandResult]],
    ) -> None:
        cls._precheck_registry.setdefault(command_name, []).append(precheck)

    def __init__(self, device: Any, command_name: str):
        """
        BaseCommandValidator 초기화

        Args:
            device: ADBDevice 인스턴스
            command_name: 검증할 명령어 이름
        """
        self.device = device
        self.command_name = command_name
        self.validation_rules: Dict[str, List[tuple]] = {}

    def validate_all(self, shell_command: str, **kwargs) -> Optional[CommandResult]:
        """
        모든 사전 검증을 수행합니다.

        Args:
            shell_command: 검증할 쉘 명령어
            **kwargs: 추가 파라미터

        Returns:
            Optional[CommandResult]: 검증 실패 시 CommandResult, 성공 시 None
        """
        # 1) 플러그인 프리체크 (등록 기반)
        for precheck in self._precheck_registry.get(self.command_name, []):
            try:
                result = precheck(self.device, shell_command, dict(kwargs))
                if result is not None:
                    return result
            except Exception as e:
                # 프리체크 예외는 안전하게 로깅만 하고 계속 진행
                CommandErrorHandler.handle_command_execution_error(
                    e, self.command_name, "precheck"
                )

        # 2) 디바이스 연결 상태 검증
        device_result = self.validate_device_connection()
        if device_result is not None:
            return device_result

        # 3) 쉘 명령어 검증
        command_result = self.validate_shell_command(shell_command)
        if command_result is not None:
            return command_result

        # 4) 파라미터 검증
        param_result = self.validate_parameters(**kwargs)
        if param_result is not None:
            return param_result

        return None

    def validate_device_connection(self) -> Optional[CommandResult]:
        """
        디바이스 연결 상태를 검증합니다.

        Returns:
            Optional[CommandResult]: 검증 실패 시 CommandResult, 성공 시 None
        """
        if not self.device:
            error_msg = "Device is None"
            CommandErrorHandler.log_error_message(self.command_name, error_msg)
            return CommandResult.failure(error_msg)

        if not hasattr(self.device, "is_connected") or not self.device.is_connected:
            error_msg = "Device not connected"
            CommandErrorHandler.log_error_message(self.command_name, error_msg)
            return CommandResult.failure(error_msg)

        return None

    def validate_shell_command(self, shell_command: str) -> Optional[CommandResult]:
        """
        쉘 명령어를 검증합니다.

        Args:
            shell_command: 검증할 쉘 명령어

        Returns:
            Optional[CommandResult]: 검증 실패 시 CommandResult, 성공 시 None
        """
        if not shell_command or not shell_command.strip():
            error_msg = "Shell command is empty"
            CommandErrorHandler.log_error_message(self.command_name, error_msg)
            return CommandResult.failure(error_msg)

        return None

    def validate_parameters(self, **kwargs) -> Optional[CommandResult]:
        """
        파라미터를 검증합니다.

        Args:
            **kwargs: 검증할 파라미터들

        Returns:
            Optional[CommandResult]: 검증 실패 시 CommandResult, 성공 시 None
        """
        for field_name, value in kwargs.items():
            if field_name in self.validation_rules:
                result = self._validate_field(field_name, value)
                if result.is_failure:
                    return result.to_command_result()

        return None

    def _validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """
        특정 필드를 검증합니다.

        Args:
            field_name: 필드 이름
            value: 필드 값

        Returns:
            ValidationResult: 검증 결과
        """
        if field_name not in self.validation_rules:
            return ValidationResult(True)

        rules = self.validation_rules[field_name]

        for rule_type, rule_param in rules:
            result = self._apply_rule(field_name, value, rule_type, rule_param)
            if result.is_failure:
                return result

        return ValidationResult(True)

    def _apply_rule(
        self, field_name: str, value: Any, rule_type: ValidationRule, rule_param: Any
    ) -> ValidationResult:
        """
        개별 검증 규칙을 적용합니다.

        Args:
            field_name: 필드 이름
            value: 필드 값
            rule_type: 규칙 타입
            rule_param: 규칙 파라미터

        Returns:
            ValidationResult: 검증 결과
        """
        if rule_type == ValidationRule.REQUIRED:
            if value is None:
                return ValidationResult(False, f"{field_name} is required")

        elif rule_type == ValidationRule.NOT_EMPTY:
            if value is None or (isinstance(value, str) and not value.strip()):
                return ValidationResult(False, f"{field_name} cannot be empty")

        elif rule_type == ValidationRule.MIN_LENGTH:
            if isinstance(value, str) and len(value) < rule_param:
                return ValidationResult(
                    False, f"{field_name} must be at least {rule_param} characters"
                )

        elif rule_type == ValidationRule.MAX_LENGTH:
            if isinstance(value, str) and len(value) > rule_param:
                return ValidationResult(
                    False, f"{field_name} must be at most {rule_param} characters"
                )

        elif rule_type == ValidationRule.PATTERN:
            import re

            if isinstance(value, str) and not re.match(rule_param, value):
                return ValidationResult(False, f"{field_name} format is invalid")

        elif rule_type == ValidationRule.ENUM_VALUE:
            if isinstance(value, str):
                try:
                    rule_param(value)
                except ValueError:
                    valid_values = [e.value for e in rule_param]
                    return ValidationResult(
                        False, f"{field_name} must be one of: {valid_values}"
                    )

        elif rule_type == ValidationRule.CUSTOM:
            if callable(rule_param):
                return rule_param(value)

        return ValidationResult(True)

    def add_validation_rules(
        self, field_name: str, builder: ValidationRuleBuilder
    ) -> None:
        """
        필드에 검증 규칙을 추가합니다.

        Args:
            field_name: 필드 이름
            builder: 검증 규칙 빌더
        """
        self.validation_rules[field_name] = builder.build()

    @abstractmethod
    def setup_validation_rules(self) -> None:
        """
        검증 규칙을 설정합니다.
        하위 클래스에서 이 메서드를 구현해야 합니다.
        """
        pass


class CommandValidator(BaseCommandValidator):
    """
    기본 명령어 검증기
    """

    def __init__(self, device: Any, command_name: str):
        super().__init__(device, command_name)
        self.setup_validation_rules()

    def setup_validation_rules(self) -> None:
        """기본 검증 규칙 설정 (파라미터 검증 없음)"""
        pass


class ConnectionManagerCommandValidator(BaseCommandValidator):
    """
    ConnectionManagerCommand를 위한 특화된 검증기
    """

    def __init__(self, device: Any, command_name: str):
        super().__init__(device, command_name)
        self.setup_validation_rules()

    def setup_validation_rules(self) -> None:
        """ConnectionManagerCommand 검증 규칙 설정"""
        # action 파라미터 검증 규칙
        self.add_validation_rules(
            "action",
            ValidationRuleBuilder("action")
            .required()
            .not_empty()
            .enum_value(self._get_connection_manager_actions()),
        )

        # setup 액션일 경우 추가 검증 규칙
        def validate_setup_params(value: Dict[str, Any]) -> ValidationResult:
            if value.get("action") == "setup":
                if not value.get("ssid") or not value.get("password"):
                    return ValidationResult(
                        False, "SSID and password are required for 'setup' action"
                    )
            return ValidationResult(True)

        self.add_validation_rules(
            "setup_params",
            ValidationRuleBuilder("setup_params").custom(validate_setup_params),
        )

    def _get_connection_manager_actions(self):
        """ConnectionManagerActions enum 반환 (지연 임포트)"""
        try:
            from QSUtils.command.command_constants import ConnectionManagerActions

            return ConnectionManagerActions
        except ImportError:
            # 임포트 실패 시 기본 값 반환
            class DummyActions:
                def __init__(self, value):
                    self.value = value

            return DummyActions


class NetworkInterfaceCommandValidator(BaseCommandValidator):
    """
    NetworkInterfaceCommand를 위한 특화된 검증기
    """

    def __init__(self, device: Any, command_name: str):
        super().__init__(device, command_name)
        self.setup_validation_rules()

    def setup_validation_rules(self) -> None:
        """NetworkInterfaceCommand 검증 규칙 설정"""
        # interface 파라미터 검증 규칙
        self.add_validation_rules(
            "interface",
            ValidationRuleBuilder("interface").not_empty().pattern(r"^[a-zA-Z0-9_-]+$"),
        )
