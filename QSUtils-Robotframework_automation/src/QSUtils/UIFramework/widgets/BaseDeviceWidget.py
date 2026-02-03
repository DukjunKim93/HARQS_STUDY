#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base device widget that provides common UI structure and functionality for all device monitoring apps.
"""

import subprocess
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QThread
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
    QProgressDialog,
    QApplication,
    QLineEdit,
)

from QSUtils.ADBDevice.DeviceLoggingManager import DeviceLoggingManager
from QSUtils.DumpManager import DumpProcessManager
from QSUtils.DumpManager.DumpTypes import DumpTriggeredBy, DumpMode
from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.widgets.DeviceConfigurationDialog import (
    DeviceConfigurationDialog,
)
from QSUtils.UIFramework.widgets.WiFiConfigDialog import WiFiConfigDialog
from QSUtils.Utils import TimestampGenerator
from QSUtils.Utils.FileUtils import ensure_directory_exists
from QSUtils.Utils.Logger import LOGD, LOGE, LOGI
from QSUtils.command.cmd_get_device_info import GetDeviceInfoCommand
from QSUtils.command.cmd_reboot import RebootCommand
from QSUtils.command.cmd_save_device_name import SaveDevNameCommand
from QSUtils.command.cmd_update_device_name import UpdateDeviceNameCommand


class ConnectionState:
    """연결 상태 상수"""

    DISCONNECTED = 0
    CONNECTED = 1


class SessionState:
    """세션 상태 상수"""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class BaseDeviceWidget(QWidget):
    """
    Base widget for device monitoring applications.
    Provides common UI structure (device info, ADB status, control buttons) and functionality.
    """

    def __init__(self, parent, device_context: DeviceContext, min_width: int = None):
        super().__init__(parent)
        self.device_context = device_context
        self.event_manager = device_context.event_manager
        self.adb_device = device_context.adb_device
        self.serial = device_context.serial
        self.settings_manager = device_context.settings_manager

        # 최소 너비 설정 (앱별로 지정 가능)
        if min_width is not None:
            self.setMinimumWidth(min_width)

        self.device_name = None

        # === 모든 앱에 필요한 상태 관리 속성 추가 ===
        self.is_running = False  # 현재 실행 상태
        self.is_manual_start = False  # 수동 시작 여부

        # === 사용자 명시적 제어 상태 관리 ===
        self.session_state = SessionState.STOPPED

        # 공통 컴포넌트 초기화
        self.title_frame = None
        self.device_name_text = None
        self.adb_status_label = None
        self.reboot_btn = None
        self.wifi_btn = None
        self.plot_btn = None
        self.dump_btn = None

        # 공통 기능 객체
        self.reboot_command = RebootCommand(self.adb_device)
        self.wifi_config_dialog = None

        # logging_manager 초기화
        self.logging_manager = DeviceLoggingManager(self.adb_device, self)
        self.device_context.logging_manager = self.logging_manager
        # 가능한 한 UI 스레드로 이동하여 하위 QObject 생성 시 스레드 불일치 방지
        try:
            if self.logging_manager.thread() is not self.thread():
                self.logging_manager.moveToThread(self.thread())
        except Exception as e:
            LOGD(f"BaseDeviceWidget: moveToThread failed or not applicable: {e}")

        # DumpProcessManager 초기화
        self.dump_manager = DumpProcessManager(
            self, self.adb_device, self.event_manager, self.logging_manager
        )
        self.device_context.dump_manager = self.dump_manager
        LOGD("BaseDeviceWidget: DumpProcessManager initialized successfully")

        # 기본 UI 설정
        self._setup_basic_ui()

        # 앱별 특화 UI (자식 클래스에서 구현)
        self._setup_app_specific_ui()

        # ADBDevice 시그널을 Event로 변환하는 핸들러 연결
        self.adb_device.deviceConnected.connect(self._on_adb_device_connected)
        self.adb_device.deviceDisconnected.connect(self._on_adb_device_disconnected)

        # logging_manager 공통 시그널 연결
        self._setup_logging_manager_signals()

        # Event 핸들러 설정
        self._setup_event_handlers()

        self._handle_device_connection_state()

        LOGD(f"BaseDeviceWidget: Initialization completed for {self.serial}")

    def _setup_log_file_widget(self):
        """Log File 표시를 위한 Label과 QLineEdit 생성"""
        self.log_file_frame = QFrame()
        self.log_file_frame.setFrameShape(QFrame.StyledPanel)
        log_file_layout = QHBoxLayout()
        self.log_file_frame.setLayout(log_file_layout)

        # Log File Label
        log_file_label = QLabel("Log File:")
        log_file_layout.addWidget(log_file_label)

        # Log File Path Display
        self.log_file_label = QLineEdit()
        self.log_file_label.setReadOnly(True)
        self.log_file_label.setPlaceholderText("No log file")
        log_file_layout.addWidget(self.log_file_label, 1)  # stretch factor = 1

        return self.log_file_frame

    def _setup_basic_ui(self):
        """모든 앱에 공통으로 적용될 기본 UI 설정"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)

        # 1. 타이틀 프레임 - 디바이스 정보 + ADB 상태 + Reboot 버튼
        self._setup_title_frame()
        main_layout.addWidget(self.title_frame, 0)

        # 2. 로그 파일 프레임 - Log File 표시
        self.log_file_frame = self._setup_log_file_widget()
        main_layout.addWidget(self.log_file_frame, 0)

        # 3. 앱별 커스텀 영역 (자식 클래스에서 구현)
        self.app_specific_frame = QFrame()
        self.app_specific_frame.setContentsMargins(
            0, 0, 0, 0
        )  # 앱별 위젯 영역의 margin 제거
        self.app_specific_layout = QVBoxLayout()
        self.app_specific_layout.setContentsMargins(
            0, 0, 0, 0
        )  # 앱별 레이아웃의 margin 제거
        self.app_specific_frame.setLayout(self.app_specific_layout)
        main_layout.addWidget(self.app_specific_frame, 1)

    def _setup_title_frame(self):
        """타이틀 프레임 설정 - 디바이스 이름, 실제 디바이스 이름과 ADB 상태 표시"""

        title_label_min_width = 120
        self.title_frame = QFrame()
        self.title_frame.setFrameShape(QFrame.StyledPanel)
        title_layout = QVBoxLayout()
        self.title_frame.setLayout(title_layout)

        # 첫 번째 줄: Device 이름과 Reboot 버튼
        first_row_layout = QHBoxLayout()

        # Device 이름
        device_name_label = QLabel("Device:")
        device_name_label.setMinimumWidth(title_label_min_width)  # 라벨 최소 너비 설정
        self.device_name_text = QPushButton(self.serial)
        self.device_name_text.clicked.connect(self._on_device_name_clicked)
        first_row_layout.addWidget(device_name_label)
        first_row_layout.addWidget(self.device_name_text)
        first_row_layout.addStretch()

        # Reboot 버튼 (맨 우측으로 이동)
        self.reboot_btn = QPushButton("Reboot")
        self.reboot_btn.clicked.connect(self.on_reboot_clicked)
        first_row_layout.addWidget(self.reboot_btn)

        title_layout.addLayout(first_row_layout)

        # 두 번째 줄: 실제 Device 이름과 ADB 연결 상태
        second_row_layout = QHBoxLayout()

        # Name 라벨
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(
            title_label_min_width
        )  # Device 라벨과 동일한 최소 너비 설정
        second_row_layout.addWidget(name_label)

        # 실제 Device 이름을 위한 LineEdit
        self.device_name_edit = QLineEdit()
        self.device_name_edit.setPlaceholderText("Device name will be displayed here")
        second_row_layout.addWidget(self.device_name_edit, 1)  # stretch factor = 1

        # ADB 연결 상태 라벨 (맨 우측으로 이동)
        self.adb_status_label = QLabel()
        self.adb_status_label.setMinimumWidth(title_label_min_width)
        self.adb_status_label.setAlignment(Qt.AlignCenter)
        second_row_layout.addWidget(self.adb_status_label)

        # editingFinished 시그널 연결
        self.device_name_edit.editingFinished.connect(self._on_device_name_changed)

        title_layout.addLayout(second_row_layout)

        # 세 번째 줄: Firmware 및 Q-Symphony 버전 정보 (하나의 라벨로 표시)
        third_row_layout = QHBoxLayout()
        third_row_layout.setAlignment(Qt.AlignLeft)

        # 버전 정보 라벨
        version_label = QLabel("Version:")
        version_label.setMinimumWidth(title_label_min_width)
        self.version_info_label = QLabel("N/A")
        third_row_layout.addWidget(version_label)
        third_row_layout.addWidget(self.version_info_label)

        third_row_layout.addStretch()

        title_layout.addLayout(third_row_layout)

    def _setup_app_specific_ui(self):
        """
        앱별 특화 UI 설정 메서드.
        자식 클래스에서 반드시 오버라이드해야 함.
        """
        pass

    def set_app_content_layout(self, layout):
        """
        앱별 콘텐츠가 추가될 기본 레이아웃을 재지정합니다.
        - 이후 self.app_specific_layout에 addWidget/addLayout 등으로 추가되는 모든 위젯은
          이 레이아웃(예: General 탭의 레이아웃)에 추가되도록 동작합니다.
        """
        try:
            if layout is None:
                return
            # 타입 체크 없이 레이아웃 참조만 교체 (호환성 유지)
            self.app_specific_layout = layout
            LOGD(
                f"BaseDeviceWidget: app_specific_layout is rebound to provided layout for {self.serial}"
            )
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Failed to rebind app_specific_layout: {e}")

    def get_app_content_layout(self):
        """현재 앱별 콘텐츠 레이아웃을 반환합니다."""
        return getattr(self, "app_specific_layout", None)

    def _setup_logging_manager_signals(self):
        """logging_manager 공통 시그널 연결 설정 - 단순화된 버전"""
        if self.logging_manager:
            # UI 업데이트를 위한 시그널 직접 연결
            self.logging_manager.log_file_display_updated_signal.connect(
                self._update_log_file_display
            )
            self.logging_manager.logging_error_signal.connect(self._on_logging_error)

    # -----------------------------
    # 공통 이벤트 핸들러
    # -----------------------------
    def on_reboot_clicked(self):
        """Reboot 버튼 클릭 처리"""
        LOGD(f"BaseDeviceWidget: Reboot button clicked for device {self.serial}")
        if hasattr(self, "reboot_command") and self.reboot_command:

            def reboot_callback(result):
                if result:
                    LOGD(
                        f"BaseDeviceWidget: Reboot command sent successfully to {self.serial}"
                    )

                    # EventManager가 있는 경우에만 REBOOT_COMPLETED 이벤트 발생
                    if self.event_manager:
                        self._safe_emit_reboot_completed(result)
                else:
                    LOGD(
                        f"BaseDeviceWidget: Failed to send reboot command to {self.serial}"
                    )

            self.reboot_command.execute_async(reboot_callback)

    def on_wifi_btn_clicked(self):
        """Wi-Fi 버튼 클릭 처리 - 모든 앱에 공통으로 적용"""
        # UI 스레드가 아닐 경우, UI 스레드에서 재호출
        try:
            app = QApplication.instance()
            if app and QThread.currentThread() is not app.thread():
                QTimer.singleShot(0, self.on_wifi_btn_clicked)
                return
        except Exception:
            pass

        if not self.wifi_config_dialog:
            self.wifi_config_dialog = WiFiConfigDialog(self, self.adb_device)

        if not self.wifi_config_dialog.isVisible():
            self.wifi_config_dialog.show()
            self.wifi_config_dialog.raise_()
            self.wifi_config_dialog.activateWindow()

    def on_plot_chart_clicked(self):
        """Plot 버튼 클릭 처리 - systemd plot chart 생성 (모든 앱에 공통)"""
        LOGD(f"BaseDeviceWidget: Plot button clicked for device {self.serial}")

        if not hasattr(self, "logging_manager") or not self.logging_manager:
            QMessageBox.warning(self, "Error", "Logging manager is not available.")
            return

        if not self.logging_manager.log_directory:
            QMessageBox.warning(self, "Error", "Log directory is not set.")
            return

        # 진행 상황 다이얼로그 생성
        progress_dialog = QProgressDialog(
            "Generating systemd plot chart...", "Cancel", 0, 100, self
        )
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setWindowTitle("Systemd Plot Chart Generation")
        progress_dialog.setMinimumWidth(400)
        progress_dialog.show()

        QApplication.processEvents()

        try:
            # 1. 타임스탬프 생성 (10%)
            progress_dialog.setLabelText("Preparing timestamp...")
            progress_dialog.setValue(10)
            QApplication.processEvents()
            time.sleep(0.1)

            timestamp = TimestampGenerator.get_log_timestamp()
            remote_svg_path = "/tmp/systemd-plot.svg"

            # 2. systemd-analyze plot 명령 실행 (20-60%)
            progress_dialog.setLabelText("Generating systemd plot chart on device...")
            progress_dialog.setValue(20)
            QApplication.processEvents()

            systemd_cmd = (
                f"LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/lib/systemd /data/usr/bin/systemd-analyze plot > "
                f"{remote_svg_path}"
            )
            LOGD(f"BaseDeviceWidget: Executing systemd plot command: {systemd_cmd}")

            result = self.adb_device.execute_adb_shell(systemd_cmd)

            if result is None:
                LOGD(f"BaseDeviceWidget: Failed to execute systemd plot command")
                QMessageBox.critical(
                    self, "Error", "Failed to generate systemd plot chart on device."
                )
                return

            progress_dialog.setValue(60)
            QApplication.processEvents()

            # 3. 로컬 파일 경로 생성 (70%)
            progress_dialog.setLabelText("Preparing local file path...")
            progress_dialog.setValue(70)
            QApplication.processEvents()
            time.sleep(0.1)

            plots_dir = Path(self.logging_manager.log_directory) / "plots"
            ensure_directory_exists(plots_dir)

            local_filename = f"systemd-plot-{self.serial}-{timestamp}.svg"
            local_file_path = plots_dir / local_filename

            LOGD(f"BaseDeviceWidget: Local file path: {local_file_path}")

            # 4. adb pull로 파일 추출 (80%)
            progress_dialog.setLabelText("Extracting plot chart to host...")
            progress_dialog.setValue(80)
            QApplication.processEvents()

            pull_cmd = [
                "adb",
                "-s",
                self.serial,
                "pull",
                remote_svg_path,
                str(local_file_path),
            ]

            LOGD(f"BaseDeviceWidget: Executing pull command: {' '.join(pull_cmd)}")

            pull_result = subprocess.run(
                pull_cmd, capture_output=True, text=True, timeout=30
            )

            if pull_result.returncode != 0:
                LOGD(
                    f"BaseDeviceWidget: Failed to pull plot chart. Return code: {pull_result.returncode}"
                )
                LOGD(f"BaseDeviceWidget: Error output: {pull_result.stderr}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to extract plot chart:\n{pull_result.stderr}",
                )
                return

            # 5. 원본 파일 삭제 (90%)
            progress_dialog.setLabelText("Cleaning up temporary file on device...")
            progress_dialog.setValue(90)
            QApplication.processEvents()
            time.sleep(0.1)

            delete_cmd = f"rm {remote_svg_path}"
            delete_result = self.adb_device.execute_adb_shell(delete_cmd)

            if delete_result is None:
                LOGD(
                    f"BaseDeviceWidget: Warning: Failed to delete temporary file {remote_svg_path} from device"
                )

            # 100% 완료
            progress_dialog.setValue(100)
            progress_dialog.setLabelText("Systemd plot chart extraction completed!")
            QApplication.processEvents()
            time.sleep(0.5)

            # 완료 메시지
            success_info = (
                f"Systemd plot chart has been successfully generated and extracted:\n\n"
            )
            success_info += f"Device: {self.serial}\n"
            success_info += f"Generated at: {timestamp}\n"
            success_info += f"Saved to: {local_file_path}\n\n"
            success_info += (
                f"The chart shows the systemd boot timeline and service startup times."
            )

            QMessageBox.information(self, "Systemd Plot Chart Completed", success_info)

            LOGD(
                f"BaseDeviceWidget: Systemd plot chart successfully extracted to {local_file_path}"
            )

        except subprocess.TimeoutExpired:
            LOGD(f"BaseDeviceWidget: Timeout while extracting plot chart")
            QMessageBox.critical(self, "Error", "Plot chart extraction timed out.")
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Exception while extracting plot chart: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during plot chart extraction:\n{str(e)}",
            )
        finally:
            progress_dialog.close()

    def on_dump_clicked(self):
        """Dump 버튼 클릭 처리"""
        LOGD(f"BaseDeviceWidget: Dump button clicked for device {self.serial}")

        # 기존 Mode 저장
        self.dump_manager.previous_dump_mode = self.dump_manager.dump_mode

        # Mode를 DIALOG로 변경
        self.dump_manager.dump_mode = DumpMode.DIALOG

        # Global 버스에 UNIFIED_DUMP_REQUESTED 이벤트 발생 (triggered_by = MANUAL)
        from QSUtils.UIFramework.base.GlobalEventManager import get_global_event_bus

        get_global_event_bus().emit_event(
            CommonEventType.UNIFIED_DUMP_REQUESTED,
            {
                "triggered_by": DumpTriggeredBy.MANUAL.value,
                "request_device_id": self.serial,
            },
        )

        LOGI(f"BaseDeviceWidget: Dump requested for device {self.serial}")

    def _handle_device_connection_state(self):
        self._check_connection_status()
        is_connected = self.adb_device.is_connected

        if is_connected:
            self._handle_device_connection()
            self.on_device_connected()
        else:
            self._handle_device_disconnection()
            self.on_device_disconnected()

        # DEVICE_CONNECTION_CHANGED 이벤트 발행
        self.event_manager.emit_event(
            CommonEventType.DEVICE_CONNECTION_CHANGED,
            {
                "connected": is_connected,
                "device_serial": self.serial,
                "connection_type": "usb",  # 기본값, 필요시 확장
            },
        )

        # UI 상태를 디바이스 연결 상태와 일치시킴
        if self.isEnabled() != is_connected:
            self.setEnabled(is_connected)
            action = "enabled" if is_connected else "disabled"
            LOGD(
                f"BaseDeviceWidget: UI {action} due to device {action.replace('ed', 'ion')}"
            )

    # -----------------------------
    # ADBDevice 시그널을 Event로 변환
    # -----------------------------
    def _on_adb_device_connected(self):
        """ADBDevice 시그널을 DEVICE_CONNECTED Event로 변환"""
        LOGD(f"BaseDeviceWidget: ADBDevice connected, emitting DEVICE_CONNECTED event")

        self._handle_device_connection_state()

    def _on_adb_device_disconnected(self):
        """ADBDevice 시그널을 DEVICE_DISCONNECTED Event로 변환"""
        LOGD(
            f"BaseDeviceWidget: ADBDevice disconnected, emitting DEVICE_DISCONNECTED event"
        )

        # WiFi Config Dialog가 열려있으면 닫기
        if hasattr(self, "wifi_config_dialog") and self.wifi_config_dialog:
            if self.wifi_config_dialog.isVisible():
                self.wifi_config_dialog.close()

        self._handle_device_connection_state()

    def on_device_connected(self):
        """디바이스 연결 Event 처리 (하위 클래스에서 오버라이드용)"""
        LOGD(f"BaseDeviceWidget: Device {self.serial} connected event received.")
        # 기본 구현은 비어있음, 하위 클래스에서 필요시 오버라이드

    def on_device_disconnected(self):
        """디바이스 연결 해제 Event 처리 (하위 클래스에서 오버라이드용)"""
        LOGD(f"BaseDeviceWidget: Device {self.serial} disconnected event received.")
        # 기본 구현은 비어있음, 하위 클래스에서 필요시 오버라이드

    def _check_connection_status(self):
        # ADB 상태 라벨 업데이트
        self._set_adb_status_style(bool(self.adb_device.is_connected))

        # UI 컨트롤 활성화 상태 일괄 업데이트
        self._update_ui_controls_state(bool(self.adb_device.is_connected))

    def _update_ui_controls_state(self, enabled: bool):
        """모든 UI 컨트롤의 활성화 상태를 일괄 업데이트"""
        # UI 컨트롤 목록
        ui_controls = [
            ("wifi_btn", self.wifi_btn),
            ("plot_btn", self.plot_btn),
            ("dump_btn", self.dump_btn),
            ("reboot_btn", self.reboot_btn),
            ("device_name_edit", self.device_name_edit),
        ]

        for control_name, control in ui_controls:
            if hasattr(self, control_name) and control:
                control.setEnabled(enabled)

        LOGD(f"BaseDeviceWidget: UI controls {'enabled' if enabled else 'disabled'}")

    def _handle_device_connection(self):
        """디바이스 연결 처리 (초기 연결 및 재연결)"""
        if self.session_state == SessionState.PAUSED:
            # 재연결 시 세션 상태 복원
            LOGD("BaseDeviceWidget: Auto-resuming paused session after reconnect")
            self.session_state = SessionState.RUNNING

        # 디바이스 이름 가져오기 (초기 연결과 재연결 모두에서 실행)
        self._get_device_name()

        # Firmware 및 Q-Symphony 버전 정보 가져오기
        self._get_version_info()

    def _handle_device_disconnection(self):
        """디바이스 연결 해제 시 상태 저장 및 정리"""
        LOGD(
            f"BaseDeviceWidget: Device disconnected. Current session_state: {self.session_state}"
        )

        previous_state = self.session_state
        # 사용자 명시적 시작 상태만 pause로 변경
        if self.session_state == SessionState.RUNNING:
            self.session_state = SessionState.PAUSED
            LOGD(
                f"BaseDeviceWidget: Session state changed from running to paused due to disconnection"
            )

            # SESSION_STATE_CHANGED 이벤트 발행
            self.event_manager.emit_event(
                CommonEventType.SESSION_STATE_CHANGED,
                {
                    "state": self.session_state,
                    "manual": False,
                    "previous_state": previous_state,
                },
            )

    def _set_adb_status_style(self, connected: bool):
        """ADB 연결 상태에 따른 스타일 설정 (QSLogger 스타일)"""
        try:
            if not hasattr(self, "adb_status_label") or self.adb_status_label is None:
                return
            if connected:
                self.adb_status_label.setText("Connected")
                self.adb_status_label.setStyleSheet(
                    "color: white; background-color: #4CAF50; padding:2px 6px; border-radius:4px;"
                )
            else:
                self.adb_status_label.setText("Disconnected")
                self.adb_status_label.setStyleSheet(
                    "color: white; background-color: #cc0000; padding:2px 6px; border-radius:4px;"
                )
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error setting ADB status style: {e}")

    def _on_logging_error(self, error_msg: str):
        """DeviceLoggingManager의 logging_error_signal을 처리하는 UI 업데이트 핸들러"""
        LOGD(f"BaseDeviceWidget: Logging error: {error_msg}")
        # 자식 클래스 UI 훅으로도 전달
        try:
            if hasattr(self, "_on_logging_error_ui_update"):
                self._on_logging_error_ui_update(error_msg)
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error forwarding logging error update: {e}")
        QMessageBox.warning(
            self, "로깅 에러", f"로깅 중 에러가 발생했습니다:\n{error_msg}"
        )

    # -----------------------------
    # 공통 세션 제어 및 Start/Stop 핸들러
    # -----------------------------
    def on_start_stop_clicked(self, manual: bool = True):
        """
        공통 Start/Stop 버튼 핸들러.
        - 시작: 사용자 명시적 시작만 허용
        - 정지: 사용자 명시적 정지
        """
        try:
            if self.session_state == SessionState.STOPPED:
                LOGD(
                    f"BaseDeviceWidget: User explicit start requested. manual={manual}"
                )
                self._start_user_session(manual=manual)
            elif self.session_state in [SessionState.RUNNING, SessionState.PAUSED]:
                LOGD("BaseDeviceWidget: User explicit stop requested.")
                self._stop_user_session()
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error in on_start_stop_clicked: {e}")

    def start_session(self, manual: bool = True):
        """
        공통 세션 시작(로깅 포함).
        - manual=True면 항상 새 파일로 시작하도록 상태 초기화 및 파일명 준비
        - DeviceLoggingManager 정책에 따라 로깅 시작
        - 앱별 추가 작업은 _on_session_started 훅에서 처리
        """
        # 실행/수동 상태 설정
        self.is_running = True
        self.is_manual_start = bool(manual)

        # 수동 시작 시: 파일 상태 초기화 + 새 파일명 사전 준비
        try:
            if manual:
                if self.logging_manager:
                    if hasattr(self.logging_manager, "reset_log_file_state"):
                        self.logging_manager.reset_log_file_state()
                    if hasattr(
                        self.logging_manager, "prepare_new_log_filename_for_session"
                    ):
                        self.logging_manager.prepare_new_log_filename_for_session()
        except Exception:
            pass

        # 로깅 시작
        try:
            if hasattr(self, "logging_manager") and self.logging_manager:
                self.logging_manager.start_logging(manual_start=self.is_manual_start)
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Failed to start logging in start_session: {e}")

        # 앱별 훅
        try:
            if hasattr(self, "_on_session_started"):
                self._on_session_started(self.is_manual_start)
        except Exception as e:
            LOGD(f"BaseDeviceWidget: _on_session_started hook error: {e}")

    def stop_session(self):
        """
        공통 세션 정지(로깅 포함).
        - DeviceLoggingManager를 통해 로깅 정지
        - 앱별 추가 정리는 _on_session_stopped 훅에서 처리
        """
        # 로깅 정지
        try:
            if hasattr(self, "logging_manager") and self.logging_manager:
                if self.logging_manager.is_currently_logging():
                    self.logging_manager.stop_logging()
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Failed to stop logging in stop_session: {e}")

        # 상태 정리
        self.is_running = False
        self.is_manual_start = False

        # 앱별 훅
        try:
            if hasattr(self, "_on_session_stopped"):
                self._on_session_stopped()
        except Exception as e:
            LOGD(f"BaseDeviceWidget: _on_session_stopped hook error: {e}")

    def _on_session_started(self, manual: bool):
        """
        앱별 세션 시작 훅.
        - 각 앱에서 필요시 오버라이드
        """
        pass

    def _on_session_stopped(self):
        """
        앱별 세션 정지 훅.
        - 각 앱에서 필요시 오버라이드
        """
        pass

    def _start_user_session(self, manual: bool = True):
        """
        사용자 명시적 세션 시작
        - session_state를 체크하여 이미 실행중이면 무시
        - session_state를 running으로 설정하고 start_session 호출
        """
        if self.session_state == SessionState.RUNNING:
            LOGD("BaseDeviceWidget: Session already running, ignoring start request")
            return

        if self.session_state == SessionState.PAUSED:
            LOGD(
                "BaseDeviceWidget: Session is paused, resuming instead of starting new session"
            )
        else:
            LOGD(f"BaseDeviceWidget: User session started. manual={manual}")

        previous_state = self.session_state
        self.session_state = SessionState.RUNNING
        self.start_session(
            manual=(False if previous_state == SessionState.PAUSED else manual)
        )

        # SESSION_STATE_CHANGED 이벤트 발행
        self.event_manager.emit_event(
            CommonEventType.SESSION_STATE_CHANGED,
            {
                "state": self.session_state,
                "manual": manual,
                "previous_state": previous_state,
            },
        )

    def _stop_user_session(self):
        """
        사용자 명시적 세션 정지
        - session_state를 체크하여 이미 정지되어 있으면 무시
        - session_state를 stopped로 설정
        - user_explicitly_started 초기화
        - stop_session 호출
        """
        # Session state 체크
        if self.session_state == SessionState.STOPPED:
            LOGD("BaseDeviceWidget: Session already stopped, ignoring stop request")
            return

        previous_state = self.session_state
        self.session_state = SessionState.STOPPED
        LOGD(
            f"BaseDeviceWidget: User session stopped. session_state={self.session_state}"
        )
        self.stop_session()

        # SESSION_STATE_CHANGED 이벤트 발행
        self.event_manager.emit_event(
            CommonEventType.SESSION_STATE_CHANGED,
            {
                "state": self.session_state,
                "manual": True,
                "previous_state": previous_state,
            },
        )

    def _update_log_file_display(self):
        """
        로그 파일 표시 UI 업데이트
        DeviceLoggingManager의 get_log_file_display_name()을 사용하여 UI에 로그 파일 이름 표시
        """
        try:
            if hasattr(self, "log_file_label") and self.log_file_label:
                if self.logging_manager:
                    display_text = self.logging_manager.get_log_file_display_name()
                    if display_text:
                        self.log_file_label.setText(display_text)
                    else:
                        self.log_file_label.clear()
                        self.log_file_label.setPlaceholderText("No log file")
                else:
                    self.log_file_label.clear()
                    self.log_file_label.setPlaceholderText("No log file")
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error updating log file display: {e}")

    # -----------------------------
    # Event 핸들러 메서드
    # -----------------------------
    def _setup_event_handlers(self):
        """BaseDeviceWidget 전용 이벤트 핸들러 설정"""
        try:
            self.event_manager.register_event_handler(
                CommonEventType.REBOOT_REQUESTED, self._on_reboot_requested
            )
            self.event_manager.register_event_handler(
                CommonEventType.DUMP_COMPLETED, self._on_dump_completed
            )
            # Device 연결 관련 이벤트 핸들러 등록
            self.event_manager.register_event_handler(
                CommonEventType.DEVICE_CONNECTED, self.on_device_connected
            )
            self.event_manager.register_event_handler(
                CommonEventType.DEVICE_DISCONNECTED, self.on_device_disconnected
            )
            LOGI("BaseDeviceWidget: Registered event handlers")
        except Exception as e:
            LOGE(f"BaseDeviceWidget: Error setting up event handlers: {e}")

    def _on_reboot_requested(self, args):
        """REBOOT_REQUESTED 이벤트 직접 처리"""
        sync_before_reboot = args.get("sync_before_reboot", True)

        LOGI(
            f"BaseDeviceWidget: Received reboot_requested event - sync: {sync_before_reboot}"
        )

        if not self.adb_device.is_connected:
            LOGE(f"BaseDeviceWidget: reboot requested but device disconnected")
            return

        # sync_before_reboot 옵션 설정
        if hasattr(self, "reboot_command") and self.reboot_command:
            self.reboot_command.sync_before_reboot = sync_before_reboot

        # 기존 재부팅 루틴 호출
        self.on_reboot_clicked()

    def _on_dump_completed(self, args):
        """DUMP_COMPLETED 이벤트 핸들러 - Mode 복구"""
        try:
            triggered_by = args.get("triggered_by")
            success = args.get("success", False)

            LOGD(
                f"BaseDeviceWidget: Dump completed - triggered_by: {triggered_by}, success: {success}"
            )

            # MANUAL 트리거인 경우에만 Mode 복구
            if triggered_by == DumpTriggeredBy.MANUAL.value and success:
                if hasattr(self.dump_manager, "previous_dump_mode"):
                    self.dump_manager.dump_mode = self.dump_manager.previous_dump_mode
                    LOGD(
                        f"BaseDeviceWidget: Restored previous dump mode after MANUAL dump completion"
                    )
                else:
                    # 이전 Mode가 없는 경우 DIALOG로 설정 (기본값)
                    self.dump_manager.dump_mode = DumpMode.DIALOG
                    LOGD(
                        f"BaseDeviceWidget: Set dump mode to DIALOG (default) after MANUAL dump completion"
                    )

        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error handling dump completed event: {e}")

    def _safe_emit_reboot_completed(self, result):
        """안전하게 REBOOT_COMPLETED 이벤트 발생"""
        try:
            self.event_manager.emit_event(
                CommonEventType.REBOOT_COMPLETED, {"result": result}
            )
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error emitting reboot completed event: {e}")

    def _get_device_name(self):
        """디바이스 이름을 비동기적으로 가져옵니다."""
        try:
            # GetDeviceInfoCommand 생성 및 실행
            get_device_info_command = GetDeviceInfoCommand(self.adb_device)

            def device_info_callback(device_info):
                """디바이스 정보 콜백 처리"""
                if device_info and isinstance(device_info, dict):
                    self.device_name = device_info.get("DeviceName")
                    if self.device_name:
                        LOGD(f"BaseDeviceWidget: Got device name: {self.device_name}")
                        # UI 스레드에서 안전하게 업데이트
                        QTimer.singleShot(
                            0,
                            lambda: self._update_device_name_display(self.device_name),
                        )
                    else:
                        LOGD("BaseDeviceWidget: DeviceName not found in device info")
                        QTimer.singleShot(
                            0, lambda: self._update_device_name_display("Unknown")
                        )
                else:
                    LOGD("BaseDeviceWidget: Failed to get device info")
                    QTimer.singleShot(
                        0, lambda: self._update_device_name_display("Error")
                    )

            # 비동기 명령어 실행
            get_device_info_command.execute_async(device_info_callback)

        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error getting device name: {e}")
            self._update_device_name_display("Error")

    def _get_version_info(self):
        """Firmware 및 Q-Symphony 버전 정보를 비동기적으로 가져옵니다."""
        try:
            # ADBDevice의 read_sw_version_file 메서드를 비동기적으로 호출
            def version_info_callback(result):
                """버전 정보 콜백 처리"""
                if result and isinstance(result, str):
                    # 버전 정보 파싱
                    firmware_version = "N/A"
                    qs_version = "N/A"

                    # 각 줄을 파싱하여 firmware와 q-symphony 정보 추출
                    for line in result.split("\n"):
                        if line.startswith("firmware :"):
                            firmware_version = line.split(":", 1)[1].strip()
                        elif line.startswith("q-symphony :"):
                            qs_version = line.split(":", 1)[1].strip()

                    LOGD(
                        f"BaseDeviceWidget: Got version info - Firmware: {firmware_version}, Q-Symphony: {qs_version}"
                    )
                    # UI 스레드에서 안전하게 업데이트
                    QTimer.singleShot(
                        0,
                        lambda: self._update_version_info_display(
                            firmware_version, qs_version
                        ),
                    )
                else:
                    LOGD("BaseDeviceWidget: Failed to get version info")
                    QTimer.singleShot(
                        0, lambda: self._update_version_info_display("N/A", "N/A")
                    )

            # ADBDevice의 read_sw_version_file 메서드를 비동기적으로 호출
            self.adb_device.execute_adb_shell_async(
                "cat /sw_version.txt", version_info_callback
            )

        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error getting version info: {e}")
            self._update_version_info_display("N/A", "N/A")

    def _update_version_info_display(self, firmware_version: str, qs_version: str):
        """버전 정보 표시를 업데이트합니다."""
        try:
            # 하나의 문자열로 버전 정보 조합 (Q-Symphony 버전 형식 수정)
            version_info = f"{firmware_version} (QS: {qs_version})"

            if hasattr(self, "version_info_label") and self.version_info_label:
                self.version_info_label.setText(version_info)
                LOGD(f"BaseDeviceWidget: Updated version info display: {version_info}")
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error updating version info display: {e}")

    def _update_device_name_display(self, device_name: str):
        """디바이스 이름 표시를 업데이트합니다."""
        try:
            if hasattr(self, "device_name_edit") and self.device_name_edit:
                self.device_name_edit.setText(device_name)
                LOGD(f"BaseDeviceWidget: Updated device name display: {device_name}")
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error updating device name display: {e}")

    def _on_device_name_changed(self):
        """
        디바이스 이름 편집이 완료되었을 때 호출되는 핸들러
        Enter 키 입력이나 포커스 아웃 시 발생
        """
        # 현재 텍스트 가져오기
        current_text = self.device_name_edit.text().strip()

        # 이전 이름과 동일하면 무시
        if hasattr(self, "device_name") and self.device_name == current_text:
            return

        # 빈 텍스트는 저장하지 않음
        if not current_text:
            LOGD(
                f"BaseDeviceWidget: Empty device name, skipping save for device {self.serial}"
            )
            return

        # SaveDevNameCommand 생성 및 실행
        try:
            save_command = SaveDevNameCommand(self.adb_device, current_text)

            def save_callback(success):
                """디바이스 이름 저장 콜백 처리"""
                if success:
                    LOGD(
                        f"BaseDeviceWidget: Device name saved successfully: '{current_text}' for device {self.serial}"
                    )

                    # 저장 성공 시 UpdateDeviceNameCommand 실행 (publish)
                    try:
                        update_command = UpdateDeviceNameCommand(
                            self.adb_device, current_text
                        )

                        def update_callback(update_success):
                            """디바이스 이름 publish 콜백 처리"""
                            if update_success:
                                LOGD(
                                    f"BaseDeviceWidget: Device name saved and published successfully: '{current_text}' "
                                    f"for device {self.serial}"
                                )
                            else:
                                LOGD(
                                    f"BaseDeviceWidget: Device name saved but publish failed: '{current_text}' for "
                                    f"device {self.serial}"
                                )

                            # publish 성공/실패와 관계없이 저장은 성공했으므로 UI 업데이트
                            self._get_device_name()

                        # 비동기 명령어 실행
                        update_command.execute_async(update_callback)

                    except Exception as e:
                        LOGD(
                            f"BaseDeviceWidget: Error executing UpdateDeviceNameCommand: {e}"
                        )
                        # publish 실패해도 저장은 성공했으므로 UI 업데이트
                        self._get_device_name()

                else:
                    LOGD(
                        f"BaseDeviceWidget: Failed to save device name: '{current_text}' for device {self.serial}"
                    )
                    # 실패 시 원래 이름으로 복원
                    if hasattr(self, "device_name") and self.device_name:
                        QTimer.singleShot(
                            0,
                            lambda: self._update_device_name_display(self.device_name),
                        )

            # 비동기 명령어 실행
            save_command.execute_async(save_callback)

        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error saving device name: {e}")
            # 에러 시 원래 이름으로 복원
            if hasattr(self, "device_name") and self.device_name:
                QTimer.singleShot(
                    0, lambda: self._update_device_name_display(self.device_name)
                )

    def _on_device_name_clicked(self):
        """디바이스 이름 버튼 클릭 핸들러"""
        LOGD(f"BaseDeviceWidget: Device name button clicked for {self.serial}")

        try:
            # DeviceConfigurationDialog 생성 및 표시 (device_context만 전달)
            dialog = DeviceConfigurationDialog(
                parent=self, device_context=self.device_context
            )
            dialog.exec()
        except Exception as e:
            LOGD(f"BaseDeviceWidget: Error showing device configuration dialog: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to show device configuration dialog:\n{str(e)}"
            )
