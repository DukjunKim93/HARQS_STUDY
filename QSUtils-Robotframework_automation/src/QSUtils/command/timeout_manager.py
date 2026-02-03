#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timeout Manager
태스크 타임아웃 관리를 전담하는 클래스
"""

import threading
from datetime import datetime
from typing import Callable, Optional


class TimeoutManager:
    """
    태스크의 타임아웃을 관리하는 클래스
    """

    def __init__(
        self, timeout_seconds: int, on_timeout_callback: Callable[[str], None]
    ):
        """
        TimeoutManager 초기화

        Args:
            timeout_seconds: 타임아웃 시간 (초)
            on_timeout_callback: 타임아웃 발생 시 호출될 콜백 함수
        """
        self.timeout_seconds = timeout_seconds
        self.on_timeout_callback = on_timeout_callback
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._start_time: Optional[datetime] = None

    def start_monitoring(self, command_name: str) -> None:
        """
        타임아웃 모니터링 시작

        Args:
            command_name: 모니터링할 명령어 이름
        """
        if self.timeout_seconds <= 0:
            return

        self._start_time = datetime.now()
        self._stop_event.clear()

        self._monitor_thread = threading.Thread(
            target=self._timeout_monitor, args=(command_name,), daemon=True
        )
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """타임아웃 모니터링 중지"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join(timeout=1.0)

    def is_timeout_occurred(self, start_time: datetime) -> bool:
        """
        타임아웃이 발생했는지 확인

        Args:
            start_time: 시작 시간

        Returns:
            bool: 타임아웃 발생 여부
        """
        if not start_time or self.timeout_seconds <= 0:
            return False

        elapsed = (datetime.now() - start_time).total_seconds()
        return elapsed >= self.timeout_seconds

    def get_elapsed_time(self, start_time: datetime) -> float:
        """
        경과 시간 확인

        Args:
            start_time: 시작 시간

        Returns:
            float: 경과 시간 (초)
        """
        if not start_time:
            return 0.0
        return (datetime.now() - start_time).total_seconds()

    def get_progress_percentage(self, start_time: datetime) -> int:
        """
        진행률 퍼센트 확인

        Args:
            start_time: 시작 시간

        Returns:
            int: 진행률 (0-100)
        """
        if not start_time or self.timeout_seconds <= 0:
            return 0

        elapsed = self.get_elapsed_time(start_time)
        progress = int((elapsed / self.timeout_seconds) * 100)
        return min(progress, 100)

    def _timeout_monitor(self, command_name: str) -> None:
        """
        타임아웃 모니터링 스레드

        Args:
            command_name: 모니터링할 명령어 이름
        """
        if not self._start_time:
            return

        while not self._stop_event.is_set():
            elapsed = self.get_elapsed_time(self._start_time)

            # 타임아웃 체크
            if elapsed >= self.timeout_seconds:
                timeout_msg = f"Task timeout after {self.timeout_seconds} seconds"
                self.on_timeout_callback(timeout_msg)
                break

            # 1초 대기
            self._stop_event.wait(1.0)

    def update_timeout(self, new_timeout_seconds: int) -> None:
        """
        타임아웃 시간 업데이트

        Args:
            new_timeout_seconds: 새로운 타임아웃 시간 (초)
        """
        self.timeout_seconds = new_timeout_seconds

    def get_remaining_time(self, start_time: datetime) -> float:
        """
        남은 시간 확인

        Args:
            start_time: 시작 시간

        Returns:
            float: 남은 시간 (초)
        """
        if not start_time or self.timeout_seconds <= 0:
            return 0.0

        elapsed = self.get_elapsed_time(start_time)
        remaining = self.timeout_seconds - elapsed
        return max(0.0, remaining)
