from typing import Optional, Callable, List, Tuple

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QPushButton,
    QVBoxLayout,
)

from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.QSMonitor.features.DefaultMonitor.DefaultMonitorFeature import (
    DefaultMonitorFeature,
)
from QSUtils.QSMonitor.features.NetworkMonitor.NetworkMonitorFeature import (
    NetworkMonitorFeature,
)
from QSUtils.QSMonitor.features.SpeakerGrid.SpeakerGridFeature import SpeakerGridFeature
from QSUtils.UIFramework.base import DeviceContext, DeviceCommandExecutor
from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.Utils import LOGD


class GeneralTab(QWidget):

    update_ui_signal = Signal(object, object)  # handler, result

    def __init__(
        self,
        parent: QWidget,
        device_context: DeviceContext,
        command_handler: CommandHandler,
        toggle_state_callback: Optional[Callable[[bool], None]],
    ) -> None:
        super().__init__(parent)

        self.device_context = device_context
        self.command_handler = command_handler
        self.toggle_state_callback = toggle_state_callback
        # SettingsManager 바로 참조 (hasattr 체크 감소)
        self.settings_manager = self.device_context.settings_manager

        self._setup_ui()

        self.general_monitoring_running = False

        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.setSingleShot(True)
        # (handler, result) 쌍을 메인 스레드에서만 관리
        self.pending_ui_updates: List[Tuple[object, object]] = []

        self.update_ui_signal.connect(self._on_update_ui_received)

        self.ui_update_timer.timeout.connect(self._batch_update_ui)

        self.default_monitor_feature = DefaultMonitorFeature(
            self, self.device_context, self.command_handler
        )
        self.device_context.register_app_component(
            "default_monitor_feature", self.default_monitor_feature
        )

        self.network_monitor_feature = NetworkMonitorFeature(
            self, self.device_context, self.command_handler
        )
        self.device_context.register_app_component(
            "network_monitor_feature", self.network_monitor_feature
        )

        self.speaker_grid_feature = SpeakerGridFeature(
            self, self.device_context, self.command_handler
        )
        self.device_context.register_app_component(
            "speaker_grid_feature", self.speaker_grid_feature
        )

        self.command_executor = DeviceCommandExecutor(
            self.device_context.adb_device,
            self.device_context.feature_registry,
            result_callback=self.update_ui_with_result,
        )

        self.device_context.register_app_component(
            "command_executor", self.command_executor
        )

        self.monitoring_groups = self._create_monitoring_group()
        # 레이아웃은 _setup_ui 에서 보장되지만, Optional 경고 방지를 위해 명시 레퍼런스 사용
        self.main_layout.addWidget(self.monitoring_groups)

        self.main_layout.addWidget(self.default_monitor_feature.get_widget())
        self.main_layout.addWidget(self.network_monitor_feature.get_widget())
        self.main_layout.addWidget(self.speaker_grid_feature.get_widget())

        # AutoReboot에서 발생하는 auto_reboot_status_changed 이벤트 핸들러 등록
        self.device_context.event_manager.register_event_handler(
            QSMonitorEventType.AUTO_REBOOT_STATUS_CHANGED,
            self._on_auto_reboot_status_changed,
        )
        LOGD("GeneralTab: Registered auto_reboot_status_changed event handler")

        self._load_monitoring_settings()
        self._load_upload_settings()

        self.all_features_set_enabled(False)

    def __del__(self):
        """소멸자 - 안전한 정리"""
        try:
            self.cleanup()
        except Exception:
            # 파이널라이저 단계에서 예외 무시
            pass

    def cleanup(self):
        """명시적 정리: 이벤트 핸들러, 타이머, 컴포넌트 등록해제 등"""
        # 상태 변수 초기화
        try:
            self._reset_state_variables()
        except Exception:
            pass

        # 명령 실행 중지
        try:
            if hasattr(self, "command_executor"):
                self.command_executor.stop_execution()
        except Exception:
            pass

        # UI 업데이트 타이머 중지
        try:
            if hasattr(self, "ui_update_timer"):
                self.ui_update_timer.stop()
        except Exception:
            pass

        # 이벤트 핸들러 해제
        try:
            if hasattr(self.device_context, "event_manager"):
                self.device_context.event_manager.unregister_event_handler(
                    QSMonitorEventType.AUTO_REBOOT_STATUS_CHANGED,
                    self._on_auto_reboot_status_changed,
                )
        except Exception:
            pass

        # 시그널 해제
        try:
            self.update_ui_signal.disconnect(self._on_update_ui_received)
        except Exception:
            pass
        try:
            self.ui_update_timer.timeout.disconnect(self._batch_update_ui)
        except Exception:
            pass

        # 앱 컴포넌트 등록 해제 (덮어쓰기/수명 관리)
        try:
            self.device_context.unregister_app_component("default_monitor_feature")
            self.device_context.unregister_app_component("network_monitor_feature")
            self.device_context.unregister_app_component("speaker_grid_feature")
            self.device_context.unregister_app_component("command_executor")
        except Exception:
            pass

    def closeEvent(self, event):  # type: ignore[override]
        """창/위젯이 닫힐 때 안전하게 정리"""
        self.cleanup()
        event.accept()

    def _reset_state_variables(self):
        """모든 상태 변수를 초기값으로 리셋"""
        # DefaultMonitorFeature의 상태 리셋
        self.default_monitor_feature.reset_state_variables()

        # NetworkMonitorFeature의 상태 리셋
        self.network_monitor_feature.reset_state_variables()

        # SpeakerGridFeature의 상태 리셋
        self.speaker_grid_feature.reset_state_variables()

        # DeviceWidget의 상태 변수 리셋
        self.pending_ui_updates.clear()

    def _setup_ui(self):
        """기본 UI 레이아웃 설정"""
        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

    def _create_monitoring_group(self) -> QGroupBox:
        monitoring_group_box = QGroupBox("Monitoring")
        monitoring_group_layout = QHBoxLayout()
        monitoring_group_box.setLayout(monitoring_group_layout)

        # Interval (ms) 라벨과 LineEdit
        monitoring_group_layout.addWidget(QLabel("Interval(ms):"))
        self.interval_edit = QLineEdit("500")
        self.interval_edit.setValidator(QIntValidator(500, 10000))
        self.interval_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.interval_edit.textChanged.connect(self.on_interval_changed)
        monitoring_group_layout.addWidget(self.interval_edit)

        # Start 버튼
        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.clicked.connect(lambda: self.on_toggle_clicked(manual=True))
        monitoring_group_layout.addWidget(self.toggle_btn)
        return monitoring_group_box

    def _create_upload_settings_group(self) -> QGroupBox:
        """업로드 설정 그룹 생성"""
        upload_group_box = QGroupBox("Upload Settings")
        upload_group_layout = QVBoxLayout()
        upload_group_box.setLayout(upload_group_layout)

        # Issue Upload Config 버튼
        self.upload_config_button = QPushButton("Issue Upload Config")
        self.upload_config_button.clicked.connect(self.on_upload_config_clicked)
        upload_group_layout.addWidget(self.upload_config_button)

        return upload_group_box

    def on_interval_changed(self, text):
        try:
            # 실행 간격 업데이트
            interval = int(text)
            if hasattr(self, "command_executor"):
                self.command_executor.set_exec_interval(interval)

            # 설정 관리자에 저장
            if hasattr(self, "settings_manager"):
                monitoring_settings = {"interval": interval}
                self.settings_manager.set("monitoring", monitoring_settings)
                LOGD(f"GeneralTab: Monitoring settings saved: {monitoring_settings}")

            LOGD(f"GeneralTab: Interval changed to {interval}ms and saved")
        except ValueError:
            LOGD(f"GeneralTab: Invalid interval value: {text}")
        except Exception as e:
            LOGD(f"GeneralTab: Error processing interval change: {e}")

    def on_upload_config_clicked(self):
        """Issue Upload Config 버튼 클릭 처리"""
        try:
            from QSUtils.JFrogUtils.JFrogConfigDialog import JFrogConfigDialog

            dialog = JFrogConfigDialog(self.settings_manager, self)
            result = dialog.exec()

            if result == 1:  # QDialog.Accepted
                LOGD("GeneralTab: JFrog configuration updated")
                # 설정이 변경되었으므로 필요한 경우 여기서 추가 처리 가능
            else:
                LOGD("GeneralTab: JFrog configuration cancelled")

        except Exception as e:
            LOGD(f"GeneralTab: Error opening JFrog config dialog: {e}")

    def on_auto_upload_changed(self, state):
        """통합된 덤프 자동 업로드 설정 변경 처리"""
        try:
            enabled = state == 2  # Qt.Checked = 2
            if hasattr(self, "settings_manager"):
                # 통합된 업로드 설정 저장
                upload_settings = self.settings_manager.get("dump.upload_settings", {})
                upload_settings["auto_upload_enabled"] = enabled
                self.settings_manager.set("dump.upload_settings", upload_settings)
                LOGD(f"GeneralTab: Auto upload setting changed to {enabled}")
        except Exception as e:
            LOGD(f"GeneralTab: Error processing auto upload change: {e}")

    def update_ui_with_result(self, handler, result):
        """Command 실행 결과를 UI 업데이트 시그널로 전송"""
        LOGD(
            f"GeneralTab: update_ui_with_result called with handler: {handler.__class__.__name__}, result: {result}"
        )

        if result is None:
            LOGD("GeneralTab: Result is None, skipping UI update")
            return

        # 메인 스레드에서 UI 업데이트를 위한 시그널 발신만 수행 (스레드 안전)
        self.update_ui_signal.emit(handler, result)

    def _on_update_ui_received(self, handler, result):
        """메인 스레드에서 UI 업데이트 시그널 수신 처리"""
        # UI 업데이트를 큐에 추가 (메인 스레드)
        try:
            self.pending_ui_updates.append((handler, result))
            # 큐 폭주 방지: 최대 200개로 제한 (초과분은 버림)
            if len(self.pending_ui_updates) > 200:
                overflow = len(self.pending_ui_updates) - 200
                if overflow > 0:
                    self.pending_ui_updates = self.pending_ui_updates[-200:]
                    LOGD(
                        f"GeneralTab: UI update queue trimmed by {overflow}, kept last 200"
                    )
        except Exception as e:
            LOGD(f"GeneralTab: Failed to enqueue UI update: {e}")
        # 이미 타이머가 실행 중이지 않으면 시작
        if not self.ui_update_timer.isActive():
            self.ui_update_timer.start(50)

    def _batch_update_ui(self):
        """배치 UI 업데이트 실행"""
        LOGD(
            f"GeneralTab: Starting batch UI update with {len(self.pending_ui_updates)} updates"
        )

        # 큐에 있는 모든 업데이트 처리
        updates = self.pending_ui_updates.copy()
        self.pending_ui_updates.clear()

        for handler, result in updates:
            # CommandHandler를 통해 일관된 방식으로 커맨드 처리
            self.command_handler.handle_with_default(handler, result)

        LOGD(f"GeneralTab: Batch UI update completed")

    def all_features_set_enabled(self, enabled: bool):
        self.default_monitor_feature.apply_session_state(enabled)
        self.network_monitor_feature.apply_session_state(enabled)
        self.speaker_grid_feature.apply_session_state(enabled)

    def on_toggle_clicked(self, manual: bool = False):
        if self.toggle_state_callback is not None:
            self.toggle_state_callback(manual)
        else:
            LOGD("GeneralTab: toggle_state_callback is None, ignoring toggle click")

    def _on_auto_reboot_status_changed(self, args):
        """Auto Reboot 상태 변경 시그널 핸들러"""
        if args.get("is_running", False):
            # Auto Reboot 시작된 경우
            # General Monitoring이 중지된 상태면 시작
            if not self.general_monitoring_running:
                LOGD("GeneralTab: Starting general monitoring due to auto reboot start")
                self.on_toggle_clicked(manual=True)
        else:
            # Auto Reboot 중지된 경우
            # General Monitoring도 함께 중지
            if self.general_monitoring_running:
                LOGD("GeneralTab: Stopping general monitoring due to auto reboot stop")
                self.on_toggle_clicked(manual=False)

            if hasattr(self, "toggle_btn") and self.toggle_btn:
                self.toggle_btn.setText("Start")

    def on_session_started(self, manual: bool):
        """세션 시작 시 QSMonitor 전용 작업"""
        if hasattr(self, "toggle_btn") and self.toggle_btn:
            self.toggle_btn.setText("Stop")

        # General tab 모니터링 상태 업데이트
        self.general_monitoring_running = True

        # 모니터링 간격 설정 및 메인 모니터링 타이머 시작
        try:
            monitoring_interval = int(self.interval_edit.text())
            if hasattr(self, "command_executor") and self.command_executor:
                self.command_executor.set_exec_interval(monitoring_interval)
                self.command_executor.start_execution()
                self.command_executor.execute_command_set()
        except (ValueError, AttributeError) as e:
            LOGD(f"GeneralTab: Failed to start command executor: {e}")

        # 모니터링 시작 시: 모든 기능 활성화
        self.all_features_set_enabled(True)

    def on_session_stopped(self):
        """세션 정지 시 QSMonitor 전용 정리"""
        # 상태 변수 초기화
        self._reset_state_variables()

        if hasattr(self, "toggle_btn") and self.toggle_btn:
            self.toggle_btn.setText("Start")

        # General tab 모니터링 상태 업데이트
        self.general_monitoring_running = False

        # 명령 정지
        try:
            if hasattr(self, "command_executor") and self.command_executor:
                self.command_executor.stop_execution()
        except (AttributeError, RuntimeError) as e:
            LOGD(f"GeneralTab: Failed to stop command executor: {e}")

        # UI 업데이트 타이머/큐 정리
        try:
            if self.ui_update_timer.isActive():
                self.ui_update_timer.stop()
        except (AttributeError, RuntimeError) as e:
            LOGD(f"GeneralTab: Failed to stop UI timer: {e}")
        try:
            self.pending_ui_updates.clear()
        except (AttributeError, RuntimeError) as e:
            LOGD(f"GeneralTab: Failed to clear pending updates: {e}")

        # 모니터링 중지 시: UI만 비활성화하고 내부 값은 유지
        self.all_features_set_enabled(False)

    def _load_monitoring_settings(self):
        """Monitoring group 설정 로드"""
        try:
            # 설정 관리자에서 Monitoring 설정 가져오기
            if hasattr(self, "settings_manager"):
                monitoring_settings = self.settings_manager.get("monitoring", {})

                # 설정 적용
                monitoring_interval = monitoring_settings.get("interval", 500)

                # UI 업데이트
                if hasattr(self, "interval_edit"):
                    self.interval_edit.setText(str(monitoring_interval))

                LOGD(f"GeneralTab: Monitoring settings loaded: {monitoring_settings}")
        except Exception as e:
            LOGD(f"GeneralTab: Error loading monitoring settings: {e}")

    def _load_upload_settings(self):
        """Upload 설정 로드 (설정 마이그레이션 포함)"""
        try:
            # 설정 관리자에서 업로드 설정 가져오기
            if hasattr(self, "settings_manager"):
                upload_settings = self.settings_manager.get("dump.upload_settings", {})

                # 설정 마이그레이션: 기존 설정이 있는 경우 새로운 통합 설정으로 변환
                auto_upload_enabled = upload_settings.get("auto_upload_enabled")
                if auto_upload_enabled is None:
                    # 기존 설정에서 마이그레이션
                    crash_monitor_upload = upload_settings.get(
                        "crash_monitor_upload", True
                    )
                    qs_failed_upload = upload_settings.get("qs_failed_upload", True)
                    # 둘 중 하나라도 활성화되어 있으면 통합 설정을 활성화
                    auto_upload_enabled = crash_monitor_upload or qs_failed_upload

                    # 마이그레이션된 설정 저장
                    upload_settings["auto_upload_enabled"] = auto_upload_enabled
                    self.settings_manager.set("dump.upload_settings", upload_settings)
                    LOGD(
                        f"GeneralTab: Migrated upload settings to auto_upload_enabled={auto_upload_enabled}"
                    )

                # UI 업데이트
                if hasattr(self, "auto_upload_checkbox"):
                    self.auto_upload_checkbox.setChecked(auto_upload_enabled)

                LOGD(f"GeneralTab: Upload settings loaded: {upload_settings}")
        except Exception as e:
            LOGD(f"GeneralTab: Error loading upload settings: {e}")
