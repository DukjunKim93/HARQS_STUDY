import threading
from datetime import datetime
from typing import Callable, Optional, Any

from PySide6.QtCore import QRunnable, QObject, Signal

from QSUtils.Utils.Logger import LOGD, LOGE
from QSUtils.command.base_command import BaseCommand
from QSUtils.command.command_constants import CommandResult
from QSUtils.command.retry_policy import RetryPolicy, RetryStrategy
from QSUtils.command.task_state_manager import TaskStateManager
from QSUtils.command.timeout_manager import TimeoutManager


class CommandTaskSignals(QObject):
    """CommandTask를 위한 시그널 클래스"""

    # 태스크 상태 시그널
    task_started = Signal(str)  # command_name
    task_completed = Signal(str, bool, str)  # command_name, success, message
    task_progress = Signal(str, int, str)  # command_name, progress, message
    task_error = Signal(str, str)  # command_name, error_message

    # 결과 시그널
    result_ready = Signal(object, object)  # command, result_data


class CommandTask(QRunnable):
    """
    비동기 명령어 실행을 위한 고급 태스크 클래스
    타임아웃, 재시도, 진행 상황 추적 등의 기능을 제공
    """

    def __init__(
        self,
        handler: BaseCommand,
        callback: Callable[[BaseCommand, Optional[Any]], None],
        timeout: int = 30,
        max_retries: int = 0,
        task_id: str = None,
    ):
        """
        CommandTask 초기화

        Args:
            handler: 실행할 BaseCommand 인스턴스
            callback: 결과 처리 콜백 함수
            timeout: 타임아웃 시간 (초)
            max_retries: 최대 재시도 횟수
            task_id: 작업 식별자
        """
        super().__init__()
        self.handler = handler
        self.callback = callback
        self.timeout = timeout
        self.max_retries = max_retries
        self.task_id = (
            task_id
            or f"{handler.__class__.__name__}_{datetime.now().strftime('%H%M%S%f')}"
        )

        # 상태 관리자 초기화
        self.state_manager = TaskStateManager(self.task_id)

        # 타임아웃 관리자 초기화
        self.timeout_manager = TimeoutManager(
            timeout_seconds=self.timeout, on_timeout_callback=self._on_timeout
        )

        # 재시도 정책 초기화
        self.retry_policy = RetryPolicy(
            max_retries=self.max_retries,
            retry_strategy=RetryStrategy.FIXED,
            base_delay=1.0,
            on_retry_callback=self._on_retry,
        )

        # 시그널
        self.signals = CommandTaskSignals()

        # Auto-delete 설정
        self.setAutoDelete(True)

    def run(self):
        """태스크 실행 메인 로직"""
        try:
            # 상태 관리자 시작
            self.state_manager.start()

            if self.state_manager.is_cancelled():
                self._emit_task_completed(False, "Task cancelled before start")
                return

            command_name = self.handler.__class__.__name__
            LOGD(
                f"CommandTask: Starting async command execution for {command_name} (ID: {self.task_id})"
            )
            self.signals.task_started.emit(command_name)

            # 타임아웃 모니터링 시작
            self.timeout_manager.start_monitoring(command_name)

            # 명령어 실행
            self._execute_with_retry()

        except Exception as e:
            error_msg = f"CommandTask: Exception occurred: {str(e)}"
            LOGE(error_msg)
            self.signals.task_error.emit(self.handler.__class__.__name__, error_msg)

            if not self.state_manager.is_cancelled():
                self.callback(self.handler, None)

        finally:
            self._cleanup()

    def _execute_with_retry(self):
        """재시도 로직을 포함한 명령어 실행"""
        while (
            self.retry_policy.should_retry() and not self.state_manager.is_cancelled()
        ):
            try:
                # 재시도 상태 처리
                if self.retry_policy.get_current_retry_count() > 0:
                    self.retry_policy.wait_for_next_retry(
                        self.handler.__class__.__name__
                    )
                    self.state_manager.increment_retry()

                # BaseCommand의 비동기 실행 메서드를 사용하도록 콜백 래핑
                result_event = threading.Event()
                result_container = {"result": None}

                def command_result_callback(result: CommandResult):
                    """BaseCommand의 CommandResult를 기존 콜백 형식으로 변환"""
                    if self.state_manager.is_cancelled():
                        return

                    result_container["result"] = result
                    result_event.set()

                    if result.success:
                        LOGD(
                            f"CommandTask: Command succeeded for {self.handler.__class__.__name__}"
                        )
                        self.signals.result_ready.emit(self.handler, result.data)
                        self.callback(self.handler, result.data)
                    else:
                        error_msg = f"Command failed: {result.error}"
                        LOGD(f"CommandTask: {error_msg}")
                        self.signals.task_error.emit(
                            self.handler.__class__.__name__, error_msg
                        )

                        # 재시도 가능한 경우
                        if self.retry_policy.should_retry():
                            self.retry_policy.increment_retry()
                            return
                        else:
                            self.callback(self.handler, None)

                # BaseCommand의 비동기 실행 메서드 호출
                self.handler.execute_async(command_result_callback)

                # 결과 대기
                start_time = self.state_manager.get_start_time()
                if start_time and result_event.wait(
                    timeout=self.timeout_manager.get_remaining_time(start_time)
                ):
                    # 성공 또는 최종 실패
                    break
                else:
                    # 타임아웃 체크
                    if start_time and self.timeout_manager.is_timeout_occurred(
                        start_time
                    ):
                        timeout_msg = f"Command timeout after {self.timeout} seconds"
                        LOGD(f"CommandTask: {timeout_msg}")
                        self.signals.task_error.emit(
                            self.handler.__class__.__name__, timeout_msg
                        )

                        if self.retry_policy.should_retry():
                            self.retry_policy.increment_retry()
                        else:
                            self.callback(self.handler, None)
                            break
                    else:
                        # 기타 이유로 대기 실패
                        break

            except Exception as e:
                error_msg = f"Execution attempt failed: {str(e)}"
                LOGE(f"CommandTask: {error_msg}")
                self.signals.task_error.emit(self.handler.__class__.__name__, error_msg)

                if self.retry_policy.should_retry():
                    self.retry_policy.increment_retry()
                else:
                    self.callback(self.handler, None)
                    break

    def _on_timeout(self, timeout_msg: str):
        """타임아웃 콜백 처리"""
        LOGD(f"CommandTask: {timeout_msg}")
        self.signals.task_error.emit(self.handler.__class__.__name__, timeout_msg)
        self.cancel()

    def _on_retry(self, retry_count: int, retry_msg: str):
        """재시도 콜백 처리"""
        LOGD(f"CommandTask: {retry_msg}")
        self.signals.task_progress.emit(
            self.handler.__class__.__name__,
            self.retry_policy.get_retry_progress(),
            retry_msg,
        )

    def _cleanup(self):
        """리소스 정리"""
        # 상태 완료
        self.state_manager.complete()

        # 타임아웃 모니터링 중지
        self.timeout_manager.stop_monitoring()

        # 태스크 완료 시그널 발산
        self._emit_task_completed(
            not self.state_manager.is_cancelled(), "Task finished"
        )

    def stop(self):
        """태스크 중지 (cancel과 동일)"""
        self.cancel()

    def cancel(self):
        """태스크 취소"""
        if self.state_manager.is_cancelled():
            return

        self.state_manager.cancel()
        cancel_msg = f"Task cancelled by user"
        LOGD(f"CommandTask: {cancel_msg} (ID: {self.task_id})")
        self.signals.task_error.emit(self.handler.__class__.__name__, cancel_msg)

    def is_running(self) -> bool:
        """태스크 실행 상태 확인"""
        return self.state_manager.is_running()

    def is_cancelled(self) -> bool:
        """태스크 취소 상태 확인"""
        return self.state_manager.is_cancelled()

    def is_completed(self) -> bool:
        """태스크 완료 상태 확인"""
        return self.state_manager.is_completed()

    def get_execution_time(self) -> float:
        """실행 시간 확인 (초)"""
        return self.state_manager.get_execution_time()

    def get_retry_count(self) -> int:
        """재시도 횟수 확인"""
        return self.retry_policy.get_current_retry_count()

    def _emit_task_completed(self, success: bool, message: str):
        """태스크 완료 시그널 발산"""
        execution_time = self.get_execution_time()
        retry_count = self.get_retry_count()
        detailed_message = (
            f"{message} (Execution time: {execution_time:.2f}s, Retries: {retry_count})"
        )
        self.signals.task_completed.emit(
            self.handler.__class__.__name__, success, detailed_message
        )
