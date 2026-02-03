#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task State Manager
태스크 상태 관리를 전담하는 클래스
"""

from datetime import datetime
from threading import Event
from typing import Optional


class TaskStateManager:
    """
    태스크의 상태 관리를 담당하는 클래스
    """

    def __init__(self, task_id: str):
        """
        TaskStateManager 초기화

        Args:
            task_id: 작업 식별자
        """
        self.task_id = task_id
        self._is_running = False
        self._is_cancelled = False
        self._retry_count = 0
        self._start_time: Optional[datetime] = None
        self._completion_event = Event()

    def start(self) -> None:
        """태스크 시작 상태로 설정"""
        self._is_running = True
        self._is_cancelled = False
        self._retry_count = 0
        self._start_time = datetime.now()
        self._completion_event.clear()

    def complete(self) -> None:
        """태스크 완료 상태로 설정"""
        self._is_running = False
        self._completion_event.set()

    def cancel(self) -> None:
        """태스크 취소 상태로 설정"""
        self._is_cancelled = True
        self._completion_event.set()

    def increment_retry(self) -> None:
        """재시도 횟수 증가"""
        self._retry_count += 1

    def is_running(self) -> bool:
        """태스크 실행 상태 확인"""
        return self._is_running

    def is_cancelled(self) -> bool:
        """태스크 취소 상태 확인"""
        return self._is_cancelled

    def is_completed(self) -> bool:
        """태스크 완료 상태 확인"""
        return self._completion_event.is_set() and not self._is_running

    def get_retry_count(self) -> int:
        """재시도 횟수 확인"""
        return self._retry_count

    def get_execution_time(self) -> float:
        """실행 시간 확인 (초)"""
        if self._start_time:
            if self.is_completed():
                return (datetime.now() - self._start_time).total_seconds()
            else:
                return (datetime.now() - self._start_time).total_seconds()
        return 0.0

    def get_start_time(self) -> Optional[datetime]:
        """시작 시간 확인"""
        return self._start_time

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        태스크 완료 대기

        Args:
            timeout: 타임아웃 시간 (초)

        Returns:
            bool: 완료되면 True, 타임아웃이면 False
        """
        return self._completion_event.wait(timeout=timeout)

    def reset(self) -> None:
        """상태 초기화"""
        self._is_running = False
        self._is_cancelled = False
        self._retry_count = 0
        self._start_time = None
        self._completion_event.clear()
