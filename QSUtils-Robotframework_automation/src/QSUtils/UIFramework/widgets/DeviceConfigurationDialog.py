#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device Configuration Dialog
디바이스 설정을 위한 다이얼로그
"""

import subprocess
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QLabel,
    QFrame,
    QMessageBox,
    QProgressDialog,
    QApplication,
)

from QSUtils.DumpManager.DumpTypes import DumpMode, DumpTriggeredBy
from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.UIFramework.widgets.VersionInfoDialog import VersionInfoDialog
from QSUtils.UIFramework.widgets.WiFiConfigDialog import WiFiConfigDialog
from QSUtils.Utils import TimestampGenerator
from QSUtils.Utils.FileUtils import ensure_directory_exists
from QSUtils.Utils.Logger import LOGD, LOGI


class DeviceConfigurationDialog(QDialog):
    """
    디바이스 설정 다이얼로그
    """

    def __init__(self, parent, device_context):
        super().__init__(parent)
        self.device_context = device_context

        if device_context:
            self.device_serial = device_context.serial
            self.adb_device = device_context.adb_device
            self.event_manager = device_context.event_manager
            self.logging_manager = device_context.logging_manager
            self.dump_manager = device_context.dump_manager
        else:
            self.device_serial = None
            self.adb_device = None
            self.event_manager = None
            self.logging_manager = None
            self.dump_manager = None

        self.wifi_config_dialog = None
        self.version_dialog = None
        self.plot_progress_dialog = None

        self._setup_ui()
        self._setup_connections()

    def __del__(self):
        """소멸자 - 안전한 정리"""
        try:
            # WiFi Config Dialog 정리
            if hasattr(self, "wifi_config_dialog") and self.wifi_config_dialog:
                self.wifi_config_dialog.close()

            # Version Dialog 정리
            if hasattr(self, "version_dialog") and self.version_dialog:
                self.version_dialog.close()

            # Plot Progress Dialog 정리
            if hasattr(self, "plot_progress_dialog") and self.plot_progress_dialog:
                self.plot_progress_dialog.close()

        except Exception:
            pass  # 소멸자에서는 예외 무시

    def _setup_ui(self):
        """UI 설정"""
        # 디바이스 이름으로 Dialog Title 설정
        if (
            self.device_context
            and hasattr(self.device_context, "device_name")
            and self.device_context.device_name
        ):
            dialog_title = f"{self.device_context.device_name}"
        elif self.device_serial:
            dialog_title = f"{self.device_serial}"
        else:
            dialog_title = "Device Configuration"

        self.setWindowTitle(dialog_title)
        # self.setMinimumSize(400, 300)
        self.setModal(True)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 버튼 그룹 레이아웃
        buttons_group_layout = QVBoxLayout()

        # 버튼들을 가로로 배치할 레이아웃
        buttons_row_layout = QHBoxLayout()

        # Version 버튼
        self.version_button = QPushButton("Version")
        buttons_row_layout.addWidget(self.version_button)

        # Wi-Fi 버튼
        self.wifi_button = QPushButton("Wi-Fi")
        buttons_row_layout.addWidget(self.wifi_button)

        # Plot 버튼
        self.plot_button = QPushButton("Plot")
        buttons_row_layout.addWidget(self.plot_button)

        # Dump 버튼
        self.dump_button = QPushButton("Dump")
        buttons_row_layout.addWidget(self.dump_button)

        buttons_row_layout.addStretch()
        buttons_group_layout.addLayout(buttons_row_layout)

        # Power Sound 개별 토글(스위치) - 버튼 라인 아랫줄, 두 줄로 배치
        power_group_layout = QVBoxLayout()

        # 1행: Power ON 사운드 스위치
        row_on_layout = QHBoxLayout()
        self.power_on_label = QLabel("Power ON sound")
        self.power_on_switch = QCheckBox()
        self._apply_toggle_style(self.power_on_switch)
        # 라벨은 좌측, 토글은 맨 우측 배치
        row_on_layout.addWidget(self.power_on_label)
        row_on_layout.addStretch()
        row_on_layout.addWidget(self.power_on_switch)
        power_group_layout.addLayout(row_on_layout)

        # 2행: Power OFF 사운드 스위치
        row_off_layout = QHBoxLayout()
        self.power_off_label = QLabel("Power OFF sound")
        self.power_off_switch = QCheckBox()
        self._apply_toggle_style(self.power_off_switch)
        # 라벨은 좌측, 토글은 맨 우측 배치
        row_off_layout.addWidget(self.power_off_label)
        row_off_layout.addStretch()
        row_off_layout.addWidget(self.power_off_switch)
        power_group_layout.addLayout(row_off_layout)

        buttons_group_layout.addLayout(power_group_layout)

        # 구분선 추가
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        buttons_group_layout.addWidget(line)

        # 닫기 버튼 레이아웃
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch()

        # 닫기 버튼
        self.close_button = QPushButton("Close")
        close_button_layout.addWidget(self.close_button)

        buttons_group_layout.addLayout(close_button_layout)
        main_layout.addLayout(buttons_group_layout)

    def _setup_connections(self):
        """시그널 연결"""
        self.close_button.clicked.connect(self.accept)

        # 버튼 기능 직접 연결
        self.version_button.clicked.connect(self._on_version_clicked)
        self.wifi_button.clicked.connect(self._on_wifi_clicked)
        self.plot_button.clicked.connect(self._on_plot_clicked)
        self.dump_button.clicked.connect(self._on_dump_clicked)

        # Power Sound 각 스위치 핸들러 연결
        self.power_on_switch.toggled.connect(self._on_power_on_switch_toggled)
        self.power_off_switch.toggled.connect(self._on_power_off_switch_toggled)

        # 다이얼로그 생성 직후 스위치 초기 상태 동기화
        QTimer.singleShot(0, self._init_power_sound_switches_state)

    def _on_version_clicked(self):
        """Version 버튼 클릭 처리"""
        LOGD(
            f"DeviceConfigurationDialog: Version button clicked for {self.device_serial}"
        )

        if not self.adb_device:
            QMessageBox.warning(self, "Error", "ADB device is not available.")
            return

        try:
            # ADB를 통해 /sw_version.txt 파일 읽기
            def version_file_callback(result):
                """버전 파일 내용 콜백 처리"""
                if result and isinstance(result, str):
                    # VersionInfoDialog를 사용하여 다이얼로그 표시
                    QTimer.singleShot(
                        0, lambda: self._show_version_dialog_with_content(result)
                    )
                else:
                    LOGD("DeviceConfigurationDialog: Failed to read version file")
                    QTimer.singleShot(
                        0,
                        lambda: self._show_version_dialog_with_content(
                            "Failed to read version information"
                        ),
                    )

            # ADBDevice의 execute_adb_shell_async 메서드를 사용하여 파일 읽기
            self.adb_device.execute_adb_shell_async(
                "cat /sw_version.txt", version_file_callback
            )

        except Exception as e:
            LOGD(f"DeviceConfigurationDialog: Error reading version file: {e}")
            self._show_version_dialog_with_content("Error reading version information")

    def _show_version_dialog_with_content(self, content: str):
        """VersionInfoDialog를 사용하여 버전 정보 다이얼로그를 표시합니다."""
        try:
            VersionInfoDialog.show_version_dialog(self, content)
        except Exception as e:
            LOGD(f"DeviceConfigurationDialog: Error showing version dialog: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to show version dialog:\n{str(e)}"
            )

    def _on_wifi_clicked(self):
        """Wi-Fi 버튼 클릭 처리"""
        LOGD(
            f"DeviceConfigurationDialog: Wi-Fi button clicked for {self.device_serial}"
        )

        if not self.adb_device:
            QMessageBox.warning(self, "Error", "ADB device is not available.")
            return

        # UI 스레드가 아닐 경우, UI 스레드에서 재호출
        try:
            app = QApplication.instance()
            if app and QThread.currentThread() is not app.thread():
                QTimer.singleShot(0, self._on_wifi_clicked)
                return
        except Exception:
            pass

        if not self.wifi_config_dialog:
            self.wifi_config_dialog = WiFiConfigDialog(self, self.adb_device)

        if not self.wifi_config_dialog.isVisible():
            self.wifi_config_dialog.show()
            self.wifi_config_dialog.raise_()
            self.wifi_config_dialog.activateWindow()

    def _on_plot_clicked(self):
        """Plot 버튼 클릭 처리 - systemd plot chart 생성"""
        LOGD(f"DeviceConfigurationDialog: Plot button clicked for {self.device_serial}")

        if not self.adb_device:
            QMessageBox.warning(self, "Error", "ADB device is not available.")
            return

        if not self.logging_manager:
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
            LOGD(
                f"DeviceConfigurationDialog: Executing systemd plot command: {systemd_cmd}"
            )

            result = self.adb_device.execute_adb_shell(systemd_cmd)

            if result is None:
                LOGD(
                    f"DeviceConfigurationDialog: Failed to execute systemd plot command"
                )
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

            local_filename = f"systemd-plot-{self.device_serial}-{timestamp}.svg"
            local_file_path = plots_dir / local_filename

            LOGD(f"DeviceConfigurationDialog: Local file path: {local_file_path}")

            # 4. adb pull로 파일 추출 (80%)
            progress_dialog.setLabelText("Extracting plot chart to host...")
            progress_dialog.setValue(80)
            QApplication.processEvents()

            pull_cmd = [
                "adb",
                "-s",
                self.device_serial,
                "pull",
                remote_svg_path,
                str(local_file_path),
            ]

            LOGD(
                f"DeviceConfigurationDialog: Executing pull command: {' '.join(pull_cmd)}"
            )

            pull_result = subprocess.run(
                pull_cmd, capture_output=True, text=True, timeout=30
            )

            if pull_result.returncode != 0:
                LOGD(
                    f"DeviceConfigurationDialog: Failed to pull plot chart. Return code: {pull_result.returncode}"
                )
                LOGD(f"DeviceConfigurationDialog: Error output: {pull_result.stderr}")
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
                    f"DeviceConfigurationDialog: Warning: Failed to delete temporary file {remote_svg_path} from device"
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
            success_info += f"Device: {self.device_serial}\n"
            success_info += f"Generated at: {timestamp}\n"
            success_info += f"Saved to: {local_file_path}\n\n"
            success_info += (
                f"The chart shows the systemd boot timeline and service startup times."
            )

            QMessageBox.information(self, "Systemd Plot Chart Completed", success_info)

            LOGD(
                f"DeviceConfigurationDialog: Systemd plot chart successfully extracted to {local_file_path}"
            )

        except subprocess.TimeoutExpired:
            LOGD(f"DeviceConfigurationDialog: Timeout while extracting plot chart")
            QMessageBox.critical(self, "Error", "Plot chart extraction timed out.")
        except Exception as e:
            LOGD(
                f"DeviceConfigurationDialog: Exception while extracting plot chart: {e}"
            )
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during plot chart extraction:\n{str(e)}",
            )
        finally:
            progress_dialog.close()

    def _on_dump_clicked(self):
        """Dump 버튼 클릭 처리"""
        LOGD(f"DeviceConfigurationDialog: Dump button clicked for {self.device_serial}")

        if not self.dump_manager:
            QMessageBox.warning(self, "Error", "Dump manager is not available.")
            return

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
                "request_device_id": self.device_serial,
            },
        )

        LOGI(
            f"DeviceConfigurationDialog: Dump requested for device {self.device_serial}"
        )

    # ----------------------- Power Sound Switches -----------------------
    POWER_ON_PATH = "/usr/share/sounds/podium/audio-ui/Power_ON.wav"
    POWER_OFF_PATH = "/usr/share/sounds/podium/audio-ui/Power_OFF.wav"

    def _apply_toggle_style(self, checkbox: QCheckBox):
        """QCheckBox를 iOS 스타일 토글 스위치처럼 보이도록 간단한 스타일 적용."""
        try:
            checkbox.setTristate(False)
            checkbox.setStyleSheet("""
                QCheckBox::indicator { width: 44px; height: 24px; }
                QCheckBox::indicator:unchecked {
                    border-radius: 12px;
                    background-color: #c0c0c0;
                }
                QCheckBox::indicator:unchecked:pressed {
                    background-color: #b0b0b0;
                }
                QCheckBox::indicator:checked {
                    border-radius: 12px;
                    background-color: #4caf50;
                }
                /* thumb */
                QCheckBox::indicator:unchecked {
                    image: none;
                }
                QCheckBox::indicator:checked {
                    image: none;
                }
                /* Note: Drawing a real thumb needs custom painting.
                   Keep it simple with colored track for now. */
                """)
        except Exception:
            pass

    def _init_power_sound_switches_state(self):
        """디바이스의 파일 존재 상태를 읽어 두 스위치 초기 상태를 동기화."""
        try:
            on_enabled = self._is_sound_enabled(self.POWER_ON_PATH)
            off_enabled = self._is_sound_enabled(self.POWER_OFF_PATH)
        except Exception:
            on_enabled = True
            off_enabled = True

        self._set_switch_state(self.power_on_switch, on_enabled)
        self._set_switch_state(self.power_off_switch, off_enabled)

        # adb가 없으면 스위치 비활성화
        if not self.adb_device:
            self.power_on_switch.setEnabled(False)
            self.power_off_switch.setEnabled(False)

    def _set_switch_state(self, switch: QCheckBox, enabled: bool):
        switch.blockSignals(True)
        switch.setChecked(enabled)
        switch.blockSignals(False)

    def _adb_file_exists(self, path: str) -> bool:
        if not self.adb_device:
            return True
        cmd = f"if [ -f {path} ]; then echo YES; else echo NO; fi"
        out = self.adb_device.execute_adb_shell(cmd)
        if out is None:
            return True
        return "YES" in out

    def _is_sound_enabled(self, path: str) -> bool:
        return self._adb_file_exists(path)

    def _safe_mv(self, src: str, dst: str) -> bool:
        # 존재할 때만 mv 수행; 실패 시 None 반환
        cmd = f"if [ -f {src} ]; then mv {src} {dst}; else exit 0; fi"
        out = self.adb_device.execute_adb_shell(cmd) if self.adb_device else ""
        return out is not None

    def _on_power_on_switch_toggled(self, checked: bool):
        if not self.adb_device:
            QMessageBox.warning(self, "Error", "ADB device is not available.")
            self._set_switch_state(self.power_on_switch, True)
            return

        path = self.POWER_ON_PATH
        bak = f"{path}.bak"

        success = True
        if checked:
            # Enable -> .bak를 원래 이름으로 복구
            success = self._safe_mv(bak, path)
        else:
            # Disable -> 원본을 .bak으로 변경
            success = self._safe_mv(path, bak)

        # 실제 상태 재확인 후 UI 동기화
        enabled_now = self._is_sound_enabled(path)
        self._set_switch_state(self.power_on_switch, enabled_now)

        if not success:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to toggle Power_ON.wav on device.\nThe partition may be read-only or permission was denied.",
            )

    def _on_power_off_switch_toggled(self, checked: bool):
        if not self.adb_device:
            QMessageBox.warning(self, "Error", "ADB device is not available.")
            self._set_switch_state(self.power_off_switch, True)
            return

        path = self.POWER_OFF_PATH
        bak = f"{path}.bak"

        success = True
        if checked:
            success = self._safe_mv(bak, path)
        else:
            success = self._safe_mv(path, bak)

        enabled_now = self._is_sound_enabled(path)
        self._set_switch_state(self.power_off_switch, enabled_now)

        if not success:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to toggle Power_OFF.wav on device.\nThe partition may be read-only or permission was denied.",
            )
