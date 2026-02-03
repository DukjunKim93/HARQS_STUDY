#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaseMainWindow
QSMonitor, QSLogger, QSAutoReboot에서 공통으로 사용하는 메인 윈도우 UI/로직을 제공.
UI는 공통 구성요소만 포함하고, 비즈니스 로직은 MainController를 통해 수행합니다.
서브클래스는 앱 설정 객체, 디바이스 윈도우 클래스를 지정하고
필요 시 추가 메뉴/기능을 확장합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Type, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QMessageBox,
    QMdiArea,
    QMdiSubWindow,
    QFileDialog,
    QSizePolicy,
    QCheckBox,
)

from QSUtils.JFrogUtils.JFrogUploadDialog import JFrogUploadDialog
from QSUtils.DumpManager.DumpTypes import DumpTriggeredBy
from QSUtils.QSMonitor.core.GlobalEvents import GlobalEventType
from QSUtils.QSMonitor.services.UnifiedDumpCoordinator import UnifiedDumpCoordinator
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.UIFramework.base.GlobalEventManager import get_global_event_bus
from QSUtils.UIFramework.base.MainController import MainController
from QSUtils.UIFramework.config.SettingsManager import SettingsManager
from QSUtils.UIFramework.widgets.BaseDeviceWidget import BaseDeviceWidget
from QSUtils.Utils.FileUtils import open_file_browser, ensure_directory_exists
from QSUtils.Utils.Logger import LOGD, LOGI


class BaseMainWindow(QMainWindow):
    """
    공통 메인 윈도우. 다음을 제공:
    - 디바이스 선택/새 창 추가
    - 로그 레벨 설정
    - 로그 경로 저장/변경/열기
    - MDI 영역 관리
    """

    def __init__(self, app_config: Any, device_window_cls: Type[BaseDeviceWidget]):
        super().__init__()
        self.app_config = app_config
        self.setWindowTitle(app_config.get_app_title())

        # 종료/해제 중 여부 플래그 (파괴된 Qt 객체 접근 방지)
        self._is_closing = False

        # 설정 관리자 초기화
        settings_manager = SettingsManager(
            app_config.get_config_file(), app_config.get_default_settings()
        )

        # Controller로 비즈니스 로직 분리
        self.controller = MainController(
            app_config=app_config, qt_parent=self, settings_manager=settings_manager
        )

        # 디바이스 서브윈도우 관리 목록: (serial, QMdiSubWindow)
        self.device_windows: List[Tuple[str, QMdiSubWindow]] = []

        # DeviceContext 관리 목록: (serial, DeviceContext)
        self.device_contexts: List[Tuple[str, DeviceContext]] = []

        self.device_window_cls = device_window_cls

        # JFrog 업로드 다이얼로그 관리
        self._current_upload_dialog = None

        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

        # Initialize device list
        self.refresh_devices()

        # Restore window geometry from settings
        geometry = self.controller.get_window_geometry()
        self.resize(geometry.get("width", 770), geometry.get("height", 980))
        if "x" in geometry and "y" in geometry:
            self.move(geometry["x"], geometry["y"])

        # Set minimum width to ensure usability
        self.setMinimumWidth(600)

        # Load log level from settings
        saved_log_level = self.controller.get_log_level()
        self.log_level_combo.setCurrentText(saved_log_level)
        self._apply_log_level(saved_log_level)

        # Initialize log path display
        initial_log_path = self.controller.settings_manager.get_log_directory()
        self.log_path_label.setText(initial_log_path)

        # Initialize log path controls state
        self.update_log_path_controls_state()

        # Initialize auto-upload checkbox state
        self._load_auto_upload_settings()

        # Log initialization message
        self.controller.log_initialization_message()

        # ---- Global Event Bus / Coordinator Initialization ----
        try:
            self._global_bus = get_global_event_bus()
            self._unified_dump_coordinator = UnifiedDumpCoordinator(self)
            self._unified_dump_coordinator.start()
            LOGD("BaseMainWindow: UnifiedDumpCoordinator started")

            # Register JFrog upload event handlers
            self._global_bus.register_event_handler(
                GlobalEventType.JFROG_UPLOAD_STARTED, self._on_jfrog_upload_started
            )
            self._global_bus.register_event_handler(
                GlobalEventType.JFROG_UPLOAD_COMPLETED, self._on_jfrog_upload_completed
            )
            LOGD("BaseMainWindow: Registered JFrog upload event handlers")
        except Exception as e:
            LOGD(f"BaseMainWindow: Failed to start UnifiedDumpCoordinator: {e}")

    # ---------------- UI ----------------
    def _setup_ui(self):
        # Device selection controls
        self.device_box = QComboBox()
        self.refresh_btn = QPushButton("Refresh")
        self.add_tab_btn = QPushButton("Add device")

        # Log level combobox
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(
            ["None", "Critical", "Error", "Warning", "Info", "Debug"]
        )
        self.log_level_combo.setCurrentText("Error")  # Default to Error

        # Log path controls
        self.log_path_label = QLabel()
        self.log_path_label.setWordWrap(True)
        self.log_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.change_log_path_btn = QPushButton("Change")
        self.change_log_path_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.open_log_folder_btn = QPushButton("Open Folder")
        self.open_log_folder_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Top layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Device:"))
        top.addWidget(self.device_box)
        top.addWidget(self.refresh_btn)
        top.addWidget(self.add_tab_btn)
        top.addStretch(1)
        top.addWidget(QLabel("Log Level:"))
        top.addWidget(self.log_level_combo)

        # Log path layout
        log_path_layout = QHBoxLayout()
        log_path_layout.addWidget(QLabel("Log Path:"))
        log_path_layout.addWidget(self.log_path_label, 1)  # stretch factor = 1
        log_path_layout.addWidget(self.change_log_path_btn)
        log_path_layout.addWidget(self.open_log_folder_btn)

        # Auto-upload dumps checkbox and Upload Config button
        self.auto_upload_checkbox = QCheckBox("Auto-upload dumps")
        self.upload_config_button = QPushButton("Upload Config")
        self.upload_config_button.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )

        # MDI area for device windows
        self.mdi_area = QMdiArea()
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setViewMode(QMdiArea.SubWindowView)

        # Upload settings layout
        upload_layout = QHBoxLayout()
        upload_layout.addWidget(self.auto_upload_checkbox)
        upload_layout.addStretch()  # 체크박스와 버튼 사이에 공간 추가
        upload_layout.addWidget(self.upload_config_button)

        # Main layout
        root = QVBoxLayout()
        root.addLayout(top)
        root.addLayout(log_path_layout)
        root.addLayout(upload_layout)
        root.addWidget(self.mdi_area)

        # Central widget
        w = QWidget()
        w.setLayout(root)
        self.setCentralWidget(w)

    def _setup_menu(self):
        # File 메뉴
        file_menu = self.menuBar().addMenu("File")
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # Window 메뉴
        window_menu = self.menuBar().addMenu("Window")

        # 기본 타일/캐스케이드/모두 닫기만 제공
        act_tile = QAction("Tile", self)
        act_tile.triggered.connect(self.mdi_area.tileSubWindows)
        window_menu.addAction(act_tile)

        act_cascade = QAction("Cascade", self)
        act_cascade.triggered.connect(self.mdi_area.cascadeSubWindows)
        window_menu.addAction(act_cascade)

        window_menu.addSeparator()

        act_close_all = QAction("Close All", self)
        act_close_all.triggered.connect(self.close_all_device_windows)
        window_menu.addAction(act_close_all)

    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.add_tab_btn.clicked.connect(self.add_device_window)
        self.log_level_combo.currentTextChanged.connect(self.on_log_level_changed)
        self.change_log_path_btn.clicked.connect(self.set_log_directory)
        self.open_log_folder_btn.clicked.connect(self.on_open_log_folder_clicked)
        self.auto_upload_checkbox.stateChanged.connect(self.on_auto_upload_changed)
        self.upload_config_button.clicked.connect(self.on_upload_config_clicked)

        # Connect device hub signals via controller
        self.controller.device_hub.deviceListUpdated.connect(
            self.on_device_list_updated
        )

    # ---------------- Slots / Logic (UI -> Controller) ----------------
    def refresh_devices(self):
        # 종료 또는 위젯 파괴 중이면 갱신하지 않음
        if getattr(self, "_is_closing", False):
            return
        try:
            serials = self.controller.list_devices()
        except Exception:
            return
        # device_box가 이미 파괴되었을 수 있으므로 모든 접근을 안전하게 처리
        try:
            current = self.device_box.currentText()
        except Exception:
            return

        # windows에 이미 추가된 디바이스는 제외
        added_devices = {serial for serial, _ in self.device_windows}
        available_devices = [s for s in serials if s not in added_devices]

        try:
            self.device_box.clear()
            self.device_box.addItems(available_devices)
            if current in available_devices:
                self.device_box.setCurrentText(current)
        except Exception:
            # 종료 중에 발생하는 예외 무시
            return

    def add_device_window(self):
        serial = self.device_box.currentText()
        if not serial:
            QMessageBox.warning(self, "ADB", "디바이스가 선택되지 않았습니다.")
            return

        # 중복 추가 방지
        for existing_serial, _ in self.device_windows:
            if existing_serial == serial:
                QMessageBox.warning(
                    self, "ADB", f"디바이스 {serial}는 이미 추가되었습니다."
                )
                return

        # DeviceContext 생성
        event_manager = EventManager()
        adb_device = self.controller.get_device_controller(serial)
        device_context = DeviceContext(
            event_manager, adb_device, self.controller.settings_manager
        )

        # DeviceContext 저장
        self.device_contexts.append((serial, device_context))

        # DeviceWindow 생성 (DeviceContext 전달)
        device_window = self.device_window_cls(self, device_context)
        LOGD(
            f"MainWindow: Creating device window for {serial} using DeviceContext architecture"
        )

        # 앱 시작 시 저장된 log_directory 값으로 초기화
        try:
            saved_log_dir = self.controller.settings_manager.get_log_directory()
            if saved_log_dir:
                device_context.set_log_directory(saved_log_dir)
        except Exception:
            pass

        # QMdiSubWindow로 래핑
        sub_window = QMdiSubWindow()
        sub_window.setWidget(device_window)
        sub_window.setWindowTitle(f"Device: {serial}")
        sub_window.setAttribute(Qt.WA_DeleteOnClose)

        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

        self.device_windows.append((serial, sub_window))
        sub_window.destroyed.connect(lambda: self.on_device_window_closed(serial))

        # 드롭다운에서 제거
        current_devices = self.controller.list_devices()
        if serial in current_devices:
            index = self.device_box.findText(serial)
            if index >= 0:
                self.device_box.removeItem(index)

        self.update_log_path_controls_state()

    def shutdown_all_tabs(self):
        """모든 디바이스 탭의 백그라운드 프로세스를 중지"""
        for _, sub_window in list(self.device_windows):
            widget = sub_window.widget()
            if widget and hasattr(widget, "get_device_tab"):
                tab = widget.get_device_tab()
                if tab and hasattr(tab, "is_running") and tab.is_running:
                    tab.on_toggle_clicked()

    def on_device_window_closed(self, serial: str):
        if getattr(self, "_is_closing", False):
            return
        # 리스트에서 제거
        self.device_windows = [(s, w) for s, w in self.device_windows if s != serial]

        # DeviceContext 정리
        for ctx_serial, device_context in self.device_contexts:
            if ctx_serial == serial:
                try:
                    device_context.cleanup()
                    LOGD(f"MainWindow: Cleaned up DeviceContext for {serial}")
                except Exception as e:
                    LOGD(
                        f"MainWindow: Error cleaning up DeviceContext for {serial}: {e}"
                    )
                break

        self.device_contexts = [
            (s, ctx) for s, ctx in self.device_contexts if s != serial
        ]

        # 종료 중 파괴된 위젯 접근을 피하기 위해 try 사용
        try:
            self.refresh_devices()
            self.update_log_path_controls_state()
        except Exception:
            pass

    def close_all_device_windows(self):
        for _, sub_window in list(self.device_windows):
            sub_window.close()
        self.device_windows.clear()
        self.update_log_path_controls_state()

    def on_log_level_changed(self, level_text):
        self._apply_log_level(level_text)

    def _apply_log_level(self, level_text):
        # 컨트롤러를 통해 로거/설정 적용
        self.controller.set_log_level(level_text)

    def on_device_list_updated(self, device_list):
        if getattr(self, "_is_closing", False):
            return
        self.refresh_devices()

    def set_log_directory(self):
        current_dir = self.controller.settings_manager.get_log_directory() or ""
        selected = QFileDialog.getExistingDirectory(
            self, "Select Log Directory", current_dir
        )
        if selected:
            self.controller.settings_manager.set_log_directory(selected)
            self.log_path_label.setText(selected)
            self.update_log_directory_for_all_devices(selected)

    def update_log_directory_for_all_devices(self, log_directory):
        for serial, sub_window in self.device_windows:
            widget = sub_window.widget()
            if widget and hasattr(widget, "device_context"):
                widget.device_context.set_log_directory(log_directory)

    def on_open_log_folder_clicked(self):
        """Open the current log directory in the system file browser.
        If no directory is set, prompt the user to select one first.
        """
        try:
            current_dir = self.controller.settings_manager.get_log_directory() or ""
            if not current_dir:
                # Ask user to select a directory first
                self.set_log_directory()
                current_dir = self.controller.settings_manager.get_log_directory() or ""
                if not current_dir:
                    return
            # Ensure directory exists
            ensure_directory_exists(current_dir)
            # Open in system file browser
            opened = open_file_browser(current_dir)
            if not opened:
                QMessageBox.warning(
                    self,
                    "Open Folder",
                    "파일 탐색기를 열 수 없습니다. 경로를 확인하세요.",
                )
        except Exception as e:
            QMessageBox.warning(
                self, "Open Folder", f"폴더 열기 중 오류가 발생했습니다:\n{e}"
            )

    def on_upload_config_clicked(self):
        """Issue Upload Config 버튼 클릭 처리"""
        try:
            from QSUtils.JFrogUtils.JFrogConfigDialog import JFrogConfigDialog

            dialog = JFrogConfigDialog(self.controller.settings_manager, self)
            result = dialog.exec()

            if result == 1:  # QDialog.Accepted
                LOGD("BaseMainWindow: JFrog configuration updated")
                # 설정이 변경되었으므로 필요한 경우 여기서 추가 처리 가능
            else:
                LOGD("BaseMainWindow: JFrog configuration cancelled")

        except Exception as e:
            LOGD(f"BaseMainWindow: Error opening JFrog config dialog: {e}")

    def on_auto_upload_changed(self, state):
        """Auto-upload dumps 체크박스 상태 변경 처리"""
        try:
            enabled = state == 2  # Qt.Checked = 2
            if hasattr(self, "controller") and hasattr(
                self.controller, "settings_manager"
            ):
                # 통합된 업로드 설정 저장
                upload_settings = self.controller.settings_manager.get(
                    "dump.upload_settings", {}
                )
                upload_settings["auto_upload_enabled"] = enabled
                self.controller.settings_manager.set(
                    "dump.upload_settings", upload_settings
                )
                LOGD(f"BaseMainWindow: Auto upload setting changed to {enabled}")
        except Exception as e:
            LOGD(f"BaseMainWindow: Error processing auto upload change: {e}")

    def _load_auto_upload_settings(self):
        """Auto-upload 설정 로드"""
        try:
            if hasattr(self, "controller") and hasattr(
                self.controller, "settings_manager"
            ):
                upload_settings = self.controller.settings_manager.get(
                    "dump.upload_settings", {}
                )
                auto_upload_enabled = upload_settings.get("auto_upload_enabled", True)
                if hasattr(self, "auto_upload_checkbox"):
                    self.auto_upload_checkbox.setChecked(auto_upload_enabled)
                LOGD(
                    f"BaseMainWindow: Auto upload settings loaded: {auto_upload_enabled}"
                )
        except Exception as e:
            LOGD(f"BaseMainWindow: Error loading auto upload settings: {e}")

    def update_log_path_controls_state(self):
        has_windows = len(self.device_windows) > 0
        # Allow changing and opening the log folder regardless of whether any device window exists.
        # This lets users set a log directory before adding devices.
        self.change_log_path_btn.setEnabled(True)
        self.open_log_folder_btn.setEnabled(True)

    # ---------------- JFrog Upload Event Handlers ----------------
    def _on_jfrog_upload_started(self, args: dict):
        """JFrog 업로드 시작 이벤트 핸들러"""
        from PySide6.QtCore import QTimer

        # UI 스레드에서 안전하게 실행되도록 QTimer 사용
        QTimer.singleShot(0, lambda: self._handle_jfrog_upload_started(args))

    def _handle_jfrog_upload_started(self, args: dict):
        """JFrog 업로드 시작 처리 실지 로직 (UI 스레드)"""
        try:
            if getattr(self, "_is_closing", False):
                return

            issue_id = args.get("issue_id")
            device_serial = args.get("device_serial")
            show_dialog = args.get("show_dialog", False)
            issue_root = args.get("issue_root")
            targets = args.get("targets", [])
            triggered_by = args.get("triggered_by")

            msg = f"JFrog 업로드 시작: {issue_id}"
            if device_serial:
                msg += f" (Device: {device_serial})"

            # UI 표시 요청이 있는 경우 JFrogUploadDialog 실행
            if show_dialog and issue_root:
                # 수동 덤프는 auto upload 설정과 무관하게 사용자 확인을 받음
                if triggered_by == DumpTriggeredBy.MANUAL.value:
                    reply = QMessageBox.question(
                        self,
                        "Upload Dump",
                        "덤프를 JFrog에 업로드할까요?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes,
                    )
                    if reply != QMessageBox.Yes:
                        event_data = {
                            "issue_id": issue_id,
                            "success": False,
                            "message": "Upload skipped by user",
                            "upload_info": None,
                            "device_serial": device_serial,
                            "device_serials": targets,
                            "uploaded_files": [],
                            "jfrog_links": {},
                            "manifest_path": str(Path(issue_root) / "manifest.json"),
                            "upload_id": issue_id,
                        }
                        self._global_bus.emit_event(
                            GlobalEventType.JFROG_UPLOAD_COMPLETED, event_data
                        )
                        return

                self._show_jfrog_upload_dialog(issue_id, issue_root, targets)

        except Exception as e:
            LOGD(f"BaseMainWindow: Error handling JFROG_UPLOAD_STARTED event: {e}")

    def _show_jfrog_upload_dialog(self, issue_id, issue_root, targets):
        """JFrog 업로드 다이얼로그 표시 및 실행"""
        try:
            # 기존 다이얼로그가 있으면 닫기
            if self._current_upload_dialog:
                try:
                    self._current_upload_dialog.close()
                except Exception:
                    pass

            # UnifiedDumpCoordinator에 있는 JFrogManager의 설정을 재사용
            config = self._unified_dump_coordinator._upload_manager.config
            dialog = JFrogUploadDialog(config, parent=self)
            self._current_upload_dialog = dialog  # 가비지 컬렉션 방지를 위해 참조 유지

            # 업로드 완료 시 처리를 위한 헬퍼 함수
            def on_upload_finished(success, message, result_data):
                from PySide6.QtCore import QTimer

                # UI 스레드에서 안전하게 결과 처리를 수행하도록 함
                QTimer.singleShot(
                    0,
                    lambda: self._handle_jfrog_upload_dialog_finished(
                        issue_id, issue_root, targets, success, message, result_data
                    ),
                )

            # Worker 생성 및 연결 (start_directory_upload 내부에서 수행됨)
            upload_prefix = "issues"
            if hasattr(self, "controller") and hasattr(
                self.controller, "settings_manager"
            ):
                upload_settings = self.controller.settings_manager.get(
                    "dump.upload_settings", {}
                )
                upload_prefix = upload_settings.get("upload_directory_prefix", "issues")
                if not upload_prefix:
                    upload_prefix = "issues"

            dialog.start_directory_upload(
                issue_root, f"{upload_prefix.rstrip('/')}/{issue_id}"
            )

            # 시그널 연결을 위해 worker에 접근
            if dialog.worker:
                dialog.worker.upload_completed.connect(on_upload_finished)

            LOGI(f"BaseMainWindow: JFrogUploadDialog started for issue {issue_id}")

        except Exception as e:
            LOGD(f"BaseMainWindow: Failed to show JFrogUploadDialog: {e}")

    def _handle_jfrog_upload_dialog_finished(
        self, issue_id, issue_root, targets, success, message, result_data
    ):
        """다이얼로그를 통한 업로드 완료 처리 (UI 스레드)"""
        try:
            # 참조 해제
            self._current_upload_dialog = None

            # 업로드된 파일 목록 수집
            uploaded_files = []
            try:
                from pathlib import Path

                root_path = Path(issue_root)
                if root_path.exists():
                    for file_path in root_path.rglob("*"):
                        if file_path.is_file():
                            uploaded_files.append(str(file_path))
            except Exception:
                pass

            # JFrog 링크 정보 구성
            jfrog_links = {}
            if result_data and "repo_url" in result_data:
                jfrog_links["repository"] = result_data["repo_url"]
            if result_data and "target_url" in result_data:
                jfrog_links["upload"] = result_data["target_url"]

            event_data = {
                "issue_id": issue_id,
                "success": success,
                "message": message,
                "upload_info": result_data,
                "device_serial": targets[0] if targets else None,
                "device_serials": targets,
                "uploaded_files": uploaded_files,
                "jfrog_links": jfrog_links,
                "manifest_path": str(Path(issue_root) / "manifest.json"),
                "upload_id": issue_id,
            }
            # 전역 버스를 통해 결과 알림 (Coordinator가 이를 수신하여 manifest 업데이트)
            self._global_bus.emit_event(
                GlobalEventType.JFROG_UPLOAD_COMPLETED, event_data
            )
            LOGD(f"BaseMainWindow: Emitted JFROG_UPLOAD_COMPLETED for issue {issue_id}")

        except Exception as e:
            LOGD(f"BaseMainWindow: Error in _handle_jfrog_upload_dialog_finished: {e}")

    def _on_jfrog_upload_completed(self, args: dict):
        """JFrog 업로드 완료 이벤트 핸들러"""
        from PySide6.QtCore import QTimer

        # UI 스레드에서 안전하게 실행되도록 QTimer 사용
        QTimer.singleShot(0, lambda: self._handle_jfrog_upload_completed(args))

    def _handle_jfrog_upload_completed(self, args: dict):
        """JFrog 업로드 완료 처리 실지 로직 (UI 스레드)"""
        try:
            # 종료 중이면 이벤트 무시
            if getattr(self, "_is_closing", False):
                return

            success = args.get("success", False)
            issue_id = args.get("issue_id")

            LOGI(
                f"BaseMainWindow: JFrog upload completed event - success: {success}, issue_id: {issue_id}"
            )

        except Exception as e:
            LOGD(f"BaseMainWindow: Error handling JFROG_UPLOAD_COMPLETED event: {e}")

    # ---------------- Global accessors ----------------
    def get_active_device_contexts(self) -> list[DeviceContext]:
        """현재 열려있는 활성 DeviceContext 목록 반환"""
        try:
            return [ctx for _, ctx in self.device_contexts]
        except Exception:
            return []

    # ---------------- Qt Overrides ----------------
    def closeEvent(self, event):
        # 닫힘 시작: 종료 플래그 설정 (이후 콜백/슬롯에서 UI 접근 금지)
        self._is_closing = True
        try:
            # 현재 윈도우 지오메트리 저장 (최대화 상태면 일반 지오메트리 사용)
            try:
                if self.isMaximized():
                    geo = self.normalGeometry()
                    width, height = geo.width(), geo.height()
                    x, y = geo.x(), geo.y()
                else:
                    width, height = self.width(), self.height()
                    x, y = self.x(), self.y()
                geometry = {
                    "width": int(width),
                    "height": int(height),
                    "x": int(x),
                    "y": int(y),
                }
                # 컨트롤러를 통해 설정 저장
                if hasattr(self, "controller") and hasattr(
                    self.controller, "settings_manager"
                ):
                    # 모든 앱이 "window_geometry" 키를 사용하도록 통일
                    self.controller.settings_manager.set_window_geometry(
                        geometry, "window_geometry"
                    )
            except Exception:
                pass

            # 종료 시 모든 백그라운드 중지
            self.shutdown_all_tabs()
            # 서브윈도우도 모두 닫기 (destroyed 콜백은 _is_closing으로 무시됨)
            self.close_all_device_windows()
            # Stop global coordinator
            try:
                if (
                    hasattr(self, "_unified_dump_coordinator")
                    and self._unified_dump_coordinator
                ):
                    self._unified_dump_coordinator.stop()
            except Exception:
                pass
        finally:
            super().closeEvent(event)
