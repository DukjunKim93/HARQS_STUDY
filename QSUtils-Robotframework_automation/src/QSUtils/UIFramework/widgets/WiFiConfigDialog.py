"""
WiFi Configuration Dialog with event-based architecture.
This module provides UI components for WiFi configuration using the event system.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFormLayout,
    QGroupBox,
    QMessageBox,
)

from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.Utils.Logger import LOGD, LOGE
from QSUtils.components.network.NetworkEvents import (
    WiFiInfoUpdatedEvent,
    NetworkConnectionEvent,
    NetworkErrorEvent,
    event_bus,
    NetworkEventType,
    EventSubscriber,
)
from QSUtils.components.network.NetworkManager import NetworkManager


class WiFiConfigDialog(QDialog, EventSubscriber):
    """WiFi Configuration 다이얼로그 - 이벤트 기반 아키텍처"""

    def __init__(
        self,
        parent=None,
        adb_device: ADBDevice = None,
        network_manager: Optional[NetworkManager] = None,
    ):
        super().__init__(parent)
        self.adb_device = adb_device

        if not self.adb_device:
            LOGE(
                "WiFiConfigDialog: adb_device is None. Network functionality will be limited."
            )
            self.network_manager = None
        else:
            # NetworkManager를 외부에서 주입받거나 직접 생성
            self.network_manager = network_manager or NetworkManager(adb_device, self)

            # 이벤트 버스에 구독
            event_bus.subscribe(NetworkEventType.WIFI_INFO_UPDATED, self)
            event_bus.subscribe(NetworkEventType.CONNECTION_STATUS_CHANGED, self)
            event_bus.subscribe(NetworkEventType.NETWORK_ERROR, self)

            # 레거시 시그널 연결 (하위 호환성)
            self.network_manager.wifi_info_updated.connect(self.update_wifi_info)

        self.setWindowTitle("Wi-Fi Configuration")
        self.setModal(True)  # 모달 다이얼로그로 설정
        self._is_initial_selection_set = False  # 콤보박스 초기 자동 설정 플래그

        self._setup_ui()
        self._connect_signals()
        # 초기 상태는 첫 번째 update_wifi_info 호출을 통해 설정됩니다.

    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)

        # WiFi Configuration 그룹 박스
        wifi_group_box = QGroupBox("WiFi Configuration")
        wifi_layout = QVBoxLayout()
        wifi_group_box.setLayout(wifi_layout)

        # 상단: SSID 및 Connect 버튼
        ssid_connect_layout = QHBoxLayout()
        ssid_connect_layout.addWidget(QLabel("SSID:"))
        self.wifi_ssid_combo = QComboBox()
        if self.network_manager:
            self.wifi_ssid_combo.addItems(
                self.network_manager.get_available_wifi_networks()
            )
        ssid_connect_layout.addWidget(self.wifi_ssid_combo)

        self.wifi_connect_btn = QPushButton("Connect")
        ssid_connect_layout.addWidget(self.wifi_connect_btn)
        wifi_layout.addLayout(ssid_connect_layout)

        # 하단: 네트워크 상태 정보
        network_info_layout = QFormLayout()

        self.wifi_current_ssid_label = QLabel("N/A")
        self.wifi_ip_label = QLabel("N/A")
        self.wifi_router_label = QLabel("N/A")
        self.wifi_rssi_label = QLabel("N/A")

        network_info_layout.addRow("Network:", self.wifi_current_ssid_label)
        network_info_layout.addRow("IP:", self.wifi_ip_label)
        network_info_layout.addRow("Router:", self.wifi_router_label)
        network_info_layout.addRow("Signal:", self.wifi_rssi_label)

        wifi_layout.addLayout(network_info_layout)
        main_layout.addWidget(wifi_group_box)

    def _connect_signals(self):
        """시그널 연결"""
        if self.network_manager:
            # Connect 버튼 클릭 시 내부 메서드 호출
            self.wifi_connect_btn.clicked.connect(self._on_connect_clicked)

        # 사용자가 ComboBox를 수동으로 변경할 때 플래그 설정
        self.wifi_ssid_combo.currentTextChanged.connect(self._on_combo_manual_change)

    def _on_connect_clicked(self):
        """Connect 버튼 클릭 핸들러"""
        if not self.network_manager:
            QMessageBox.warning(
                self, "WiFi Configuration", "Network Manager is not available."
            )
            return

        selected_ssid = self.wifi_ssid_combo.currentText()
        if not selected_ssid:
            QMessageBox.warning(self, "WiFi Configuration", "Please select an SSID.")
            return

        password = self.network_manager.get_wifi_password(selected_ssid)
        if not password:
            QMessageBox.critical(
                self,
                "WiFi Configuration",
                f"Password not found for SSID: {selected_ssid}",
            )
            return

        LOGD(f"WiFiConfigDialog: Connect button clicked for SSID: {selected_ssid}")
        # 사용자가 연결을 시도했음을 표시
        self._user_initiated_connection = True
        self.network_manager.connect_to_wifi(selected_ssid, password)

    def showEvent(self, event):
        """다이얼로그가 표시될 때 호출됩니다."""
        super().showEvent(event)
        self._is_initial_selection_set = False  # 다이얼로그가 열릴 때마다 플래그 리셋
        LOGD(
            "WiFiConfigDialog: Dialog shown, resetting _is_initial_selection_set to False"
        )

        if self.network_manager:
            LOGD("WiFiConfigDialog: Dialog shown, starting network monitor.")
            self.network_manager.start_monitoring()
            self.network_manager.request_immediate_update()

    def hideEvent(self, event):
        """다이얼로그가 숨겨질 때 호출됩니다."""
        super().hideEvent(event)
        if self.network_manager:
            LOGD("WiFiConfigDialog: Dialog hidden, stopping network monitor.")
            self.network_manager.stop_monitoring()

    def update_wifi_info(self, current_ssid, ip_address, router_address, rssi):
        """WiFi 정보 업데이트 및 Connect 버튼 상태 관리 (레거시 메서드)"""
        self.wifi_current_ssid_label.setText(current_ssid)
        self.wifi_ip_label.setText(ip_address)
        self.wifi_router_label.setText(router_address)
        self.wifi_rssi_label.setText(rssi)

        # 현재 연결된 SSID를 기반으로 콤보박스와 Connect 버튼 상태 업데이트
        if current_ssid and current_ssid != "N/A":
            self.set_current_ssid(current_ssid)
            self.update_connect_button_state(current_ssid)
        else:
            # 연결된 SSID가 없으면 콤보박스 선택을 리셋하고 Connect 버튼을 활성화
            self.reset_ssid_selection()
            self.update_connect_button_state(None)

    def get_wifi_ssid_combo(self):
        """SSID 콤보박스 반환 (DeviceWidget에서의 연결을 위해 임시로 유지, 추후 제거 가능)"""
        return self.wifi_ssid_combo

    def get_wifi_connect_btn(self):
        """WiFi 연결 버튼 반환 (DeviceWidget에서의 연결을 위해 임시로 유지, 추후 제거 가능)"""
        return self.wifi_connect_btn

    def set_current_ssid(self, ssid: str):
        """
        콤보박스의 현재 선택된 항목을 지정된 SSID로 설정합니다.
        이 작업은 다이얼로그가 열리고 최초 한 번만 수행됩니다.
        SSID가 콤보박스 목록에 없으면 아무 작업도 하지 않습니다.
        """
        if self._is_initial_selection_set:
            # 이미 초기 설정이 완료되었으면 사용자 변경을 방해하지 않음
            LOGD(
                f"WiFiConfigDialog: Initial selection already made. Ignoring auto-set to '{ssid}'."
            )
            return

        index = self.wifi_ssid_combo.findText(ssid)
        if index >= 0:
            self.wifi_ssid_combo.setCurrentIndex(index)
            self._is_initial_selection_set = True  # 초기 설정 완료 표시
            LOGD(f"WiFiConfigDialog: SSID combo initially set to '{ssid}'.")
        else:
            LOGD(f"WiFiConfigDialog: SSID '{ssid}' not found in combo list.")

    def reset_ssid_selection(self):
        """SSID 콤보박스 선택을 첫 번째 항목으로 리셋합니다."""
        if self._is_initial_selection_set:
            # 이미 초기 설정이 완료되었으면 사용자 변경을 방해하지 않음
            LOGD(
                f"WiFiConfigDialog: Initial selection already made. Ignoring reset to first item."
            )
            return

        if self.wifi_ssid_combo.count() > 0:
            self.wifi_ssid_combo.setCurrentIndex(0)
            LOGD(f"WiFiConfigDialog: SSID combo selection reset to first item.")
        else:
            LOGD(f"WiFiConfigDialog: SSID combo is empty, cannot reset selection.")

    def _on_combo_manual_change(self, text: str):
        """
        사용자가 ComboBox를 수동으로 변경할 때 호출됩니다.
        사용자가 선택한 후에는 자동 업데이트가 선택을 덮어쓰지 않도록 플래그를 설정합니다.
        """
        if text:  # 빈 문자열이 아닐 때만 처리
            self._is_initial_selection_set = True
            LOGD(
                f"WiFiConfigDialog: User manually changed SSID combo to '{text}', setting _is_initial_selection_set to True"
            )

    def update_connect_button_state(self, current_connected_ssid: Optional[str]):
        """
        현재 연결된 SSID와 콤보박스의 선택된 SSID를 비교하여
        Connect 버튼의 활성화 상태를 업데이트합니다.
        """
        selected_ssid = self.wifi_ssid_combo.currentText()

        # current_connected_ssid가 None이거나 "N/A"이면 연결된 상태가 아님
        is_connected_to_a_network = (
            current_connected_ssid and current_connected_ssid != "N/A"
        )

        if is_connected_to_a_network and selected_ssid == current_connected_ssid:
            self.wifi_connect_btn.setEnabled(False)
            LOGD(
                f"WiFiConfigDialog: Connect button disabled. Already connected to '{selected_ssid}'."
            )
        else:
            self.wifi_connect_btn.setEnabled(True)
            LOGD(
                f"WiFiConfigDialog: Connect button enabled. Selected '{selected_ssid}', connected to '{current_connected_ssid}'."
            )

    # EventSubscriber 인터페이스 구현
    def handle_event(self, event):
        """이벤트 처리"""
        if isinstance(event, WiFiInfoUpdatedEvent):
            # WiFi 정보 업데이트 이벤트 처리
            self._handle_wifi_info_updated(event)
        elif isinstance(event, NetworkConnectionEvent):
            # 네트워크 연결 상태 변경 이벤트 처리
            self._handle_connection_status_changed(event)
        elif isinstance(event, NetworkErrorEvent):
            # 네트워크 오류 이벤트 처리
            self._handle_network_error(event)

    def _handle_wifi_info_updated(self, event: WiFiInfoUpdatedEvent):
        """WiFi 정보 업데이트 이벤트 처리"""
        LOGD(f"WiFiConfigDialog: WiFi info updated via event - SSID: {event.ssid}")

        # UI 업데이트 (메인 스레드에서 안전하게 실행)
        def update_ui():
            self.wifi_current_ssid_label.setText(event.ssid)
            self.wifi_ip_label.setText(event.ip_address)
            self.wifi_router_label.setText(event.router_address)
            self.wifi_rssi_label.setText(event.rssi)

            # 현재 연결된 SSID를 기반으로 콤보박스와 Connect 버튼 상태 업데이트
            if event.ssid and event.ssid != "N/A":
                self.set_current_ssid(event.ssid)
                self.update_connect_button_state(event.ssid)
            else:
                # 연결된 SSID가 없으면 콤보박스 선택을 리셋하고 Connect 버튼을 활성화
                self.reset_ssid_selection()
                self.update_connect_button_state(None)

        # PySide6에서는 메인 스레드에서 UI 업데이트를 보장하기 위해 signal/slot 사용
        # 또는 QMetaObject.invokeMethod를 사용할 수 있음
        # 여기서는 간단하게 직접 호출 (이미 메인 스레드에서 실행될 것임)
        update_ui()

    def _handle_connection_status_changed(self, event: NetworkConnectionEvent):
        """네트워크 연결 상태 변경 이벤트 처리"""
        if event.connected:
            LOGD(f"WiFiConfigDialog: Connected to network - SSID: {event.ssid}")
            # 연결 성공 시 사용자 연결 시도 플래그 리셋
            if hasattr(self, "_user_initiated_connection"):
                self._user_initiated_connection = False
            # 연결 성공 메시지 표시 (선택적)
            # QMessageBox.information(self, "WiFi Connection", f"Successfully connected to {event.ssid}")
        else:
            LOGD(
                f"WiFiConfigDialog: Disconnected from network - Error: {event.error_message}"
            )
            # 연결 실패 메시지는 실제로 연결이 실패했을 때만 표시
            # WiFi 전환 과정에서 일시적으로 연결이 해제되는 경우는 메시지를 표시하지 않음
            if (
                event.error_message
                and "Failed to connect to WiFi" in event.error_message
            ):
                # 사용자가 수동으로 연결을 시도한 경우에만 에러 메시지 표시
                if (
                    hasattr(self, "_user_initiated_connection")
                    and self._user_initiated_connection
                ):
                    # 연결 실패 후 일정 시간 대기하여 실제 실패인지 확인
                    # 타이머를 사용하여 잠시 후에 에러 메시지 표시
                    from PySide6.QtCore import QTimer

                    self._pending_error_message = event.error_message
                    QTimer.singleShot(2000, self._show_connection_error_if_still_failed)
                # 연결 해제 시에는 플래그를 즉시 리셋하지 않음 (연결 성공 시 리셋)

    def _show_connection_error_if_still_failed(self):
        """2초 후에도 여전히 연결 실패 상태이면 에러 메시지 표시"""
        # 사용자가 연결을 시도했고, 아직 연결되지 않은 경우에만 에러 메시지 표시
        if (
            hasattr(self, "_user_initiated_connection")
            and self._user_initiated_connection
        ):
            if hasattr(self, "_pending_error_message") and self._pending_error_message:
                # 현재 연결 상태 확인 - 여전히 연결되지 않았는지 확인
                current_ssid = self.wifi_current_ssid_label.text()
                if current_ssid == "N/A" or not current_ssid:
                    QMessageBox.warning(
                        self,
                        "WiFi Connection",
                        f"Connection failed: {self._pending_error_message}",
                    )

        # 상태 정리
        self._pending_error_message = None
        self._user_initiated_connection = False

    def _handle_network_error(self, event: NetworkErrorEvent):
        """네트워크 오류 이벤트 처리"""
        LOGD(
            f"WiFiConfigDialog: Network error - Code: {event.error_code}, Message: {event.error_message}"
        )

        if not event.recoverable:
            # 복구 불가능한 오류의 경우 사용자에게 알림
            QMessageBox.critical(
                self,
                "Network Error",
                f"A critical network error occurred:\n\n{event.error_message}\n\nError Code: {event.error_code}",
            )
        else:
            # 복구 가능한 오류의 경우 로그만 기록 (사용자에게는 연결 상태 변경 이벤트로 알려짐)
            pass

    def __del__(self):
        """소멸자 - 이벤트 구독 해제"""
        if self.network_manager:
            # 이벤트 버스에서 구독 해제
            event_bus.unsubscribe(NetworkEventType.WIFI_INFO_UPDATED, self)
            event_bus.unsubscribe(NetworkEventType.CONNECTION_STATUS_CHANGED, self)
            event_bus.unsubscribe(NetworkEventType.NETWORK_ERROR, self)

            # 모니터링 중지
            self.network_manager.stop_monitoring()

        LOGD("WiFiConfigDialog: Cleaned up event subscriptions")
