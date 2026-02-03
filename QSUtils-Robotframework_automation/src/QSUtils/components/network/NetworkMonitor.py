"""
Network monitoring functionality with UI-independent architecture.
This module provides network status monitoring without direct UI dependencies.
"""

import threading
import time
from typing import Callable, Dict, Optional

from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_connection_manager import ConnectionManagerCommand
from QSUtils.components.network.NetworkEvents import (
    WiFiInfoUpdatedEvent,
    NetworkErrorEvent,
    event_bus,
    NetworkEventType,
)


class NetworkMonitor:
    """네트워크 상태 모니터링 클래스 - UI 독립적 설계"""

    def __init__(
        self,
        adb_device: ADBDevice,
        wifi_info_callback: Optional[Callable[[Dict[str, str]], None]] = None,
    ):
        self.adb_device = adb_device
        self.current_network_info = {}
        self.wifi_info_callback = wifi_info_callback
        self._monitoring = False
        self._monitor_thread = None
        self._update_interval = 1.0  # seconds
        self._stop_event = threading.Event()

        # 이벤트 버스에 WiFi 정보 업데이트 이벤트 구독
        event_bus.subscribe(NetworkEventType.WIFI_INFO_UPDATED, self)

    def start_monitoring(self):
        """네트워크 상태 모니터링 시작"""
        if not self._monitoring:
            self._monitoring = True
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self._monitor_thread.start()
            LOGD(f"NetworkMonitor: Started monitoring for {self.adb_device.serial}")

    def stop_monitoring(self):
        """네트워크 상태 모니터링 중지"""
        if self._monitoring:
            self._monitoring = False
            self._stop_event.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2.0)
            LOGD(f"NetworkMonitor: Stopped monitoring for {self.adb_device.serial}")

    def _monitor_loop(self):
        """모니터링 루프 (QTimer 대신 threading 사용)"""
        while self._monitoring and not self._stop_event.is_set():
            try:
                self.request_immediate_update()
                # _stop_event를 기다리면서 타임아웃으로 주기적인 업데이트 구현
                self._stop_event.wait(timeout=self._update_interval)
            except Exception as e:
                LOGD(f"NetworkMonitor: Error in monitor loop: {e}")
                time.sleep(1.0)  # 에러 발생 시 잠시 대기

    def request_immediate_update(self):
        """즉시 네트워크 상태 업데이트 요청"""
        try:
            network_info_command = ConnectionManagerCommand(
                self.adb_device, action="get-network-info"
            )
            network_info_command.execute_async(self.network_info_callback)
        except Exception as e:
            LOGD(f"NetworkMonitor: Failed to create command: {e}")
            # 오류 이벤트 발행
            error_event = NetworkErrorEvent(
                error_code="COMMAND_CREATE_FAILED",
                error_message=str(e),
                recoverable=True,
            )
            event_bus.publish(error_event)

    def network_info_callback(self, result):
        """네트워크 정보 콜백 처리"""
        LOGD(f"NetworkMonitor: Callback received for {self.adb_device.serial}")

        from QSUtils.command.command_constants import CommandResult

        actual_data = None

        if isinstance(result, CommandResult):
            if result.success:
                actual_data = result.data
        elif isinstance(result, dict):
            actual_data = result

        if isinstance(actual_data, dict):
            self.current_network_info = actual_data

            # WiFi 정보 업데이트 이벤트 생성 및 발행
            wifi_event = WiFiInfoUpdatedEvent(
                ssid=actual_data.get("SSID", "N/A"),
                ip_address=actual_data.get("Wi-Fi IP Address", "N/A"),
                router_address=actual_data.get("Router", "N/A"),
                rssi=actual_data.get("RSSI", "N/A"),
            )
            event_bus.publish(wifi_event)

            # 레거시 콜백 함수 호출 (하위 호환성)
            if self.wifi_info_callback:
                wifi_info = {
                    "SSID": wifi_event.ssid,
                    "IP": wifi_event.ip_address,
                    "Router": wifi_event.router_address,
                    "RSSI": wifi_event.rssi,
                }
                self.wifi_info_callback(wifi_info)
        else:
            # 실패 시 N/A 값으로 이벤트 발행
            wifi_event = WiFiInfoUpdatedEvent(
                ssid="N/A", ip_address="N/A", router_address="N/A", rssi="N/A"
            )
            event_bus.publish(wifi_event)

            # 레거시 콜백 함수 호출
            if self.wifi_info_callback:
                self.wifi_info_callback(
                    {"SSID": "N/A", "IP": "N/A", "Router": "N/A", "RSSI": "N/A"}
                )

    def get_current_network_info(self):
        """현재 네트워크 정보 반환"""
        return self.current_network_info.copy()

    def set_update_interval(self, interval: float):
        """업데이트 간격 설정 (초 단위)"""
        if interval > 0:
            self._update_interval = interval
            LOGD(
                f"NetworkMonitor: Update interval set to {interval}s for {self.adb_device.serial}"
            )

    def is_monitoring(self) -> bool:
        """모니터링 활성 상태 반환"""
        return self._monitoring

    # EventSubscriber 인터페이스 구현
    def handle_event(self, event):
        """이벤트 처리 (필요한 경우 확장을 위해 구현)"""
        pass

    def __del__(self):
        """소멸자 - 모니터링 정리"""
        self.stop_monitoring()
        # 이벤트 버스에서 구독 해제
        event_bus.unsubscribe(NetworkEventType.WIFI_INFO_UPDATED, self)
