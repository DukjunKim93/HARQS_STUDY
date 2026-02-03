#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device Command Executor - 명령 실행 및 비동기 처리 담당 클래스
"""

from typing import Callable, List, Optional

from PySide6.QtCore import QThreadPool, QTimer

from QSUtils.Utils.Logger import LOGD


class DeviceCommandExecutor:
    """명령 실행 및 비동기 처리 담당 클래스"""

    def __init__(
        self,
        adb_device,
        feature_registry,
        result_callback: Optional[Callable[[object, object], None]] = None,
    ):
        """
        생성자

        Args:
            adb_device: ADBDevice 인스턴스
            feature_registry: FeatureRegistry 인스턴스
            result_callback: 명령 결과를 전달받을 콜백 (handler, data)
        """
        self.adb_device = adb_device
        self.feature_registry = feature_registry
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        self.current_task = None
        self.current_command_index = 0
        self.is_device_connected = adb_device.is_connected
        self.current_handler = None
        self.result_callback = result_callback
        self.command_handlers = self._initialize_handlers()

        # 실행 주기 관리를 위한 QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.execute_command_set)
        self.timer.setInterval(500)  # 기본값 500ms

        # ADBDevice 시그널 연결
        self._connect_device_signals()

    def _initialize_handlers(self):
        """
        FeatureRegistry를 통해 handlers 초기화

        Returns:
            List[Any]: 초기화된 command handler 인스턴스 목록

        Raises:
            ValueError: Command handlers를 사용할 수 없는 경우
        """
        command_handler_classes = self.feature_registry.get_all_command_handlers()

        if not command_handler_classes:
            raise ValueError("No command handlers configured")

        # ADB device로 handler 인스턴스 생성
        command_handlers = []
        for handler_class in command_handler_classes:
            try:
                command_handlers.append(handler_class(self.adb_device))
                LOGD(f"DeviceCommandExecutor: Created handler {handler_class.__name__}")
            except Exception as e:
                LOGD(
                    f"DeviceCommandExecutor: Failed to create handler {handler_class.__name__}: {e}"
                )
                raise

        LOGD(
            f"DeviceCommandExecutor: Initialized {len(command_handlers)} command handlers"
        )
        return command_handlers

    def _connect_device_signals(self):
        """ADBDevice 시그널 연결"""
        try:
            self.adb_device.deviceConnected.connect(self._on_device_connected)
            self.adb_device.deviceDisconnected.connect(self._on_device_disconnected)
            LOGD("DeviceCommandExecutor: Connected device signals")
        except Exception as e:
            LOGD(f"DeviceCommandExecutor: Failed to connect device signals: {e}")

    def _on_device_connected(self):
        """디바이스 연결 시그널 핸들러"""
        LOGD("DeviceCommandExecutor: Device connected")
        self.is_device_connected = True

    def _on_device_disconnected(self):
        """디바이스 연결 해제 시그널 핸들러"""
        LOGD("DeviceCommandExecutor: Device disconnected")
        self.is_device_connected = False
        # 디바이스 연결 해제 시 진행 중인 명령 중지
        if self.current_handler:
            LOGD(
                "DeviceCommandExecutor: Stopping execution due to device disconnection"
            )
            self.stop_execution()

    def _disconnect_device_signals(self):
        """ADBDevice 시그널 연결 해제"""
        try:
            if hasattr(self.adb_device, "deviceConnected"):
                self.adb_device.deviceConnected.disconnect(self._on_device_connected)
            if hasattr(self.adb_device, "deviceDisconnected"):
                self.adb_device.deviceDisconnected.disconnect(
                    self._on_device_disconnected
                )
            LOGD("DeviceCommandExecutor: Disconnected device signals")
        except Exception as e:
            LOGD(f"DeviceCommandExecutor: Failed to disconnect device signals: {e}")

    def execute_command_set(self):
        """명령어 세트 실행 시작"""
        if not self.is_device_connected:
            LOGD(
                "DeviceCommandExecutor: Cannot start command set - device not connected"
            )
            return

        LOGD("DeviceCommandExecutor: Starting command set execution")
        self.current_command_index = 0
        self._execute_next_command_in_set()

    def _execute_next_command_in_set(self):
        """세트 내의 다음 명령어 실행"""
        if not self.is_device_connected:
            LOGD("DeviceCommandExecutor: Stopping command set - device disconnected")
            self.current_handler = None
            return

        if self.current_command_index < len(self.command_handlers):
            handler = self.command_handlers[self.current_command_index]
            self.execute_command(handler)
        else:
            LOGD("DeviceCommandExecutor: Command set completed")
            self.current_handler = None

    def execute_command(self, handler):
        """단일 명령 실행"""
        handler_name = handler.__class__.__name__
        LOGD(f"DeviceCommandExecutor: Executing {handler_name}")

        if hasattr(handler, "execute_async"):
            # 현재 handler 설정 전에 이미 다른 handler가 실행 중인지 확인
            if self.current_handler is not None:
                LOGD(
                    f"DeviceCommandExecutor: WARNING - Overwriting current_handler {self.current_handler.__class__.__name__} with {handler_name}"
                )

            self.current_handler = handler
            LOGD(f"DeviceCommandExecutor: Set current_handler to {handler_name}")
            handler.execute_async(self._on_command_finished_for_set)
        else:
            LOGD(f"DeviceCommandExecutor: No execute_async for {handler_name}")
            result = self.adb_device.execute_command(handler)
            self._on_command_finished_for_set(result)

    def _on_command_finished_for_set(self, command_result):
        """명령어 실행 완료 콜백"""
        # 현재 handler를 안전하게 저장하고 즉시 초기화하여 다음 command에 영향 주지 않도록 함
        handler = self.current_handler

        # 방어적 프로그래밍: handler가 없는 경우 경고 로그만 남기고 계속 진행
        if handler is None:
            LOGD(
                f"DeviceCommandExecutor: WARNING - Command finished but no handler is set! "
                f"This may indicate async callback timing issue. "
                f"Command result: {command_result}"
            )
            # 현재 실행 중인 명령 인덱스를 기록하여 디버깅에 도움
            LOGD(
                f"DeviceCommandExecutor: Current command index: {self.current_command_index}"
            )
            LOGD(f"DeviceCommandExecutor: Total handlers: {len(self.command_handlers)}")

            # 다음 명령 실행을 계속 진행 (안전한 복구)
            if self.is_device_connected:
                self.current_command_index += 1
                self._execute_next_command_in_set()
            return

        handler_name = handler.__class__.__name__
        handler_id = id(handler)  # handler의 고유 ID

        # 중요: 현재 handler를 즉시 초기화하여 다음 command 실행 영향 방지
        self.current_handler = None

        LOGD(
            f"DeviceCommandExecutor: Command finished for {handler_name} (ID: {handler_id})"
        )

        # CommandResult 객체 처리
        if command_result is not None and hasattr(command_result, "success"):
            if command_result.success:
                # 성공한 경우 데이터를 전달
                if self.result_callback is not None:
                    try:
                        # Handler ID 검증: 비동기 콜백 경쟁 감지 (엄격한 검증)
                        result_handler_id = getattr(command_result, "_handler_id", None)
                        if (
                            result_handler_id is not None
                            and result_handler_id != handler_id
                        ):
                            LOGD(
                                f"DeviceCommandExecutor: CRITICAL ERROR - Handler ID mismatch! "
                                f"Expected {handler_id} ({handler_name}), got {result_handler_id}"
                            )
                            LOGD(
                                f"DeviceCommandExecutor: Blocking result delivery to prevent data corruption"
                            )
                            # ID 불일치 시 결과 전달 차단 (데이터 무결성 보호)
                            return

                        LOGD(
                            f"DeviceCommandExecutor: Processing result for {handler_name} (ID: {handler_id})"
                        )

                        self.result_callback(handler, command_result.data)
                        LOGD(
                            f"DeviceCommandExecutor: Successfully delivered result for {handler_name} (ID: {handler_id})"
                        )
                    except Exception as e:
                        LOGD(
                            f"DeviceCommandExecutor: Error calling result_callback for {handler_name}: {e}"
                        )
            else:
                # 실패한 경우 에러 메시지 로깅
                LOGD(
                    f"DeviceCommandExecutor: Command failed for {handler_name}: {command_result.error}"
                )
        else:
            LOGD(f"DeviceCommandExecutor: Command failed for {handler_name}: No result")

        # 디바이스 연결 상태 확인 후 다음 명령 실행
        if self.is_device_connected:
            self.current_command_index += 1
            self._execute_next_command_in_set()
        else:
            LOGD("DeviceCommandExecutor: Stopping command set - device disconnected")

    def set_exec_interval(self, interval_ms: int):
        """
        실행 간격 설정

        Args:
            interval_ms (int): 실행 간격 (밀리초)
        """
        if interval_ms < 1:
            interval_ms = 1
        self.timer.setInterval(interval_ms)
        LOGD(f"DeviceCommandExecutor: Execution interval set to {interval_ms}ms")

    def start_execution(self):
        """명령 실행 시작"""
        if not self.timer.isActive():
            self.timer.start()
            LOGD("DeviceCommandExecutor: Execution started")

    def stop_execution(self):
        """명령 실행 중지"""
        LOGD("DeviceCommandExecutor: Stopping command execution")

        if self.current_task:
            self.current_task.stop()
            self.current_task = None

        if self.timer.isActive():
            self.timer.stop()
            LOGD("DeviceCommandExecutor: Timer stopped")

        self.thread_pool.clear()
        self.thread_pool.waitForDone(1000)
        self.current_handler = None

    def cleanup(self):
        """리소스 정리"""
        LOGD("DeviceCommandExecutor: Cleaning up resources")
        self.stop_execution()
        self._disconnect_device_signals()
