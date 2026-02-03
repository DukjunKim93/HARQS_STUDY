"""
Network management functionality with event-based architecture.
This module provides WiFi and network management without direct UI dependencies.
"""

from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal

from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.Utils.Logger import LOGD
from QSUtils.command.cmd_connection_manager import ConnectionManagerCommand
from QSUtils.components.network.NetworkEvents import (
    WiFiInfoUpdatedEvent,
    NetworkConnectionEvent,
    NetworkErrorEvent,
    event_bus,
    NetworkEventType,
)
from QSUtils.components.network.NetworkMonitor import NetworkMonitor
from QSUtils.components.network.WiFiConfig import WiFiConfig


class NetworkManager(QObject):
    """WiFi 및 네트워크 관리 클래스 - 이벤트 기반 아키텍처"""

    # 레거시 시그널 (하위 호환성 유지)
    wifi_info_updated = Signal(
        str, str, str, str
    )  # current_ssid, ip_address, router_address, rssi

    def __init__(self, adb_device: ADBDevice, parent_widget=None):
        super().__init__(parent_widget)  # QObject needs a parent for Qt integration
        self.adb_device = adb_device
        self.parent_widget = (
            parent_widget  # Optional parent widget for legacy compatibility
        )
        self.wifi_config = WiFiConfig()

        # UI 독립적인 NetworkMonitor 생성
        self.network_monitor = NetworkMonitor(adb_device, self._on_wifi_info_updated)

        # 이벤트 버스에 구독
        event_bus.subscribe(NetworkEventType.WIFI_INFO_UPDATED, self)
        event_bus.subscribe(NetworkEventType.CONNECTION_STATUS_CHANGED, self)
        event_bus.subscribe(NetworkEventType.NETWORK_ERROR, self)

        LOGD(f"NetworkManager: Initialized for {adb_device.serial}")

    def connect_to_wifi(self, ssid: str, password: str):
        """WiFi 연결"""
        LOGD(f"NetworkManager: Connecting to {ssid} for {self.adb_device.serial}")
        try:
            wifi_command = ConnectionManagerCommand(
                self.adb_device, action="setup", ssid=ssid, password=password
            )
            wifi_command.execute_async(self.wifi_connect_callback)
        except Exception as e:
            LOGD(f"NetworkManager: Failed to create WiFi connect command: {e}")
            # 오류 이벤트 발행
            error_event = NetworkErrorEvent(
                error_code="WIFI_CONNECT_COMMAND_FAILED",
                error_message=str(e),
                recoverable=True,
            )
            event_bus.publish(error_event)

    def wifi_connect_callback(self, result):
        """WiFi 연결 콜백"""
        LOGD(f"NetworkManager: WiFi connect callback for {self.adb_device.serial}")

        if result is True:
            LOGD(
                f"NetworkManager: Successfully connected to WiFi for {self.adb_device.serial}"
            )
            # 연결 성공 이벤트 발행
            connection_event = NetworkConnectionEvent(
                connected=True,
                ssid="Connected",  # 실제 SSID는 다음 네트워크 정보 업데이트에서 확인
            )
            event_bus.publish(connection_event)
        else:
            error_message = "Failed to connect to WiFi."
            if isinstance(result, str) and result:
                error_message = result

            LOGD(
                f"NetworkManager: WiFi connection failed for {self.adb_device.serial}: {error_message}"
            )

            # 연결 실패 이벤트 발행
            connection_event = NetworkConnectionEvent(
                connected=False, error_message=error_message
            )
            event_bus.publish(connection_event)

            # 오류 이벤트 발행
            error_event = NetworkErrorEvent(
                error_code="WIFI_CONNECT_FAILED",
                error_message=error_message,
                recoverable=True,
            )
            event_bus.publish(error_event)

    def _on_wifi_info_updated(self, wifi_info: Dict[str, str]):
        """
        WiFi 정보 업데이트 콜백 (NetworkMonitor에서 호출)
        레거시 시그널 발행 및 UI 업데이트
        """
        ssid = wifi_info.get("SSID", "N/A")
        ip_address = wifi_info.get("IP", "N/A")
        router_address = wifi_info.get("Router", "N/A")
        rssi = wifi_info.get("RSSI", "N/A")

        LOGD(f"NetworkManager: WiFi info updated - SSID: {ssid}, IP: {ip_address}")

        # 레거시 시그널 발행 (기존 UI와의 호환성)
        self.wifi_info_updated.emit(ssid, ip_address, router_address, rssi)

        # 부모 위젯이 있는 경우 레거시 UI 업데이트 메서드 호출
        if self.parent_widget and hasattr(self.parent_widget, "update_wifi_status_ui"):
            try:
                self.parent_widget.update_wifi_status_ui(
                    {
                        "SSID": ssid,
                        "Wi-Fi IP Address": ip_address,
                        "Router": router_address,
                        "RSSI": rssi,
                    }
                )
            except Exception as e:
                LOGD(f"NetworkManager: Error calling parent update_wifi_status_ui: {e}")

    def start_monitoring(self):
        """네트워크 모니터링 시작"""
        self.network_monitor.start_monitoring()
        LOGD(f"NetworkManager: Started network monitoring for {self.adb_device.serial}")

    def stop_monitoring(self):
        """네트워크 모니터링 중지"""
        self.network_monitor.stop_monitoring()
        LOGD(f"NetworkManager: Stopped network monitoring for {self.adb_device.serial}")

    def request_immediate_update(self):
        """즉시 네트워크 상태 업데이트 요청"""
        self.network_monitor.request_immediate_update()
        LOGD(f"NetworkManager: Requested immediate update for {self.adb_device.serial}")

    def get_current_network_info(self) -> Dict[str, Any]:
        """현재 네트워크 정보 반환"""
        return self.network_monitor.get_current_network_info()

    def get_available_wifi_networks(self) -> list:
        """사용 가능한 WiFi 네트워크 목록 반환"""
        return list(self.wifi_config.ssid_passwords.keys())

    def get_wifi_password(self, ssid: str) -> Optional[str]:
        """SSID에 해당하는 WiFi 비밀번호 반환"""
        return self.wifi_config.ssid_passwords.get(ssid)

    def set_update_interval(self, interval: float):
        """네트워크 상태 업데이트 간격 설정 (초 단위)"""
        self.network_monitor.set_update_interval(interval)
        LOGD(
            f"NetworkManager: Update interval set to {interval}s for {self.adb_device.serial}"
        )

    def is_monitoring(self) -> bool:
        """모니터링 활성 상태 반환"""
        return self.network_monitor.is_monitoring()

    def add_wifi_config(self, ssid: str, password: str):
        """WiFi 설정 추가"""
        self.wifi_config.ssid_passwords[ssid] = password
        LOGD(f"NetworkManager: Added WiFi config for SSID: {ssid}")

    def remove_wifi_config(self, ssid: str):
        """WiFi 설정 제거"""
        if ssid in self.wifi_config.ssid_passwords:
            del self.wifi_config.ssid_passwords[ssid]
            LOGD(f"NetworkManager: Removed WiFi config for SSID: {ssid}")

    # EventSubscriber 인터페이스 구현
    def handle_event(self, event):
        """이벤트 처리"""
        if isinstance(event, WiFiInfoUpdatedEvent):
            # WiFi 정보 업데이트 이벤트는 NetworkMonitor에서 직접 처리되므로
            # 여기서는 추가적인 로직이 필요한 경우에만 구현
            pass
        elif isinstance(event, NetworkConnectionEvent):
            # 연결 상태 변경 이벤트 처리
            LOGD(
                f"NetworkManager: Connection status changed - Connected: {event.connected}"
            )
            if event.connected:
                LOGD(f"NetworkManager: Connected to SSID: {event.ssid}")
            else:
                LOGD(f"NetworkManager: Disconnected. Error: {event.error_message}")
        elif isinstance(event, NetworkErrorEvent):
            # 네트워크 오류 이벤트 처리
            LOGD(
                f"NetworkManager: Network error - Code: {event.error_code}, Message: {event.error_message}"
            )
            if not event.recoverable:
                LOGD(f"NetworkManager: Unrecoverable error occurred")

    def initial_wifi_status_sync(self, network_info: Dict[str, Any]):
        """
        초기 WiFi 상태 동기화.
        DeviceWidget이 초기화될 때 호출되며, 현재 연결된 WiFi 정보를 바탕으로
        WiFiConfigDialog의 콤보박스와 Connect 버튼 상태를 설정합니다.
        """
        LOGD(f"NetworkManager: Initial WiFi status sync for {self.adb_device.serial}")

        if not isinstance(network_info, dict):
            LOGD(
                f"NetworkManager: Invalid network_info format for initial sync: {network_info}"
            )
            return

        current_ssid = network_info.get("SSID")
        wifi_status = network_info.get("Wi-Fi")

        # 부모 위젯이 있고 레거시 메서드를 가진 경우 호출
        if (
            self.parent_widget
            and hasattr(self.parent_widget, "wifi_config_dialog")
            and self.parent_widget.wifi_config_dialog is not None
        ):

            try:
                if current_ssid and wifi_status == "Connected":
                    LOGD(
                        f"NetworkManager: Setting initial SSID to '{current_ssid}' for dialog."
                    )
                    self.parent_widget.wifi_config_dialog.set_current_ssid(current_ssid)
                else:
                    LOGD(
                        f"NetworkManager: No active SSID or not connected. Resetting dialog SSID selection."
                    )
                    self.parent_widget.wifi_config_dialog.reset_ssid_selection()

                # Connect 버튼 상태 업데이트
                self.parent_widget.wifi_config_dialog.update_connect_button_state(
                    current_ssid
                )
            except Exception as e:
                LOGD(f"NetworkManager: Error in initial WiFi status sync: {e}")
        else:
            LOGD(
                f"NetworkManager: WiFiConfigDialog not yet created during initial sync."
            )

    def reset_wifi_status_ui(self):
        """
        WiFi 상태 UI 리셋.
        레거시 메서드로, 현재는 이벤트 기반 아키텍처로 대체되었으나
        하위 호환성을 위해 유지합니다.
        """
        # 이벤트 기반 아키텍처에서는 UI 리셋이 필요한 경우
        # 해당 이벤트를 발행하여 구독자들이 처리하도록 함
        reset_event = WiFiInfoUpdatedEvent(
            ssid="N/A", ip_address="N/A", router_address="N/A", rssi="N/A"
        )
        event_bus.publish(reset_event)
        LOGD(
            f"NetworkManager: WiFi status UI reset event published for {self.adb_device.serial}"
        )

    def __del__(self):
        """소멸자 - 이벤트 구독 해제 및 정리"""
        # 이벤트 버스에서 구독 해제
        event_bus.unsubscribe(NetworkEventType.WIFI_INFO_UPDATED, self)
        event_bus.unsubscribe(NetworkEventType.CONNECTION_STATUS_CHANGED, self)
        event_bus.unsubscribe(NetworkEventType.NETWORK_ERROR, self)

        # 모니터링 중지
        self.stop_monitoring()

        LOGD(f"NetworkManager: Cleaned up for {self.adb_device.serial}")
