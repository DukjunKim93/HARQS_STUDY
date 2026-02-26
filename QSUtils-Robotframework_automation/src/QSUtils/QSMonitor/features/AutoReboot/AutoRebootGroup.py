# -*- coding: utf-8 -*-
"""
Auto Reboot 그룹을 포함하는 클래스
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QProgressBar,
    QSizePolicy,
)

from QSUtils.DumpManager import DumpMode, DumpState, DumpTriggeredBy
from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.QSMonitor.core.GlobalEvents import GlobalEventType
from QSUtils.UIFramework.base import DeviceContext
from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.UIFramework.base.GlobalEventManager import get_global_event_bus
from QSUtils.UIFramework.widgets.BaseEventWidget import BaseEventWidget, UIElementGroup
from QSUtils.Utils import LOGD, LOGE, LOGI, LOGW
from QSUtils.Utils.DateTimeUtils import TimestampGenerator

GROUP_MINIMUM_WIDTH = 300


class AutoRebootGroup(BaseEventWidget):
    """Auto Reboot 그룹을 포함하는 클래스"""

    def __init__(self, parent, device_context: DeviceContext):
        self.device_context = device_context
        if device_context is None:
            raise ValueError("device_context cannot be None")

        super().__init__(parent, self.device_context.event_manager, "AutoRebootGroup")

        self.dump_manager = self.device_context.dump_manager

        self.auto_reboot_started = False
        self.qs_failed_count_label = None
        self.crash_count_label = None
        self.success_count_label = None
        self.reboot_count_label = None

        # Auto Reboot 관련 속성 초기화
        self.auto_reboot_running = False
        self.auto_reboot_timer = QTimer(self)
        self.auto_reboot_timer.setInterval(1000)  # 1초 간격
        self.auto_reboot_timer.timeout.connect(self._on_auto_reboot_tick)

        # Auto Reboot 상태 추적
        self.reboot_count = 0
        self.success_count = 0
        self.crash_count = 0
        self.total_run_seconds = 0
        self.auto_reboot_elapsed_sec = 0

        # Auto Reboot 설정은 UI에서 직접 읽어옴

        # Flag: after auto-unchecking "Check Q‑Symphony before reboot" due to forced dump,
        # re-enable it automatically when QS state becomes On again via monitoring
        self._should_reenable_check_qs_option = False

        # Q-Symphony Failed Dumps 카운터
        self.qs_failed_count = 0

        # Flag for tracking QS success after reboot
        self._waiting_qs_success_after_reboot = False

        # Flag for pausing interval countdown until device boot/connection recovery completes
        self._waiting_for_device_reconnect = False

        # Timer to force reboot 10s after Q-Symphony turns On (optional feature)
        self.reboot_on_qs_timer = QTimer(self)
        try:
            self.reboot_on_qs_timer.setSingleShot(True)
            self.reboot_on_qs_timer.setInterval(10000)
        except Exception:
            pass
        self.reboot_on_qs_timer.timeout.connect(self._on_qs_on_reboot_timeout)

        # Headless coredump status timer (updates "Extracting coredump... (Xs)" every second)
        self._coredump_status_timer = QTimer(self)
        try:
            self._coredump_status_timer.setInterval(1000)
        except Exception:
            pass
        self._coredump_status_timer.timeout.connect(self._on_coredump_status_tick)
        self._coredump_status_start_ts = None
        self._coredump_status_active = False

        # 마지막으로 관측된 Q‑Symphony 상태 캐시 ("On" / "Off" / "Unknown")
        self._last_symphony_state = "Unknown"

        self._setup_ui()
        self._load_auto_reboot_settings()
        self._load_upload_settings()

    def _setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Auto Reboot 그룹
        self.auto_reboot_group = self._create_auto_reboot_group()
        self.auto_reboot_group.setMinimumWidth(GROUP_MINIMUM_WIDTH)
        main_layout.addWidget(self.auto_reboot_group)

    def _create_auto_reboot_group(self):
        """Auto Reboot 그룹 생성"""
        auto_reboot_group_box = QGroupBox("Auto Reboot")
        auto_reboot_group_layout = QVBoxLayout()
        auto_reboot_group_box.setLayout(auto_reboot_group_layout)

        # Interval(sec): | LineEdit | Progress Bar | Button 한 줄 배치
        interval_control_layout = self._create_interval_control()
        auto_reboot_group_layout.addLayout(interval_control_layout)

        # Current Status with Duration
        current_status_widget = self._create_status_widget()
        auto_reboot_group_layout.addWidget(current_status_widget)

        # 좌우 배치를 위한 컨테이너
        config_stats_container = QWidget()
        config_stats_layout = QHBoxLayout()
        config_stats_layout.setContentsMargins(0, 0, 0, 0)
        config_stats_container.setLayout(config_stats_layout)

        # Reboot Configuration 그룹 (왼쪽)
        reboot_config_group = self._create_reboot_config_group()
        reboot_config_group.setMinimumWidth(300)
        config_stats_layout.addWidget(reboot_config_group)

        # Reboot Statistics 그룹 (오른쪽)
        reboot_stats_group = self._create_reboot_stats_group()
        reboot_stats_group.setMinimumWidth(300)
        config_stats_layout.addWidget(reboot_stats_group)

        # 컨테이너를 메인 레이아웃에 추가
        auto_reboot_group_layout.addWidget(config_stats_container)

        return auto_reboot_group_box

    def _create_interval_control(self):
        """Interval 컨트롤 라인 생성"""
        interval_control_layout = QHBoxLayout()

        # Interval 설정
        interval_control_layout.addWidget(QLabel("Interval(s):"))
        self.autoreboot_interval_edit = self.create_widget(
            QLineEdit, "autoreboot_interval_edit", UIElementGroup.SESSION_INVERSE, "100"
        )
        self.autoreboot_interval_edit.setEnabled(True)
        self.autoreboot_interval_edit.setValidator(QIntValidator(10, 3600))
        self.autoreboot_interval_edit.setMaximumWidth(
            50
        )  # 4자리 숫자 표현 가능한 폭으로 제한
        self.autoreboot_interval_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        interval_control_layout.addWidget(self.autoreboot_interval_edit)

        # Progress Bar (라벨 없음, 확장 가능)
        self.autoreboot_progress_bar = self.create_widget(
            QProgressBar, "autoreboot_progress_bar", UIElementGroup.ALWAYS_DISABLED
        )
        self.autoreboot_progress_bar.setRange(0, 60)
        self.autoreboot_progress_bar.setValue(0)
        self.autoreboot_progress_bar.setFormat("100s")
        self.autoreboot_progress_bar.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # 수평으로 확장 가능하도록 설정
        interval_control_layout.addWidget(self.autoreboot_progress_bar)

        # Start/Stop Button
        self.autoreboot_start_btn = self.create_widget(
            QPushButton, "autoreboot_start_btn", UIElementGroup.ALWAYS_ENABLED, "Start"
        )
        self.autoreboot_start_btn.clicked.connect(self.on_autoreboot_start_clicked)
        interval_control_layout.addWidget(self.autoreboot_start_btn)

        return interval_control_layout

    def _create_status_widget(self):
        """Status 위젯 생성"""
        current_status_widget = QWidget()
        current_status_layout = QHBoxLayout()
        current_status_layout.setContentsMargins(0, 0, 0, 0)
        current_status_layout.addWidget(QLabel("Status:"))
        self.ui_elements["current_status_label"] = QLabel("Stopped")
        current_status_layout.addWidget(self.ui_elements["current_status_label"])
        current_status_layout.addStretch()
        self.ui_elements["total_duration_label"] = QLabel("00:00:00")
        current_status_layout.addWidget(self.ui_elements["total_duration_label"])
        current_status_widget.setLayout(current_status_layout)
        return current_status_widget

    def _create_reboot_config_group(self):
        """Reboot Configuration 그룹 생성"""
        group = QGroupBox("Configuration")
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Sync before reboot
        self.sync_before_reboot_checkbox = self.create_widget(
            QCheckBox,
            "sync_before_reboot_checkbox",
            UIElementGroup.ALWAYS_ENABLED,
            "Sync before reboot",
        )
        self.sync_before_reboot_checkbox.setChecked(True)
        layout.addWidget(self.sync_before_reboot_checkbox)

        # Check QS before reboot
        self.check_qs_before_reboot_checkbox = self.create_widget(
            QCheckBox,
            "check_qs_before_reboot_checkbox",
            UIElementGroup.ALWAYS_ENABLED,
            "Check QS before reboot",
        )
        self.check_qs_before_reboot_checkbox.setChecked(False)
        layout.addWidget(self.check_qs_before_reboot_checkbox)

        # Do NOT reboot on QS fails (하위 옵션)
        do_not_reboot_widget = QWidget()
        do_not_reboot_layout = QHBoxLayout()
        do_not_reboot_layout.setContentsMargins(20, 0, 0, 0)  # 왼쪽에 20px 들여쓰기
        do_not_reboot_layout.setSpacing(0)  # 레이아웃 내부 스페이싱 제거
        do_not_reboot_widget.setLayout(do_not_reboot_layout)
        do_not_reboot_widget.setContentsMargins(0, 0, 0, 0)  # 위젯 외부 마진 제거

        self.do_not_reboot_on_qs_fails_checkbox = self.create_widget(
            QCheckBox,
            "do_not_reboot_on_qs_fails_checkbox",
            UIElementGroup.ALWAYS_ENABLED,
            "Do NOT reboot when QS fails",
        )
        self.do_not_reboot_on_qs_fails_checkbox.setChecked(False)
        do_not_reboot_layout.addWidget(self.do_not_reboot_on_qs_fails_checkbox)
        do_not_reboot_layout.addStretch()

        layout.addWidget(do_not_reboot_widget)

        # Reboot 10s after Q-Symphony turns On
        self.reboot_after_qs_on_checkbox = self.create_widget(
            QCheckBox,
            "reboot_after_qs_on_checkbox",
            UIElementGroup.ALWAYS_ENABLED,
            "Reboot 10s after QS turns On",
        )
        self.reboot_after_qs_on_checkbox.setChecked(False)
        layout.addWidget(self.reboot_after_qs_on_checkbox)

        # "Check QS before reboot" 체크박스 상태 변경 시그널 연결
        self.check_qs_before_reboot_checkbox.stateChanged.connect(
            self._on_check_qs_before_reboot_changed
        )

        # "Reboot 10s after QS turns On" 체크박스 상태 변경 시그널 연결
        self.reboot_after_qs_on_checkbox.stateChanged.connect(
            self._on_reboot_after_qs_on_changed
        )

        return group

    def _create_reboot_stats_group(self):
        """Reboot Statistics 그룹 생성"""
        group = QGroupBox("Statistics")
        layout = QVBoxLayout()
        group.setLayout(layout)

        # 통계 항목들 세로 배치
        stats_items = [
            ("Count:", "reboot_count_label", "0"),
            ("Success:", "success_count_label", "0"),
            ("Crash:", "crash_count_label", "0"),
            ("QS Failed:", "qs_failed_count_label", "0"),
        ]

        for label_text, attr_name, initial_value in stats_items:
            stat_widget = self._create_stat_widget(label_text, initial_value)
            setattr(self, attr_name, stat_widget.findChild(QLineEdit))
            layout.addWidget(stat_widget)

        return group

    def _create_stat_widget(self, label_text, initial_value):
        """통계 항목 위젯 생성"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        value_edit = QLineEdit(initial_value)
        value_edit.setReadOnly(True)
        value_edit.setFixedWidth(100)
        value_edit.setAlignment(Qt.AlignRight)  # 숫자 오른쪽 정렬

        layout.addWidget(label)
        layout.addStretch()  # 라벨과 LineEdit 사이에 공간 추가
        layout.addWidget(value_edit)

        widget.setLayout(layout)
        return widget

    def get_ui_elements(self):
        """UI 요소들 반환"""
        return self.ui_elements

    def update_ui_element(self, element_name, value):
        """특정 UI 요소 업데이트"""
        if element_name in self.ui_elements:
            widget = self.ui_elements[element_name]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QLabel):
                widget.setText(str(value))
            elif isinstance(widget, QCheckBox):
                if isinstance(value, bool):
                    widget.setChecked(value)
                else:
                    widget.setChecked(str(value).lower() == "true")

    # -----------------------------
    # Auto Reboot 관련 메서드
    # -----------------------------
    def _on_auto_reboot_tick(self):
        """Auto Reboot 타이머 틱 핸들러 - 시그널 기반으로 리팩토링"""
        if not self.auto_reboot_running:
            return

        if not self._waiting_for_device_reconnect:
            self.auto_reboot_elapsed_sec += 1
        self.total_run_seconds += 1

        # 주기 만료 시 동작: Event를 통해 DeviceWidget에 재부팅 요청
        if (
            not self._waiting_for_device_reconnect
            and self.auto_reboot_elapsed_sec
            >= int(self.ui_elements["autoreboot_interval_edit"].text())
        ):
            # 모든 필요한 정보를 Event 인자로 전달
            self._on_auto_reboot_timer_expired()

        self._update_auto_reboot_ui()
        self._update_auto_reboot_status()
        self._update_auto_reboot_current_status()

    def _on_auto_reboot_timer_expired(self):
        self.request_reboot()

    def request_reboot(self):
        self.auto_reboot_started = True
        self._waiting_for_device_reconnect = True

        LOGI(f"AutoRebootGroup: Requesting reboot for {self.device_context.serial}")
        if self.is_check_qs_before_reboot_enabled():
            # DeviceWidget 메서드 직접 호출로 QS 상태 확인
            default_monitor_feature = self.device_context.get_app_component(
                "default_monitor_feature"
            )
            if default_monitor_feature.is_symphony_success():
                # QS 성공 상태: 기존 이벤트 방식으로 재부팅 요청
                LOGI(
                    f"AutoRebootGroup: QS successful - rebooting device {self.device_context.serial}"
                )
                self.send_event(
                    CommonEventType.REBOOT_REQUESTED,
                    {"sync_before_reboot": self.is_sync_before_reboot_enabled()},
                )
            else:
                # QS 실패 상태: dump 요청
                LOGW(
                    f"AutoRebootGroup: "
                    f"QS failed - > extracting crash dump for {self.device_context.serial} due to QS failure"
                )
                self._request_dump_for_failed_qs()
        else:
            # QS 체크 없이 기존 이벤트 방식으로 재부팅 요청
            self.send_event(
                CommonEventType.REBOOT_REQUESTED,
                {"sync_before_reboot": self.is_sync_before_reboot_enabled()},
            )

    def send_event(self, event, args):
        self.event_manager.emit_event(event, args)

    def on_autoreboot_start_clicked(self):
        """Auto Reboot Start/Stop 버튼 클릭 핸들러"""
        if not self.auto_reboot_running:
            # Auto Reboot 시작
            self._start_auto_reboot()
        else:
            # Auto Reboot 중지
            self._stop_auto_reboot()

    def _reset_statistics(self):
        """통계 카운터 초기화"""
        self.reboot_count = 0
        self.success_count = 0
        self.crash_count = 0
        self.qs_failed_count = 0
        self.total_run_seconds = 0
        self._update_auto_reboot_status()

    def _start_auto_reboot(self):
        """Auto Reboot 시작 - Event 발행"""

        LOGD(f"AutoRebootGroup: Starting auto reboot for {self.device_context.serial}")

        self.dump_manager.set_dump_mode(DumpMode.HEADLESS)

        # Auto Reboot 설정 저장
        self._save_auto_reboot_settings()

        # Auto Reboot 상태만 관리하고 Event 발행
        self.auto_reboot_running = True
        self.auto_reboot_elapsed_sec = 0
        self.auto_reboot_timer.start()

        # 통계 초기화
        self._reset_statistics()

        self._update_auto_reboot_ui()
        self._update_auto_reboot_controls()
        self._update_auto_reboot_current_status()

        # 시작 시점 보정: 최근 상태가 On 이거나, 약간 지연 후 On 으로 판정되면 10s 타이머 시작
        try:
            if (
                self.is_reboot_after_qs_enabled()
                and self.dump_manager.get_state() == DumpState.IDLE
            ):
                if getattr(self, "_last_symphony_state", "Unknown") == "On":
                    self.start_reboot_on_qs_timer()
                else:
                    # DefaultMonitor 준비가 늦는 경우를 위해 지연 재평가
                    self._deferred_check_start_qs_on_timer(300)
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error during start-time QS-On check: {e}")

    def _stop_auto_reboot(self):
        """Auto Reboot 중지 - Event 발행"""

        LOGD(f"AutoRebootGroup: Stopping auto reboot for {self.device_context.serial}")

        self.dump_manager.set_dump_mode(DumpMode.DIALOG)

        # Auto Reboot 상태만 관리하고 Event 발행
        self.auto_reboot_started = False
        self.auto_reboot_running = False
        self.auto_reboot_timer.stop()

        # Stop 시 모든 상태 변수 초기화
        self._waiting_qs_success_after_reboot = False
        self._waiting_for_device_reconnect = False
        self._should_reenable_check_qs_option = False
        self.auto_reboot_elapsed_sec = 0

        # coredump 상태 타이머 초기화
        self._stop_coredump_status_timer()
        self._coredump_status_start_ts = None
        self._coredump_status_active = False

        # QS-On 타이머 중지
        if self.reboot_on_qs_timer.isActive():
            self.reboot_on_qs_timer.stop()

        self._update_auto_reboot_ui()
        self._update_auto_reboot_controls()
        self._update_auto_reboot_current_status()

    def _update_auto_reboot_ui(self):
        """Auto Reboot UI 업데이트"""
        # 버튼 텍스트 업데이트
        if "autoreboot_start_btn" in self.ui_elements:
            if self.auto_reboot_running:
                self.ui_elements["autoreboot_start_btn"].setText("Stop")
            else:
                self.ui_elements["autoreboot_start_btn"].setText("Start")

        # Progress bar 업데이트
        if "autoreboot_progress_bar" in self.ui_elements:
            remaining = max(
                0,
                int(self.ui_elements["autoreboot_interval_edit"].text())
                - self.auto_reboot_elapsed_sec,
            )
            self.ui_elements["autoreboot_progress_bar"].setMaximum(
                int(self.ui_elements["autoreboot_interval_edit"].text())
            )
            self.ui_elements["autoreboot_progress_bar"].setValue(
                self.auto_reboot_elapsed_sec
            )
            self.ui_elements["autoreboot_progress_bar"].setFormat(f"{remaining}s")

    def _update_auto_reboot_controls(self):
        """Auto Reboot 컨트롤 상태 업데이트"""
        self.ui_elements["autoreboot_interval_edit"].setEnabled(
            not self.auto_reboot_running
        )

    def _update_auto_reboot_status(self):
        """Auto Reboot 상태 정보 업데이트 - ui_elements 기반으로 통일"""
        # Reboot Count 업데이트
        self.reboot_count_label.setText(str(self.reboot_count))

        # Success Count 업데이트
        self.success_count_label.setText(str(self.success_count))

        # Crash Count 업데이트
        self.crash_count_label.setText(str(self.crash_count))

        # QS Failed Count 업데이트
        self.qs_failed_count_label.setText(str(self.qs_failed_count))

        hours = self.total_run_seconds // 3600
        minutes = (self.total_run_seconds % 3600) // 60
        seconds = self.total_run_seconds % 60
        self.ui_elements["total_duration_label"].setText(
            f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def _update_auto_reboot_current_status(self):
        """Auto Reboot Current Status 업데이트"""
        if not self.auto_reboot_running:
            self._set_current_status("Stopped")
        elif self._waiting_for_device_reconnect:
            self._set_current_status("Waiting for complete boot...")
        elif not self.device_context.adb_device.is_connected:
            self._set_current_status("Device disconnected")
        elif self.reboot_on_qs_timer.isActive():
            self._set_current_status("Reboot within 10s...")
        else:
            self._set_current_status("Waiting for reboot")

    def _load_auto_reboot_settings(self):
        """Auto Reboot 설정 로드"""

        try:
            # 설정 관리자에서 Auto Reboot 설정 가져오기
            auto_reboot_settings = self.device_context.settings_manager.get(
                "auto_reboot", {}
            )

            # 설정 적용 - UI에 직접 적용
            # UI 업데이트
            self.ui_elements["autoreboot_interval_edit"].setText(
                str(auto_reboot_settings.get("interval", 100))
            )
            self.ui_elements["sync_before_reboot_checkbox"].setChecked(
                auto_reboot_settings.get("sync_before_reboot", True)
            )
            self.ui_elements["check_qs_before_reboot_checkbox"].setChecked(
                auto_reboot_settings.get("check_qs_before_reboot", False)
            )
            self.ui_elements["do_not_reboot_on_qs_fails_checkbox"].setChecked(
                auto_reboot_settings.get("do_not_reboot_on_qs_fails", False)
            )
            self.ui_elements["reboot_after_qs_on_checkbox"].setChecked(
                auto_reboot_settings.get("reboot_after_qs_on", False)
            )

            # Progress bar 업데이트
            self.ui_elements["autoreboot_progress_bar"].setMaximum(
                auto_reboot_settings.get("interval", 100)
            )
            self.ui_elements["autoreboot_progress_bar"].setValue(0)
            self.ui_elements["autoreboot_progress_bar"].setFormat(
                f"{auto_reboot_settings.get('interval', 100)}s"
            )

            LOGD(
                f"AutoRebootGroup: Auto Reboot settings loaded and applied successfully"
            )
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error loading auto reboot settings: {e}")
            # 기본값으로 복구
            self.ui_elements["autoreboot_interval_edit"].setText(str(100))
            self.ui_elements["sync_before_reboot_checkbox"].setChecked(True)
            self.ui_elements["check_qs_before_reboot_checkbox"].setChecked(False)
            self.ui_elements["do_not_reboot_on_qs_fails_checkbox"].setChecked(False)
            self.ui_elements["reboot_after_qs_on_checkbox"].setChecked(False)
            LOGD(
                f"AutoRebootGroup: Auto Reboot settings restored to defaults due to error"
            )

    def _save_auto_reboot_settings(self):
        """Auto Reboot 설정 저장"""
        try:
            # UI에서 현재 설정 값 가져오기
            try:
                auto_reboot_interval = int(
                    self.ui_elements["autoreboot_interval_edit"].text()
                )
            except ValueError:
                auto_reboot_interval = 100
            # 설정 관리자에 저장

            auto_reboot_settings = {
                "interval": auto_reboot_interval,
                "sync_before_reboot": (
                    self.ui_elements["sync_before_reboot_checkbox"].isChecked()
                ),
                "check_qs_before_reboot": (
                    self.ui_elements["check_qs_before_reboot_checkbox"].isChecked()
                ),
                "reboot_after_qs_on": (
                    self.ui_elements["reboot_after_qs_on_checkbox"].isChecked()
                ),
                "do_not_reboot_on_qs_fails": (
                    self.ui_elements["do_not_reboot_on_qs_fails_checkbox"].isChecked()
                ),
            }

            self.device_context.settings_manager.set(
                "auto_reboot", auto_reboot_settings
            )
            LOGD(f"AutoRebootGroup: Auto Reboot settings saved: {auto_reboot_settings}")
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error saving auto reboot settings: {e}")

    def _load_upload_settings(self):
        """Upload 설정 로드"""
        try:
            # 설정 관리자에서 업로드 설정 가져오기
            if hasattr(self.device_context, "settings_manager"):
                upload_settings = self.device_context.settings_manager.get(
                    "dump.upload_settings", {}
                )

                # QS Failed 업로드 설정 적용
                qs_failed_upload_enabled = upload_settings.get("qs_failed_upload", True)

                # UI 업데이트
                if hasattr(self, "qs_failed_upload_checkbox"):
                    self.qs_failed_upload_checkbox.setChecked(qs_failed_upload_enabled)

                LOGD(f"AutoRebootGroup: Upload settings loaded: {upload_settings}")
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error loading upload settings: {e}")

    def on_auto_reboot_setting_changed(self):
        """Auto Reboot 설정 변경 시 즉시 저장"""
        try:
            self._save_auto_reboot_settings()
            LOGD(f"AutoRebootGroup: Auto Reboot setting changed and saved")
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error saving auto reboot setting on change: {e}")

    def _on_forced_dump_completed(self):
        """강제 덤프 완료 후 처리"""
        LOGD(
            "AutoRebootGroup: Forced dump completed. "
            "Performing reboot now and disabling 'Check Q‑Symphony before reboot'."
        )

        # 타이머와 상태 업데이트 (_on_dump_completed에서 이미 처리됨)
        self.auto_reboot_elapsed_sec = 0
        self._update_auto_reboot_ui()
        self._update_auto_reboot_current_status()

        LOGD("AutoRebootGroup: Status update called after dump completion")

        # dump 추출이 완료되면 auto_reboot_timer를 다시 시작
        if self.auto_reboot_running and not self.auto_reboot_timer.isActive():
            self.auto_reboot_timer.start()
            LOGD("AutoRebootGroup: Restarted auto_reboot_timer after dump extraction")

        # 상태 업데이트
        if self.auto_reboot_running:
            LOGD(
                f"AutoRebootGroup: Setting status to 'Rebooting after dump...' "
                f"(auto_reboot_running={self.auto_reboot_running})"
            )
            self._set_current_status("Rebooting after dump...")
        else:
            LOGD(
                f"AutoRebootGroup: Setting status to 'Stopped' (auto_reboot_running={self.auto_reboot_running})"
            )
            self._set_current_status("Stopped")

        # "Check Q‑Symphony before reboot" 옵션 자동 해제 및 설정 저장
        try:
            self.ui_elements["check_qs_before_reboot_checkbox"].setChecked(False)
            # 설정 저장
            auto_reboot_settings = {
                "interval": self.get_auto_reboot_interval(),
                "sync_before_reboot": self.is_sync_before_reboot_enabled(),
                "check_qs_before_reboot": False,
                "reboot_after_qs_on": self.is_reboot_after_qs_enabled(),
                "do_not_reboot_on_qs_fails": self.is_do_not_reboot_on_qs_fails_enabled(),
            }
            self.device_context.settings_manager.set(
                "auto_reboot", auto_reboot_settings
            )
            # QS가 On 되면 다시 활성화하도록 플래그 설정
            self._should_reenable_check_qs_option = True
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error disabling check_qs_before_reboot option: {e}")

        LOGD(
            f"AutoRebootGroup: QS Failed Dumps count will be handled by dump_completed event"
        )

        # 재부팅 실행은 Event 기반으로 처리됨
        LOGD(
            f"AutoRebootGroup: Reboot after dump will be handled by reboot_completed event"
        )

    # --------- UI helpers ---------
    def _on_qs_on_reboot_timeout(self):
        """QS-On 타이머 타임아웃 핸들러"""
        self.request_reboot()
        LOGD("AutoRebootGroup: QS-On reboot requested after 10s timeout")

    # --------- QS-On 타이머 시작 보조 ---------
    def _deferred_check_start_qs_on_timer(self, delay_ms: int = 300):
        """지연 후 현재 QS 상태를 재확인하여 필요 시 QS-On 10s 타이머를 시작"""

        def _check_and_start():
            try:
                if not self.is_reboot_after_qs_enabled():
                    return
                # 덤프 중에는 시작하지 않음
                if self.dump_manager.get_state() != DumpState.IDLE:
                    return
                # 이미 10s 타이머가 돌고 있으면 중복 시작하지 않음
                if self.reboot_on_qs_timer.isActive():
                    return
                default_monitor_feature = self.device_context.get_app_component(
                    "default_monitor_feature"
                )
                if (
                    default_monitor_feature
                    and default_monitor_feature.is_symphony_success()
                ):
                    self.start_reboot_on_qs_timer()
            except Exception as e:
                LOGD(f"AutoRebootGroup: Deferred QS-On check failed: {e}")

        try:
            QTimer.singleShot(delay_ms, _check_and_start)
        except Exception:
            # singleShot 사용 불가 환경에서도 즉시 한번 시도
            _check_and_start()

    def _start_coredump_status_timer(self):
        """Start periodic UI updates for headless coredump extraction."""
        try:
            import time as _time

            self._coredump_status_start_ts = _time.time()
            self._coredump_status_active = True
            if not self._coredump_status_timer.isActive():
                self._coredump_status_timer.start()
            # Immediate initial update
            self._set_current_status("Extracting coredump... (0s)")
            LOGD("AutoRebootGroup: Started headless coredump status timer")
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error starting coredump status timer: {e}")

    def _stop_coredump_status_timer(self):
        """Stop periodic UI updates for headless coredump extraction."""
        try:
            self._coredump_status_active = False
            if self._coredump_status_timer.isActive():
                self._coredump_status_timer.stop()
            LOGD("AutoRebootGroup: Stopped headless coredump status timer")
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error stopping coredump status timer: {e}")
        finally:
            self._coredump_status_start_ts = None

    def _on_coredump_status_tick(self):
        """Tick handler to update 'Extracting coredump...' elapsed seconds."""
        try:
            if (
                not getattr(self, "_coredump_status_active", False)
                or self._coredump_status_start_ts is None
            ):
                return
            import time as _time

            elapsed = int(_time.time() - self._coredump_status_start_ts)
            if elapsed < 0:
                elapsed = 0
            self._set_current_status(f"Extracting coredump... ({elapsed}s)")
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error updating coredump status timer: {e}")

    def _on_check_qs_before_reboot_changed(self, state):
        """Check QS before reboot 체크박스 상태 변경 핸들러"""
        # 하위 옵션 활성화/비활성화
        if "do_not_reboot_on_qs_fails_checkbox" in self.ui_elements:
            self.ui_elements["do_not_reboot_on_qs_fails_checkbox"].setEnabled(
                state == Qt.CheckState.Checked.value
            )

    def _on_reboot_after_qs_on_changed(self, state):
        """Reboot 10s after QS turns On 체크박스 상태 변경 핸들러"""
        if state == Qt.CheckState.Unchecked.value:
            # 체크박스가 해제된 경우 타이머 중지
            if self.reboot_on_qs_timer.isActive():
                self.reboot_on_qs_timer.stop()
                LOGD(
                    "AutoRebootGroup: Stopped reboot_on_qs_timer due to checkbox unchecked"
                )
                # 상태 업데이트
                self._update_auto_reboot_current_status()
        elif state == Qt.CheckState.Checked.value:
            # 체크박스가 체크된 경우: 최근 상태가 On 이면 즉시, 아니면 지연 재평가로 시작
            try:
                if (
                    self.is_reboot_after_qs_enabled()
                    and self.dump_manager.get_state() == DumpState.IDLE
                ):
                    if getattr(self, "_last_symphony_state", "Unknown") == "On":
                        if not self.reboot_on_qs_timer.isActive():
                            self.start_reboot_on_qs_timer()
                    else:
                        self._deferred_check_start_qs_on_timer(300)
            except Exception as e:
                LOGD(
                    f"AutoRebootGroup: Error handling reboot_after_qs_on checkbox: {e}"
                )

    def _on_qs_failed_upload_changed(self, state):
        """QS Failed 덤프 자동 업로드 설정 변경 처리"""
        try:
            enabled = state == Qt.CheckState.Checked.value
            if hasattr(self.device_context, "settings_manager"):
                # 업로드 설정 가져오기
                upload_settings = self.device_context.settings_manager.get(
                    "dump.upload_settings", {}
                )
                upload_settings["qs_failed_upload"] = enabled
                self.device_context.settings_manager.set(
                    "dump.upload_settings", upload_settings
                )
                LOGD(f"AutoRebootGroup: QS Failed upload setting changed to {enabled}")
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error processing QS Failed upload change: {e}")

    def _set_current_status(self, text: str):
        """Current Status 레이블을 업데이트합니다."""
        try:
            if (
                "current_status_label" in self.ui_elements
                and self.ui_elements["current_status_label"] is not None
            ):
                self.ui_elements["current_status_label"].setText(str(text))

            # 상태바 업데이트를 위한 이벤트 발행
            self.event_manager.emit_event(
                QSMonitorEventType.AUTO_REBOOT_STATUS_CHANGED,
                {"status": str(text), "is_running": self.auto_reboot_running},
            )
        except Exception as e:
            LOGD(f"AutoRebootGroup: Error updating current status: {e}")

    # -----------------------------
    # UI 상태 읽기 메서드
    # -----------------------------
    def is_sync_before_reboot_enabled(self):
        """Sync before reboot 체크박스 상태 확인"""
        try:
            if "sync_before_reboot_checkbox" in self.ui_elements:
                return self.ui_elements["sync_before_reboot_checkbox"].isChecked()
            return False
        except Exception:
            return False

    def is_check_qs_before_reboot_enabled(self):
        """Check QS before reboot 체크박스 상태 확인"""
        return self.ui_elements["check_qs_before_reboot_checkbox"].isChecked()

    def is_reboot_after_qs_enabled(self):
        """Reboot 10s after QS turns on 체크박스 상태 확인"""
        return self.ui_elements["reboot_after_qs_on_checkbox"].isChecked()

    def is_do_not_reboot_on_qs_fails_enabled(self):
        """Do NOT reboot on QS fails 체크박스 상태 확인"""
        try:
            if "do_not_reboot_on_qs_fails_checkbox" in self.ui_elements:
                return self.ui_elements[
                    "do_not_reboot_on_qs_fails_checkbox"
                ].isChecked()
            return False
        except Exception:
            return False

    def get_auto_reboot_interval(self):
        """Auto Reboot 인터벌 값 확인"""
        return int(self.ui_elements["autoreboot_interval_edit"].text())

    def is_auto_reboot_running(self):
        """Auto Reboot 실행 상태 확인"""
        return self.auto_reboot_running

    def get_auto_reboot_statistics(self):
        """Auto Reboot 통계 정보 확인"""
        return {
            "reboot_count": self.reboot_count,
            "success_count": self.success_count,
            "crash_count": self.crash_count,
            "qs_failed_count": self.qs_failed_count,
            "total_run_seconds": self.total_run_seconds,
        }

    def get_auto_reboot_settings(self):
        """Auto Reboot 관련 모든 설정 상태 확인"""
        return {
            "sync_before_reboot": self.is_sync_before_reboot_enabled(),
            "check_qs_before_reboot": self.is_check_qs_before_reboot_enabled(),
            "do_not_reboot_on_qs_fails": self.is_do_not_reboot_on_qs_fails_enabled(),
            "reboot_after_qs_on": self.is_reboot_after_qs_enabled(),
            "interval": self.get_auto_reboot_interval(),
            "is_running": self.is_auto_reboot_running(),
        }

    # -----------------------------
    # Event 핸들러 메서드
    # -----------------------------
    def _on_reboot_completed(self, args):
        """재부팅 완료 Event 핸들러 - Reboot Count 업데이트"""
        # Auto Reboot 실행 중이 아닌 경우 즉시 반환
        if not self.auto_reboot_running:
            LOGD(
                "AutoRebootGroup: Reboot completed but AutoReboot is not running - statistics not updated"
            )
            return

        result = args.get("result", None)
        LOGD(f"AutoRebootGroup: Reboot completed with result: {result}")

        # Reboot Count 업데이트
        self.reboot_count += 1

        # Statistics UI 업데이트
        self._update_auto_reboot_status()

        self._waiting_qs_success_after_reboot = True

        # 재부팅 요청 직후 연결 복구 전까지 interval 카운트는 정지
        self.auto_reboot_elapsed_sec = 0
        self._update_auto_reboot_ui()
        LOGD(
            "AutoRebootGroup: Auto reboot interval reset and waiting for device reconnect"
        )

    def _on_device_connection_changed(self, args):
        """디바이스 연결 상태 변경 Event 핸들러 - 재연결 시 interval 카운트 재개"""
        if not self.auto_reboot_running:
            return

        connected = args.get("connected", False)

        if connected and self._waiting_for_device_reconnect:
            self._waiting_for_device_reconnect = False
            self.auto_reboot_elapsed_sec = 0
            self._update_auto_reboot_ui()
            self._update_auto_reboot_current_status()
            LOGD(
                "AutoRebootGroup: Device reconnected - restarting interval countdown"
            )

    def _on_dump_completed(self, args):
        """덤프 완료 Event 핸들러 - 재부팅 실행"""
        # Auto Reboot 실행 중이 아닌 경우 즉시 반환
        if not self.auto_reboot_running:
            LOGD(
                "AutoRebootGroup: Dump completed but AutoReboot is not running - reboot not executed"
            )
            return

        triggered_by = args.get("triggered_by", None)
        success = args.get("success", False)

        LOGD(
            f"AutoRebootGroup: Dump completed event - triggered_by: {triggered_by}, success: {success}"
        )

        # coredump 상태 타이머 중지
        self._stop_coredump_status_timer()

        # AutoReboot 실행 중인 경우에만 재부팅 실행
        if success:
            # dump 완료 후 재부팅 실행
            LOGD(
                "AutoRebootGroup: Dump completed successfully - executing reboot after dump"
            )

            # "Do NOT reboot when QS fails" 옵션 확인 (QS_FAILED 트리거인 경우만)
            if (
                triggered_by == DumpTriggeredBy.QS_FAILED.value
                and self.is_do_not_reboot_on_qs_fails_enabled()
            ):
                # 옵션이 활성화된 경우: AutoReboot 중지 및 상태 업데이트
                LOGD(
                    "AutoRebootGroup: 'Do NOT reboot when QS fails' is enabled - stopping AutoReboot after dump"
                )
                self._stop_auto_reboot()
                self._set_current_status("Dump completed - AutoReboot stopped")
            else:
                # 옵션이 비활성화되거나 다른 트리거인 경우: 재부팅 요청
                self.send_event(
                    CommonEventType.REBOOT_REQUESTED,
                    {"sync_before_reboot": self.is_sync_before_reboot_enabled()},
                )
        else:
            # dump 실패한 경우
            LOGD("AutoRebootGroup: Dump failed - handling failure")
            # 실패 시 타이머 재시작
            if self.auto_reboot_running and not self.auto_reboot_timer.isActive():
                self.auto_reboot_timer.start()
                LOGD("AutoRebootGroup: Restarted auto_reboot_timer after dump failure")

    def _on_crash_detected(self, args):
        """크래시 감지 Event 핸들러 - Crash Count 업데이트"""
        # Auto Reboot 실행 중이 아닌 경우 즉시 반환
        if not self.auto_reboot_running:
            LOGD(
                "AutoRebootGroup: Crash detected but AutoReboot is not running - Crash count not updated"
            )
            return

        crash_info = args.get("crash_info", {})
        LOGD(f"AutoRebootGroup: Crash detected event - info: {crash_info}")

        # Crash Count 업데이트
        self.crash_count += 1
        LOGD(
            f"AutoRebootGroup: Crash count updated to {self.crash_count} (AutoReboot running)"
        )

        # Statistics UI 업데이트
        self._update_auto_reboot_status()

    def _register_specific_event_handlers(self, event_manager):
        """AutoRebootGroup 특정 Event 핸들러 등록"""
        event_manager.register_event_handler(
            CommonEventType.REBOOT_COMPLETED, self._on_reboot_completed
        )
        event_manager.register_event_handler(
            CommonEventType.DUMP_COMPLETED, self._on_dump_completed
        )
        event_manager.register_event_handler(
            CommonEventType.DUMP_STARTED, self._on_dump_started
        )
        event_manager.register_event_handler(
            CommonEventType.DUMP_ERROR, self._on_dump_error
        )
        event_manager.register_event_handler(
            QSMonitorEventType.CRASH_DETECTED, self._on_crash_detected
        )
        event_manager.register_event_handler(
            QSMonitorEventType.SYMPHONY_GROUP_STATE_CHANGED,
            self._on_symphony_group_state_changed,
        )
        event_manager.register_event_handler(
            CommonEventType.DEVICE_CONNECTION_CHANGED,
            self._on_device_connection_changed,
        )
        LOGD("AutoRebootGroup: Registered specific event handlers")

    def _on_dump_started(self, args):
        """Dump 시작 이벤트 핸들러"""
        if not self.auto_reboot_running:
            return

        triggered_by = args.get("triggered_by")
        LOGI(
            f"AutoRebootGroup: Dump extraction started via EventManager - triggered_by: {triggered_by}"
        )

        if triggered_by == DumpTriggeredBy.CRASH_MONITOR.value:
            # Crash Count 증가
            self.crash_count += 1
            LOGI(
                f"AutoRebootGroup: Crash count updated to {self.crash_count} (CRASH_MONITOR triggered)"
            )
        elif triggered_by == DumpTriggeredBy.QS_FAILED.value:
            # QS Failed Count 증가
            self.qs_failed_count += 1
            LOGI(
                f"AutoRebootGroup: QS Failed count updated to {self.qs_failed_count} (QS_FAILED triggered)"
            )

        self._update_auto_reboot_status()
        self._start_coredump_status_timer()

    def _on_dump_error(self, args):
        """Dump 에러 이벤트 핸들러"""
        error_message = args.get("error_message", "")
        LOGD(f"AutoRebootGroup: Dump extraction error: {error_message}")
        self._stop_coredump_status_timer()

    def _request_dump_for_failed_qs(self):
        """QS 실패 시 dump 생성 요청"""
        LOGI("AutoRebootGroup: QS failed - requesting GLOBAL dump generation")

        # Auto Reboot 타이머 일시 중지
        if self.auto_reboot_timer.isActive():
            self.auto_reboot_timer.stop()
            LOGD("AutoRebootGroup: Stopped auto_reboot_timer for dump generation")

        # 전역 덤프 요청 이벤트 발행
        try:
            issue_ts = TimestampGenerator.get_log_timestamp()

            # 통합된 업로드 설정 사용 (GeneralTab의 마스터 설정)
            upload_enabled = False
            if hasattr(self.device_context, "settings_manager"):
                upload_settings = self.device_context.settings_manager.get(
                    "dump.upload_settings", {}
                )
                upload_enabled = upload_settings.get("auto_upload_enabled", True)

            get_global_event_bus().emit_event(
                GlobalEventType.UNIFIED_DUMP_REQUESTED,
                {
                    "triggered_by": DumpTriggeredBy.QS_FAILED.value,
                    "request_device_id": self.device_context.serial,
                    "timestamp": issue_ts,
                    "upload_enabled": upload_enabled,
                },
            )
            LOGI(
                f"AutoRebootGroup: UNIFIED_DUMP_REQUESTED emitted (issue_id={issue_ts}, upload_enabled={upload_enabled})"
            )
        except Exception as e:
            LOGE(f"AutoRebootGroup: Failed to emit GLOBAL_DUMP_REQUESTED: {e}")

    def _on_symphony_group_state_changed(self, args):
        """Symphony 그룹 상태 변경 signal 핸들러 - Success Count 및 QS-On 타이머 처리"""
        # 이벤트 인자에서 상태 추출 및 캐시 갱신 (실행 중이 아니어도 최신 상태는 기억)
        state = args.get("state", "Unknown")
        try:
            self._last_symphony_state = state
        except Exception:
            pass

        LOGD(
            f"AutoRebootGroup: Symphony group state changed signal received with state: {state}"
        )

        # Auto Reboot 실행 중이 아니면 통계/타이머는 처리하지 않음 (상태 캐시만 유지)
        if not self.auto_reboot_running:
            LOGD(
                "AutoRebootGroup: "
                "Symphony group state changed but AutoReboot is not running - skipping timer/stat updates"
            )
            return

        # state가 'On'인 경우에만 처리
        if state != "On":
            LOGD("AutoRebootGroup: Symphony state is not 'On', skipping processing")
            return

        if self.auto_reboot_started:
            self.success_count += 1
            self._update_auto_reboot_status()

        # 덤프 중에는 10초 타이머 시작하지 않음
        if self.dump_manager.get_state() != DumpState.IDLE:
            return

        # "Reboot 10s after QS turns On" 체크박스가 활성화된 경우 타이머 시작
        if self.is_reboot_after_qs_enabled():
            if not self.reboot_on_qs_timer.isActive():
                self.start_reboot_on_qs_timer()

    def start_reboot_on_qs_timer(self):
        if self.reboot_on_qs_timer:
            if self.reboot_on_qs_timer.isActive():
                LOGW("AutoRebootGroup: Reboot 10s timer already running")
                return
            self.reboot_on_qs_timer.start()
            LOGD("AutoRebootGroup: Starting 10s timer for QS-On reboot")

    # -----------------------------
    # BaseEventWidget 추상 메서드 구현
    # -----------------------------

    def update_ui(self, data):
        """
        UI 업데이트 메서드 (BaseEventWidget 추상 메서드 구현)

        Args:
            data: UI 업데이트에 필요한 데이터
        """
        # AutoRebootGroup은 현재 데이터 기반 UI 업데이트가 필요 없음
        # 필요시 구현 가능
        pass
