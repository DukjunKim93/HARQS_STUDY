#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retry Policy
재시도 정책을 관리하는 클래스
"""

import time
from enum import Enum
from typing import Callable, Optional, Tuple, Any


class RetryStrategy(Enum):
    """재시도 전략 enum"""

    FIXED = "fixed"  # 고정 간격
    EXPONENTIAL = "exponential"  # 지수 증가
    LINEAR = "linear"  # 선형 증가


class RetryPolicy:
    """
    재시도 정책을 관리하는 클래스
    """

    def __init__(
        self,
        max_retries: int = 0,
        retry_strategy: RetryStrategy = RetryStrategy.FIXED,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        on_retry_callback: Optional[Callable[[int, str], None]] = None,
    ):
        """
        RetryPolicy 초기화

        Args:
            max_retries: 최대 재시도 횟수
            retry_strategy: 재시도 전략
            base_delay: 기본 대기 시간 (초)
            max_delay: 최대 대기 시간 (초)
            backoff_factor: 백오프 계수 (지수 증가 전략용)
            on_retry_callback: 재시도 시 호출될 콜백 함수
        """
        self.max_retries = max_retries
        self.retry_strategy = retry_strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.on_retry_callback = on_retry_callback
        self.current_retry_count = 0

    def should_retry(self) -> bool:
        """
        재시도해야 하는지 확인

        Returns:
            bool: 재시도 가능 여부
        """
        return self.current_retry_count < self.max_retries

    def increment_retry(self) -> None:
        """재시도 횟수 증가"""
        self.current_retry_count += 1

    def reset(self) -> None:
        """재시도 상태 초기화"""
        self.current_retry_count = 0

    def get_current_retry_count(self) -> int:
        """현재 재시도 횟수 확인"""
        return self.current_retry_count

    def get_retry_delay(self) -> float:
        """
        현재 재시도를 위한 대기 시간 계산

        Returns:
            float: 대기 시간 (초)
        """
        if self.retry_strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.retry_strategy == RetryStrategy.EXPONENTIAL:
            delay = min(
                self.base_delay * (self.backoff_factor**self.current_retry_count),
                self.max_delay,
            )
        elif self.retry_strategy == RetryStrategy.LINEAR:
            delay = min(
                self.base_delay * (self.current_retry_count + 1), self.max_delay
            )
        else:
            delay = self.base_delay

        return delay

    def wait_for_next_retry(self, command_name: str) -> None:
        """
        다음 재시도를 위해 대기

        Args:
            command_name: 명령어 이름
        """
        if not self.should_retry():
            return

        delay = self.get_retry_delay()

        # 콜백 호출
        if self.on_retry_callback:
            retry_msg = (
                f"Retry attempt {self.current_retry_count + 1}/{self.max_retries}"
            )
            self.on_retry_callback(self.current_retry_count + 1, retry_msg)

        # 대기
        if delay > 0:
            time.sleep(delay)

    def execute_with_retry(
        self,
        operation: Callable,
        operation_args: tuple = (),
        operation_kwargs: Optional[dict] = None,
        command_name: str = "Command",
    ) -> Tuple[bool, Optional[Exception], Any]:
        """
        재시도 정책에 따라 작업 실행

        Args:
            operation: 실행할 작업 함수
            operation_args: 작업 함수 인자
            operation_kwargs: 작업 함수 키워드 인자
            command_name: 명령어 이름

        Returns:
            tuple: (성공 여부, 예외, 결과)
        """
        if operation_kwargs is None:
            operation_kwargs = {}

        self.reset()
        last_exception = None

        while self.current_retry_count <= self.max_retries:
            try:
                result = operation(*operation_args, **operation_kwargs)
                return True, None, result
            except Exception as e:
                last_exception = e

                if not self.should_retry():
                    break

                self.increment_retry()
                self.wait_for_next_retry(command_name)

        return False, last_exception, None

    def get_retry_progress(self) -> int:
        """
        재시도 진행률 확인

        Returns:
            int: 진행률 (0-100)
        """
        if self.max_retries == 0:
            return 100

        progress = int((self.current_retry_count / self.max_retries) * 100)
        return min(progress, 100)

    def get_remaining_retries(self) -> int:
        """
        남은 재시도 횟수 확인

        Returns:
            int: 남은 재시도 횟수
        """
        return max(0, self.max_retries - self.current_retry_count)

    def set_max_retries(self, max_retries: int) -> None:
        """
        최대 재시도 횟수 설정

        Args:
            max_retries: 최대 재시도 횟수
        """
        self.max_retries = max_retries

    def set_retry_strategy(self, retry_strategy: RetryStrategy) -> None:
        """
        재시도 전략 설정

        Args:
            retry_strategy: 재시도 전략
        """
        self.retry_strategy = retry_strategy

    def is_exhausted(self) -> bool:
        """
        재시도 횟수가 모두 소진되었는지 확인

        Returns:
            bool: 소진 여부
        """
        return self.current_retry_count >= self.max_retries
