#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device tab view for the LogViewer application.
"""

from collections import deque

from PySide6.QtCore import QProcess, QTimer, Signal, Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QTableWidget,
    QHeaderView,
    QAbstractItemView,
    QSpinBox,
    QTableWidgetItem,
    QFileDialog,
    QSplitter,
)

from QSUtils.QSLogger.views.HighlightConfigDialog import (
    HighlightConfigDialog,
    HighlightRule,
)
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.config.SettingsManager import SettingsManager
from QSUtils.UIFramework.widgets.BaseDeviceWidget import BaseDeviceWidget, SessionState
from QSUtils.Utils.Logger import LOGD


class DeviceWidget(BaseDeviceWidget):
    """
    Tab widget for displaying and controlling logs from a specific Android device.
    """

    # UI 업데이트를 위한 시그널
    update_ui_signal = Signal(object, object)  # handler, result

    def __init__(self, parent, device_context: DeviceContext):
        """
        Initialize the device tab.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext instance containing device-specific components
        """
        # BaseDeviceWidget.__init__에서 호출되는 _setup_app_specific_ui에서
        # self.max_log_lines 값을 사용하므로, super() 호출 전에 먼저 초기화한다.
        self.max_log_lines = 1000  # 기본 최대 로그 라인 수

        super().__init__(parent, device_context, min_width=400)
        # was_running_before_disconnect와 is_manual_start는 이제 BaseDeviceWidget에서 초기화됨

        # 프로세스 및 버퍼 (향후 사용 가능성을 위해 유지)
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.buf = bytearray()

        # UI & 타이머
        self.timer = QTimer(self)
        self.is_running = False

        # 비동기 명령어 실행을 위한 변수
        self.ui_update_timer = QTimer()
        self.ui_update_timer.setSingleShot(True)
        self.pending_ui_updates = []

        # UI 업데이트 시그널 연결
        self.update_ui_signal.connect(self._on_update_ui_received)

        # UI 업데이트 타이머 연결
        self.ui_update_timer.timeout.connect(self._batch_update_ui)

        # Track original enabled state for child widgets
        self._widget_enabled_states = {}

        # Filter Config Dialog 초기화
        self.filter_config_dialog = None

        # 필터 규칙 목록
        self.filter_rules = []

        # SettingsManager for persisting filter rules (QSLogger scope)
        # Prefer shared SettingsManager from parent hierarchy (MainWindow/Controller) to avoid overwriting on exit
        self.settings_manager = None
        try:
            p = parent
            while p is not None:
                if hasattr(p, "settings_manager") and p.settings_manager is not None:
                    self.settings_manager = p.settings_manager
                    break
                if hasattr(p, "controller") and hasattr(
                    p.controller, "settings_manager"
                ):
                    self.settings_manager = p.controller.settings_manager
                    break
                p = p.parent()
        except Exception:
            self.settings_manager = None

        if self.settings_manager is None:
            # Fallback: create our own SettingsManager (legacy behavior)
            from pathlib import Path

            config_dir = Path.home() / ".QSUtils"
            config_file = config_dir / "qslogger.json"
            default_settings = {
                "log_directory": str(Path.home() / "QSMonitor_logs"),
                "window_geometry": {"width": 770, "height": 980, "x": 200, "y": 200},
                "filter_rules": [],
                "log_level": "Error",
            }
            self.settings_manager = SettingsManager(config_file, default_settings)
        try:
            saved_rules = self.settings_manager.get_filter_rules() or []
            # Deserialize into HighlightRule objects
            self.filter_rules = [
                HighlightRule.from_dict(r) if isinstance(r, dict) else r
                for r in saved_rules
            ]
            if self.filter_rules:
                LOGD(
                    f"DeviceWidget: Loaded {len(self.filter_rules)} saved filter rules"
                )
        except Exception as e:
            LOGD(f"DeviceWidget: Failed to load filter rules: {e}")

        # Ensure filter dialog is initialized with any loaded rules so they are ready at startup
        try:
            if not self.filter_config_dialog:
                self.filter_config_dialog = HighlightConfigDialog(
                    self, self.filter_rules
                )
                self.filter_config_dialog.rules_changed.connect(
                    self._on_filter_rules_changed
                )
        except Exception as e:
            LOGD(f"DeviceWidget: Failed to initialize filter dialog: {e}")

        # 실시간 로그 표시 관련 속성
        self.max_log_lines = 1000  # 기본 최대 로그 라인 수
        self.log_buffer = deque(maxlen=self.max_log_lines)  # 환형 버퍼
        self.log_text_format = QTextCharFormat()
        self.log_text_format.setFont(QFont("Consolas", 9))

        # 로그 파싱을 위한 정규식 패턴
        import re

        # 패턴 1: HOST 시간 + 전체 형식 (PID 있는 경우)
        self.log_pattern_full = re.compile(
            r"\[(\d{6}-\d{2}:\d{2}:\d{2}\.\d{3})\]\s+"  # HOST 시간
            r"(\w+\s+\d+\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)\s+"  # Target 시간 (마이크로초 선택적)
            r"(\S+)\s+"  # Target hostname
            r"(\S+?)\[(\d+)\]:"  # Process name과 PID
            r"\s*(.*)"  # 실제 로그 메시지
        )

        # 패턴 2: HOST 시간 + Target 시간 + hostname + process (PID 없는 경우)
        self.log_pattern_host_no_pid = re.compile(
            r"\[(\d{6}-\d{2}:\d{2}:\d{2}\.\d{3})\]\s+"  # HOST 시간
            r"(\w+\s+\d+\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)\s+"  # Target 시간 (마이크로초 선택적)
            r"(\S+)\s+"  # Target hostname
            r"(\S+?):"  # Process name (PID 없음)
            r"\s*(.*)"  # 실제 로그 메시지
        )

        # 패턴 3: Target 시간 + hostname + process (HOST 시간 없는 경우)
        self.log_pattern_no_host = re.compile(
            r"(\w+\s+\d+\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)\s+"  # Target 시간 (마이크로초 선택적)
            r"(\S+)\s+"  # Target hostname
            r"(\S+?):"  # Process name (PID 없음)
            r"\s*(.*)"  # 실제 로그 메시지
        )

        # 패턴 4: Target 시간 + hostname + process + kernel 메시지 (HOST 시간 없는 경우)
        self.log_pattern_kernel = re.compile(
            r"(\w+\s+\d+\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)\s+"  # Target 시간 (마이크로초 선택적)
            r"(\S+)\s+"  # Target hostname
            r"(\S+?):"  # Process name
            r"\s*(.*)"  # 실제 로그 메시지
        )

        # HOST 시간만 파싱하기 위한 정규식 패턴
        self.host_time_pattern = re.compile(
            r"\[(\d{6}-\d{2}:\d{2}:\d{2}\.\d{3})\]"  # HOST 시간
        )

        # Target 시간만 파싱하기 위한 정규식 패턴
        self.target_time_pattern = re.compile(
            r"(\w+\s+\d+\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)"  # Target 시간 (마이크로초 선택적)
        )

        # ANSI 컬러 코드 제거를 위한 정규식 (CSI 시퀀스)
        self.ansi_escape_re = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        # ANSI SGR (Select Graphic Rendition) 전용 정규식 - 색상 코드 추출 용도
        self.ansi_sgr_re = re.compile(r"\x1B\[([0-9;]*)m")

        # 실시간 로그 표시 UI 설정
        self._setup_log_viewer_ui()

        # LoggingManager의 new_log_line_signal 연결
        self.logging_manager.new_log_line_signal.connect(self._on_new_log_line)

        # QSLogger 전용 컴포넌트들을 DeviceContext에 등록
        self.device_context.register_app_component(
            "filter_config_dialog", self.filter_config_dialog
        )
        self.device_context.register_app_component("filter_rules", self.filter_rules)
        self.device_context.register_app_component(
            "ui_update_timer", self.ui_update_timer
        )
        self.device_context.register_app_component(
            "pending_ui_updates", self.pending_ui_updates
        )
        self.device_context.register_app_component("log_buffer", self.log_buffer)
        self.device_context.register_app_component("max_log_lines", self.max_log_lines)

        LOGD(f"DeviceWidget: Initialization completed for {self.serial}")

    # -----------------------------
    # Event 기반 연결/해제 처리
    # -----------------------------
    def on_device_connected(self):
        """디바이스 연결 Event 처리 - QSLogger 특화"""
        LOGD(f"DeviceWidget: Device {self.serial} connected event received.")
        # QSLogger 특화 연결 처리가 필요하면 여기에 구현
        # 기본 처리는 BaseDeviceWidget에서 이미 handled됨

    def on_device_disconnected(self):
        """디바이스 연결 해제 Event 처리 - QSLogger 특화"""
        LOGD(f"DeviceWidget: Device {self.serial} disconnected event received.")
        # QSLogger 특화 연결 해제 처리가 필요하면 여기에 구현
        # 기본 처리는 BaseDeviceWidget에서 이미 handled됨

    def _setup_app_specific_ui(self):
        """QSLogger 특화 UI 설정"""
        # Start/Stop 버튼
        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.clicked.connect(lambda: self.on_toggle_clicked(manual=True))

        # 로그 컨트롤 프레임 - 최대 라인 수 및 컨트롤
        self.log_control_frame = QFrame()
        self.log_control_frame.setFrameShape(QFrame.StyledPanel)
        log_control_layout = QHBoxLayout()
        self.log_control_frame.setLayout(log_control_layout)

        # 최대 라인 수 설정
        max_lines_label = QLabel("Max Lines:")
        self.max_lines_spinbox = QSpinBox()
        self.max_lines_spinbox.setRange(100, 10000)
        self.max_lines_spinbox.setValue(self.max_log_lines)
        self.max_lines_spinbox.setSingleStep(100)
        self.max_lines_spinbox.valueChanged.connect(self._on_max_lines_changed)

        # 적용 버튼
        self.apply_max_lines_btn = QPushButton("Apply")
        self.apply_max_lines_btn.clicked.connect(self._on_apply_max_lines_clicked)

        # 로그 지우기 버튼
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self._on_clear_log_clicked)

        # 배치: Max Lines [Apply] [Clear Log] [Start]
        log_control_layout.addWidget(max_lines_label)
        log_control_layout.addWidget(self.max_lines_spinbox)
        log_control_layout.addWidget(self.apply_max_lines_btn)
        log_control_layout.addWidget(self.clear_log_btn)
        log_control_layout.addStretch()
        log_control_layout.addWidget(self.toggle_btn)

        self.app_specific_layout.addWidget(
            self.log_control_frame, 0
        )  # stretch factor = 0 (고정 높이)

        # BaseDeviceWidget의 공통 버튼 활성화 (QSLogger도 이제 Wi-Fi, Dump, Plot, Reboot 버튼 사용)
        if hasattr(self, "control_buttons_frame") and self.control_buttons_frame:
            self.control_buttons_frame.show()

    def _setup_log_viewer_ui(self):
        """실시간 로그 뷰어 UI를 설정합니다."""

        # 로그 디스플레이 컨트롤 프레임
        self.log_control_frame = QFrame()
        self.log_control_frame.setFrameShape(QFrame.StyledPanel)
        log_control_layout = QHBoxLayout()
        self.log_control_frame.setLayout(log_control_layout)

        # Message Filter 버튼
        self.filter_btn = QPushButton("Message Filter")
        self.filter_btn.clicked.connect(self._on_filter_btn_clicked)

        log_control_layout.addStretch()
        log_control_layout.addWidget(self.filter_btn)

        self.app_specific_layout.addWidget(
            self.log_control_frame, 0
        )  # stretch factor = 0 (고정 높이)

        # 좌우 분할을 위한 QSplitter 생성
        self.log_splitter = QSplitter(Qt.Horizontal)

        # 왼쪽: 하이라이트 로그 뷰어 프레임
        self.highlight_log_frame = QFrame()
        self.highlight_log_frame.setFrameShape(QFrame.StyledPanel)
        highlight_log_layout = QVBoxLayout()
        highlight_log_layout.setContentsMargins(0, 0, 0, 0)  # 마진 제거
        self.highlight_log_frame.setLayout(highlight_log_layout)

        # 하이라이트 로그 컨트롤 레이아웃
        highlight_control_layout = QHBoxLayout()
        highlight_control_layout.setContentsMargins(0, 0, 0, 5)  # 아래쪽에만 5px 마진

        # 하이라이트 로그 저장 버튼
        self.save_highlight_btn = QPushButton("저장")
        self.save_highlight_btn.clicked.connect(self._on_save_highlight_clicked)
        self.save_highlight_btn.setMaximumWidth(60)

        highlight_control_layout.addStretch()
        highlight_control_layout.addWidget(self.save_highlight_btn)
        highlight_log_layout.addLayout(highlight_control_layout)

        # 하이라이트 로그 테이블 위젯
        self.highlight_log_table_widget = QTableWidget()
        self.highlight_log_table_widget.setColumnCount(7)
        self.highlight_log_table_widget.setHorizontalHeaderLabels(
            [
                "Host Time",
                "Target Time",
                "Hostname",
                "Process",
                "PID",
                "Message",
                "Original Log",
            ]
        )
        self.highlight_log_table_widget.setFont(QFont("Consolas", 9))
        self.highlight_log_table_widget.setAlternatingRowColors(False)
        self.highlight_log_table_widget.setShowGrid(True)
        self.highlight_log_table_widget.setGridStyle(Qt.DotLine)
        self.highlight_log_table_widget.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.highlight_log_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.highlight_log_table_widget.horizontalHeader().setStretchLastSection(True)
        self.highlight_log_table_widget.verticalHeader().setVisible(False)
        self.highlight_log_table_widget.setWordWrap(False)

        # 행 높이 설정으로 간격 줄이기
        self.highlight_log_table_widget.verticalHeader().setDefaultSectionSize(
            16
        )  # 기본 행 높이를 16px로 설정

        # 컬럼 너비 설정
        highlight_header = self.highlight_log_table_widget.horizontalHeader()
        highlight_header.setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )  # HOST 시간
        highlight_header.setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )  # Target 시간
        highlight_header.setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )  # Hostname
        highlight_header.setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )  # Process
        highlight_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # PID
        highlight_header.setSectionResizeMode(5, QHeaderView.Stretch)  # 로그 메시지
        highlight_header.setSectionResizeMode(
            6, QHeaderView.ResizeToContents
        )  # 원본 로그 (숨김)

        # 원본 로그 컬럼 숨기기
        self.highlight_log_table_widget.hideColumn(6)

        # 테이블 스타일 설정 - 헤더 포함
        self.highlight_log_table_widget.setStyleSheet(
            "            QTableWidget {"
            "                background-color: white;"
            "                gridline-color: #cccccc;"
            "            }"
            "            QTableWidget::item {"
            "                border-bottom: 1px solid #eeeeee;"
            "                padding: 2px;"
            "            }"
            "            QTableWidget::item:selected {"
            "                background-color: #0078d7;"
            "                color: white;"
            "            }"
            "            QHeaderView::section {"
            "                background-color: #f0f0f0;"
            "                color: #333333;"
            "                padding: 3px;"
            "                border: 1px solid #cccccc;"
            "                border-left: none;"
            "                border-top: none;"
            "                font-weight: bold;"
            "            }"
            "            QHeaderView::section:first {"
            "                border-left: 1px solid #cccccc;"
            "            }"
            "            QHeaderView::section:horizontal {"
            "                border-top: 1px solid #cccccc;"
            "            }"
            "        "
        )

        highlight_log_layout.addWidget(self.highlight_log_table_widget)

        # 오른쪽: 전체 로그 뷰어 프레임
        self.full_log_frame = QFrame()
        self.full_log_frame.setFrameShape(QFrame.StyledPanel)
        full_log_layout = QVBoxLayout()
        full_log_layout.setContentsMargins(0, 0, 0, 0)  # 마진 제거
        self.full_log_frame.setLayout(full_log_layout)

        # 전체 로그 컨트롤 레이아웃
        full_control_layout = QHBoxLayout()

        # 전체 로그 저장 버튼
        self.save_full_btn = QPushButton("저장")
        self.save_full_btn.clicked.connect(self._on_save_full_clicked)
        self.save_full_btn.setMaximumWidth(60)

        full_control_layout.addStretch()
        full_control_layout.addWidget(self.save_full_btn)
        full_log_layout.addLayout(full_control_layout)

        # 전체 로그 테이블 위젯
        self.full_log_table_widget = QTableWidget()
        self.full_log_table_widget.setColumnCount(7)
        self.full_log_table_widget.setHorizontalHeaderLabels(
            [
                "Host Time",
                "Target Time",
                "Hostname",
                "Process",
                "PID",
                "Message",
                "Original Log",
            ]
        )
        self.full_log_table_widget.setFont(QFont("Consolas", 9))
        self.full_log_table_widget.setAlternatingRowColors(False)
        self.full_log_table_widget.setShowGrid(True)
        self.full_log_table_widget.setGridStyle(Qt.DotLine)
        self.full_log_table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.full_log_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.full_log_table_widget.horizontalHeader().setStretchLastSection(True)
        self.full_log_table_widget.verticalHeader().setVisible(False)
        self.full_log_table_widget.setWordWrap(False)

        # 행 높이 설정으로 간격 줄이기
        self.full_log_table_widget.verticalHeader().setDefaultSectionSize(
            16
        )  # 기본 행 높이를 16px로 설정

        # 컬럼 너비 설정
        full_header = self.full_log_table_widget.horizontalHeader()
        full_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # HOST 시간
        full_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Target 시간
        full_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Hostname
        full_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Process
        full_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # PID
        full_header.setSectionResizeMode(5, QHeaderView.Stretch)  # 로그 메시지
        full_header.setSectionResizeMode(
            6, QHeaderView.ResizeToContents
        )  # 원본 로그 (숨김)

        # 원본 로그 컬럼 숨기기
        self.full_log_table_widget.hideColumn(6)

        # 테이블 스타일 설정 - 헤더 포함
        self.full_log_table_widget.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #cccccc;
            }
            QTableWidget::item {
                border-bottom: 1px solid #eeeeee;
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #333333;
                padding: 3px;
                border: 1px solid #cccccc;
                border-left: none;
                border-top: none;
                font-weight: bold;
            }
            QHeaderView::section:first {
                border-left: 1px solid #cccccc;
            }
            QHeaderView::section:horizontal {
                border-top: 1px solid #cccccc;
            }
        """)

        full_log_layout.addWidget(self.full_log_table_widget)

        # QSplitter에 위젯 추가
        self.log_splitter.addWidget(self.highlight_log_frame)
        self.log_splitter.addWidget(self.full_log_frame)

        # 초기 분할 비율 설정 (왼쪽 40%, 오른쪽 60%)
        self.log_splitter.setSizes([400, 600])

        # 분할 바 너비 설정 (더 얇게)
        self.log_splitter.setHandleWidth(3)

        # 로그 뷰어 컨테이너 프레임
        self.log_viewer_frame = QFrame()
        self.log_viewer_frame.setFrameShape(QFrame.StyledPanel)

        # QSplitter를 컨테이너 프레임에 직접 추가
        log_viewer_layout = QVBoxLayout()
        log_viewer_layout.setContentsMargins(0, 0, 0, 0)  # 마진 제거
        log_viewer_layout.addWidget(self.log_splitter)
        self.log_viewer_frame.setLayout(log_viewer_layout)

        self.app_specific_layout.addWidget(
            self.log_viewer_frame, 1
        )  # stretch factor = 1 (대부분의 공간 차지)

    def __del__(self):
        """소멸자 - 안전한 정리"""
        try:
            # 타이머 중지
            if hasattr(self, "timer"):
                self.timer.stop()
            if hasattr(self, "ui_update_timer"):
                self.ui_update_timer.stop()

        except Exception:
            pass  # 소멸자에서는 예외 무시

    def update_ui_with_result(self, handler, result):
        """Command 실행 결과를 UI 업데이트 시그널로 전송"""
        LOGD(
            f"DeviceWidget: update_ui_with_result called with handler: {handler.__class__.__name__}, result: {result}"
        )

        if result is None:
            LOGD(f"DeviceWidget: Result is None, skipping UI update")
            return

        # UI 업데이트를 큐에 추가
        self.pending_ui_updates.append((handler, result))

        # 메인 스레드에서 UI 업데이트를 위한 시그널 발신
        self.update_ui_signal.emit(handler, result)

    def _on_update_ui_received(self, handler, result):
        """메인 스레드에서 UI 업데이트 시그널 수신 처리"""
        # 이미 타이머가 실행 중이지 않으면 시작
        if not self.ui_update_timer.isActive():
            self.ui_update_timer.start(50)

    def _batch_update_ui(self):
        """배치 UI 업데이트 실행"""
        LOGD(
            f"DeviceWidget: Starting batch UI update with {len(self.pending_ui_updates)} updates"
        )

        # 큐에 있는 모든 업데이트 처리
        updates = self.pending_ui_updates.copy()
        self.pending_ui_updates.clear()

        for handler, result in updates:
            # 로그 디스플레이 업데이트 핸들러 호출
            try:
                # 핸들러 이름으로 비교하여 올바른 메서드인지 확인
                if handler.__name__ == "_update_log_display":
                    handler(self, result)
                    LOGD(
                        f"DeviceWidget: Successfully called _update_log_display handler"
                    )
                else:
                    LOGD(f"DeviceWidget: Unknown handler: {handler.__name__}")
            except Exception as e:
                LOGD(f"DeviceWidget: Error calling handler {handler}: {e}")

        LOGD(f"DeviceWidget: Batch UI update completed")

    def _on_session_started(self, manual: bool):
        """세션 시작 시 QSLogger 전용 UI 업데이트"""
        try:
            if hasattr(self, "toggle_btn") and self.toggle_btn:
                self.toggle_btn.setText("Stop")
                self.toggle_btn.setEnabled(True)
        except Exception:
            pass

    def _on_session_stopped(self):
        """세션 정지 시 QSLogger 전용 정리"""
        try:
            if hasattr(self, "toggle_btn") and self.toggle_btn:
                self.toggle_btn.setText("Start")
        except Exception:
            pass
        # UI 업데이트 타이머/큐 정리
        try:
            if hasattr(self, "ui_update_timer") and self.ui_update_timer.isActive():
                self.ui_update_timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "pending_ui_updates"):
                self.pending_ui_updates.clear()
        except Exception:
            pass

    # -----------------------------
    # 버튼 이벤트
    # -----------------------------
    # Reboot 기능은 BaseDeviceWidget에서 구현되었으므로 제거

    def on_toggle_clicked(self, manual: bool = True):
        """Start/Stop 버튼 클릭 처리
        Args:
            manual (bool): True if triggered by user action; False for automatic (e.g., reconnect)
        """
        if self.session_state in [SessionState.STOPPED, SessionState.PAUSED]:
            LOGD(f"DeviceWidget: Start button clicked. manual={manual}")
            self._start_user_session(manual=manual)
        else:
            LOGD("DeviceWidget: Stop button clicked.")
            self._stop_user_session()

    def setEnabled(self, enabled: bool):
        """
        Override setEnabled to handle child widgets properly; avoid disabling whole widget on disconnect.

        Args:
            enabled: Desired enabled state
        """
        LOGD(
            f"DeviceWidget: setEnabled called with {enabled}. Current isEnabled(): {self.isEnabled()}"
        )

        # Custom logic: selectively enable/disable child controls
        self._handle_widget_enabling_disabling(enabled)

        # Do not disable the entire widget when device disconnects; keep UI responsive
        if enabled:
            super().setEnabled(True)
            LOGD("DeviceWidget: Applied super().setEnabled(True)")
        else:
            # Keep top-level widget enabled to allow viewing logs and using controls
            LOGD(
                "DeviceWidget: Skipped disabling top-level widget; managed child controls instead"
            )

    def _handle_widget_enabling_disabling(self, enabled: bool):
        """Helper method to handle enabling/disabling of child widgets."""
        if enabled:
            # 기기가 재연결될 때 모든 인터랙티브 위젯 활성화
            if self.title_frame:
                self.title_frame.setEnabled(True)

                if hasattr(self, "toggle_btn") and self.toggle_btn:
                    self.toggle_btn.setEnabled(True)

                # 타이틀 프레임의 다른 위젯들도 활성화
                widget_types = (QPushButton, QLineEdit, QLabel)
                widgets_to_enable = []
                for w_type in widget_types:
                    widgets_to_enable.extend(self.title_frame.findChildren(w_type))

                for widget in widgets_to_enable:
                    if widget != self.toggle_btn:  # toggle_btn은 아래에서 별도 처리
                        widget.setEnabled(True)

            # Reboot button 활성화
            if hasattr(self, "reboot_btn") and self.reboot_btn:
                self.reboot_btn.setEnabled(True)

            # device_control_frame 활성화
            if hasattr(self, "device_control_frame") and self.device_control_frame:
                self.device_control_frame.setEnabled(True)

            # log_control_frame 활성화
            if hasattr(self, "log_control_frame") and self.log_control_frame:
                self.log_control_frame.setEnabled(True)

            # log_viewer_frame 활성화
            if hasattr(self, "log_viewer_frame") and self.log_viewer_frame:
                self.log_viewer_frame.setEnabled(True)

            # 저장된 상태 클리어
            self._widget_enabled_states.clear()
        else:
            # Save states map fresh
            self._widget_enabled_states.clear()

            # Preserve whether we were running to auto-restart later
            was_running = self.is_running
            self.was_running_before_disconnect = bool(was_running)

            # Disable only Reboot button; keep the rest of the UI usable

            if hasattr(self, "reboot_btn") and self.reboot_btn:
                self._widget_enabled_states[self.reboot_btn] = (
                    self.reboot_btn.isEnabled()
                )
                self.reboot_btn.setEnabled(False)

            # Preserve logging state flag (for append-on-reconnect)
            if self.logging_manager.is_currently_logging():
                self.logging_manager.set_was_logging_before_disconnect(True)
                LOGD(
                    f"DeviceWidget: Preserved logging state before disable for device {self.serial}"
                )

            # If monitoring was running, stop it now (without toggling UI button handler)
            if was_running:
                self.is_running = False
                self.logging_manager.stop_logging()
                LOGD("DeviceWidget: Stopped logging directly due to device disable")

    # -----------------------------
    # DeviceLoggingManager 시그널 핸들러
    # -----------------------------
    def _on_logging_started_ui_update(self, log_file_name: str):
        """DeviceLoggingManager의 logging_started_signal을 처리하는 UI 업데이트 핸들러"""
        LOGD(f"DeviceWidget: UI update for logging started. File: {log_file_name}")
        # 추가적인 UI 업데이트가 필요하다면 여기에 구현
        pass

    def _on_logging_stopped_ui_update(self):
        """DeviceLoggingManager의 logging_stopped_signal을 처리하는 UI 업데이트 핸들러"""
        LOGD(f"DeviceWidget: UI update for logging stopped.")
        # 추가적인 UI 업데이트가 필요하다면 여기에 구현
        pass

    def _on_logging_error_ui_update(self, error_msg: str):
        """DeviceLoggingManager의 logging_error_signal을 처리하는 UI 업데이트 핸들러"""
        LOGD(f"DeviceWidget: UI update for logging error: {error_msg}")
        # 사용자에게 에러 알림
        QMessageBox.warning(
            self, "로깅 에러", f"로깅 중 에러가 발생했습니다:\n{error_msg}"
        )

    # -----------------------------
    # 실시간 로그 표시 관련 메서드
    # -----------------------------
    def _on_new_log_line(self, log_line: str):
        """새로운 로그 라인을 처리하고 UI에 표시합니다.
        LoggingCommand에서 한 번에 여러 줄을 전달할 수 있으므로 반드시 라인 단위로 분리해 처리합니다.
        """
        # Debug log to check if log lines are being received by DeviceWidget
        LOGD(f"DeviceWidget: Received new log line: {log_line[:100]}...")

        if not log_line:
            return

        # 여러 줄이 한 번에 들어오는 경우가 있어 라인 단위로 분리 처리
        for line in log_line.splitlines():
            # 공백 라인은 표시하지 않음
            if not line or not line.strip():
                continue

            # 각 라인을 버퍼에 추가
            self.log_buffer.append(line)

            # UI 업데이트 (메인 스레드에서 안전하게 실행)
            self.update_ui_with_result(self._update_log_display, line)

    def _update_log_display(self, handler, log_line: str):
        """로그 디스플레이를 업데이트합니다."""
        # Debug log to check if UI update is being called
        LOGD(f"DeviceWidget: Updating log display with: {log_line[:50]}...")

        log_line_stripped = log_line.strip()

        # 전체 로그 테이블에 새 행 추가
        full_row_count = self.full_log_table_widget.rowCount()
        self.full_log_table_widget.insertRow(full_row_count)

        # 파싱 시도 - 여러 패턴을 순차적으로 시도
        parsed_data = None

        # 패턴 1: HOST 시간 + 전체 형식 (PID 있는 경우) 파싱 시도
        match = self.log_pattern_full.match(log_line_stripped)
        if match:
            parsed_data = {
                "host_time": match.group(1),
                "target_time": match.group(2),
                "hostname": match.group(3),
                "process_name": match.group(4),
                "pid": match.group(5),
                "log_message": match.group(6),
                "parse_type": "full",
            }
        else:
            # 패턴 2: HOST 시간 + Target 시간 + hostname + process (PID 없는 경우) 파싱 시도
            match = self.log_pattern_host_no_pid.match(log_line_stripped)
            if match:
                parsed_data = {
                    "host_time": match.group(1),
                    "target_time": match.group(2),
                    "hostname": match.group(3),
                    "process_name": match.group(4),
                    "pid": "",
                    "log_message": match.group(5),
                    "parse_type": "host_no_pid",
                }
            else:
                # 패턴 3: HOST 시간 없이 Target 시간부터 시작하는 형식 파싱 시도
                match = self.log_pattern_no_host.match(log_line_stripped)
                if match:
                    # HOST 시간이 없지만 Target 시간은 있는 경우
                    parsed_data = {
                        "host_time": "",
                        "target_time": match.group(1),
                        "hostname": match.group(2),
                        "process_name": match.group(3),
                        "pid": "",
                        "log_message": match.group(4),
                        "parse_type": "no_host",
                    }
                else:
                    # 패턴 4: 커널 로그 등 다른 형식 파싱 시도
                    match = self.log_pattern_kernel.match(log_line_stripped)
                    if match:
                        parsed_data = {
                            "host_time": "",
                            "target_time": match.group(1),
                            "hostname": match.group(2),
                            "process_name": match.group(3),
                            "pid": "",
                            "log_message": match.group(4),
                            "parse_type": "kernel",
                        }

        # 하이라이트 여부 확인
        is_highlighted = False
        highlight_bg_color = None
        highlight_text_color = None

        if parsed_data:
            # 파싱 성공 - 전체 로그 테이블에 데이터 표시
            self.full_log_table_widget.setItem(
                full_row_count, 0, self._create_table_item(parsed_data["host_time"])
            )
            self.full_log_table_widget.setItem(
                full_row_count, 1, self._create_table_item(parsed_data["target_time"])
            )
            self.full_log_table_widget.setItem(
                full_row_count, 2, self._create_table_item(parsed_data["hostname"])
            )
            self.full_log_table_widget.setItem(
                full_row_count, 3, self._create_table_item(parsed_data["process_name"])
            )
            self.full_log_table_widget.setItem(
                full_row_count, 4, self._create_table_item(parsed_data["pid"])
            )
            # ANSI 컬러 파싱 및 메시지 텍스트 정리
            clean_msg, ansi_color = self._parse_ansi_color_and_strip(
                parsed_data["log_message"]
            )
            self.full_log_table_widget.setItem(
                full_row_count, 5, self._create_table_item(clean_msg, True)
            )
            self.full_log_table_widget.setItem(
                full_row_count, 6, self._create_table_item(log_line)
            )  # 원본 로그 (숨김)

            # 전체 로그 테이블에 행 색상 설정
            if parsed_data["parse_type"] == "full":
                self._set_full_log_row_color(
                    full_row_count,
                    parsed_data["log_message"],
                    process_name=parsed_data["process_name"],
                    pid_str=parsed_data["pid"],
                )
            elif parsed_data["parse_type"] == "host_no_pid":
                self._set_full_log_row_color(
                    full_row_count,
                    parsed_data["log_message"],
                    process_name=parsed_data["process_name"],
                    pid_str=parsed_data["pid"],
                )
            elif parsed_data["parse_type"] in ["no_host", "kernel"]:
                self._set_full_log_row_color(
                    full_row_count,
                    parsed_data["log_message"],
                    is_partial_parse=True,
                    process_name=parsed_data["process_name"],
                    pid_str=parsed_data["pid"],
                )

            # 행 색상 적용 후에도 ANSI에서 유도한 메시지 텍스트 색상을 다시 적용 (bleed 방지)
            if "ansi_color" in locals() and ansi_color:
                msg_item = self.full_log_table_widget.item(full_row_count, 5)
                if msg_item:
                    msg_item.setForeground(ansi_color)

            # 필터 규칙 적용 여부 확인
            if parsed_data["parse_type"] not in ["no_host", "kernel"]:
                highlight_bg_color, highlight_text_color = self._apply_filter_rules(
                    parsed_data["process_name"],
                    parsed_data["pid"],
                    parsed_data["log_message"],
                )
                # 필터 규칙이 적용된 경우
                if highlight_bg_color != QColor(
                    255, 255, 255
                ) or highlight_text_color != QColor(0, 0, 0):
                    is_highlighted = True
                    # 하이라이트 로그 테이블에도 추가
                    self._add_to_highlight_table(
                        parsed_data, log_line, highlight_bg_color, highlight_text_color
                    )
        else:
            # 모든 파싱 실패 - 최소한의 정보만 추출 시도
            host_time_match = self.host_time_pattern.search(log_line_stripped)
            target_time_match = self.target_time_pattern.search(log_line_stripped)

            if host_time_match:
                # HOST 시간만 파싱 성공
                host_time = host_time_match.group(1)
                remaining_log = log_line[host_time_match.end() :].strip()

                self.full_log_table_widget.setItem(
                    full_row_count, 0, self._create_table_item(host_time)
                )
                self.full_log_table_widget.setItem(
                    full_row_count, 1, self._create_table_item("")
                )  # Target 시간 (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 2, self._create_table_item("")
                )  # Hostname (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 3, self._create_table_item("")
                )  # Process (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 4, self._create_table_item("")
                )  # PID (비움)
                # ANSI 컬러 파싱 및 메시지 텍스트 정리
                clean_msg, ansi_color_ht = self._parse_ansi_color_and_strip(
                    remaining_log
                )
                self.full_log_table_widget.setItem(
                    full_row_count, 5, self._create_table_item(clean_msg, True)
                )  # 나머지 로그
                self.full_log_table_widget.setItem(
                    full_row_count, 6, self._create_table_item(log_line)
                )  # 원본 로그 (숨김)

                # 부분 파싱 행은 연한 회색으로 표시
                self._set_full_log_row_color(
                    full_row_count, remaining_log, is_partial_parse=True
                )
                # 행 색상 적용 후 ANSI 색상 재적용
                if ansi_color_ht:
                    msg_item = self.full_log_table_widget.item(full_row_count, 5)
                    if msg_item:
                        msg_item.setForeground(ansi_color_ht)
            elif target_time_match:
                # Target 시간만 파싱 성공
                target_time = target_time_match.group(1)
                remaining_log = log_line[target_time_match.end() :].strip()

                self.full_log_table_widget.setItem(
                    full_row_count, 0, self._create_table_item("")
                )  # HOST 시간 (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 1, self._create_table_item(target_time)
                )
                self.full_log_table_widget.setItem(
                    full_row_count, 2, self._create_table_item("")
                )  # Hostname (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 3, self._create_table_item("")
                )  # Process (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 4, self._create_table_item("")
                )  # PID (비움)
                # ANSI 컬러 파싱 및 메시지 텍스트 정리
                clean_msg2, ansi_color_tt = self._parse_ansi_color_and_strip(
                    remaining_log
                )
                self.full_log_table_widget.setItem(
                    full_row_count, 5, self._create_table_item(clean_msg2, True)
                )  # 나머지 로그
                self.full_log_table_widget.setItem(
                    full_row_count, 6, self._create_table_item(log_line)
                )  # 원본 로그 (숨김)

                # 부분 파싱 행은 연한 회색으로 표시
                self._set_full_log_row_color(
                    full_row_count, remaining_log, is_partial_parse=True
                )
                # 행 색상 적용 후 ANSI 색상 재적용
                if ansi_color_tt:
                    msg_item = self.full_log_table_widget.item(full_row_count, 5)
                    if msg_item:
                        msg_item.setForeground(ansi_color_tt)
            else:
                # 완전한 파싱 실패
                self.full_log_table_widget.setItem(
                    full_row_count, 0, self._create_table_item("")
                )  # HOST 시간 (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 1, self._create_table_item("")
                )  # Target 시간 (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 2, self._create_table_item("")
                )  # Hostname (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 3, self._create_table_item("")
                )  # Process (비움)
                self.full_log_table_widget.setItem(
                    full_row_count, 4, self._create_table_item("")
                )  # PID (비움)
                # ANSI 컬러 파싱 및 메시지 텍스트 정리 (원본 전체 라인 기준)
                clean_msg3, ansi_color_pf = self._parse_ansi_color_and_strip(log_line)
                self.full_log_table_widget.setItem(
                    full_row_count, 5, self._create_table_item(clean_msg3, True)
                )  # 전체 로그
                self.full_log_table_widget.setItem(
                    full_row_count, 6, self._create_table_item(log_line)
                )  # 원본 로그 (숨김)

                # 완전한 파싱 실패 행은 진한 회색으로 표시
                self._set_full_log_row_color(
                    full_row_count, log_line, is_parse_failed=True
                )
                # 행 색상 적용 후 ANSI 색상 재적용
                if ansi_color_pf:
                    msg_item = self.full_log_table_widget.item(full_row_count, 5)
                    if msg_item:
                        msg_item.setForeground(ansi_color_pf)

        # 자동 스크롤
        self._auto_scroll_to_bottom()

        # 최대 라인 수 제한
        self._enforce_max_lines_limit()

    def _create_table_item(self, text, is_message=False):
        """테이블 아이템 생성"""
        item = QTableWidgetItem(text)

        if is_message:
            # 메시지 컬럼은 툴팁으로 전체 내용 표시
            item.setToolTip(text)

        # 텍스트 색상을 검은색으로 설정 (하얀 배경에서 보이도록)
        item.setForeground(QColor(0, 0, 0))

        return item

    def _strip_ansi(self, text: str) -> str:
        """ANSI 컬러 코드 제거"""
        if not text:
            return text
        try:
            return self.ansi_escape_re.sub("", text)
        except Exception:
            return text

    def _parse_ansi_color_and_strip(self, text: str):
        """텍스트 내 ANSI SGR 코드를 파싱하여 최종 전경색을 추출하고, 코드는 제거한 텍스트를 반환합니다.
        Returns: (clean_text: str, fg_color: Optional[QColor])
        """
        if not text:
            return text, None
        try:
            final_color_code = (
                None  # 마지막으로 적용된 전경색 코드 (30-37,90-97) 또는 None=기본색
            )
            params_seen = []
            for m in self.ansi_sgr_re.finditer(text):
                params = m.group(1)
                # 빈 파라미터나 0은 reset으로 간주
                if params == "" or params == "0":
                    final_color_code = None
                    params_seen = []
                    continue
                # 여러 파라미터가 ; 로 구분됨
                try:
                    parts = [int(p) for p in params.split(";") if p != ""]
                except ValueError:
                    continue
                params_seen = parts
                # 39는 기본색으로 리셋
                if 39 in parts:
                    final_color_code = None
                # 전경색 코드 탐색 (마지막으로 등장한 것을 채택)
                for p in parts:
                    if (30 <= p <= 37) or (90 <= p <= 97):
                        final_color_code = p
            # 매핑
            color = None
            if final_color_code is not None:
                base_colors = {
                    30: QColor(0, 0, 0),  # Black
                    31: QColor(220, 20, 60),  # Crimson-ish red for readability
                    32: QColor(0, 128, 0),  # Green
                    33: QColor(184, 134, 11),  # DarkGoldenrod (better on white)
                    34: QColor(25, 25, 112),  # MidnightBlue
                    35: QColor(139, 0, 139),  # DarkMagenta
                    36: QColor(0, 139, 139),  # DarkCyan
                    37: QColor(105, 105, 105),  # DimGray (white text can be too strong)
                    90: QColor(105, 105, 105),  # Bright Black (Gray)
                    91: QColor(255, 69, 0),  # OrangeRed
                    92: QColor(50, 205, 50),  # LimeGreen
                    93: QColor(255, 215, 0),  # Gold
                    94: QColor(65, 105, 225),  # RoyalBlue
                    95: QColor(186, 85, 211),  # MediumOrchid
                    96: QColor(72, 209, 204),  # MediumTurquoise
                    97: QColor(
                        245, 245, 245
                    ),  # Bright White (very light gray for contrast)
                }
                color = base_colors.get(final_color_code)
            clean_text = self.ansi_escape_re.sub("", text)
            return clean_text, color
        except Exception:
            return self._strip_ansi(text), None

    def _set_full_log_row_color(
        self,
        row,
        log_message,
        is_parse_failed=False,
        is_partial_parse=False,
        process_name: str = "",
        pid_str: str = "",
    ):
        """전체 로그 테이블의 로그 레벨에 따른 행 색상 설정"""
        # 기본 색상 설정
        if is_parse_failed:
            # 완전한 파싱 실패 - 진한 회색
            color = QColor(220, 220, 220)
            text_color = QColor(0, 0, 0)  # 검은색 텍스트
        elif is_partial_parse:
            # 부분 파싱 (HOST 시간만) - 연한 회색
            color = QColor(245, 245, 220)  # 연한 노란빛 회색
            text_color = QColor(0, 0, 0)  # 검은색 텍스트
        elif "ERROR" in log_message.upper() or "FATAL" in log_message.upper():
            # 에러 - 빨간색
            color = QColor(255, 200, 200)
            text_color = QColor(139, 0, 0)  # 진한 빨간색 텍스트
        elif "WARN" in log_message.upper() or "WARNING" in log_message.upper():
            # 경고 - 주황색
            color = QColor(255, 230, 200)
            text_color = QColor(255, 140, 0)  # 진한 주황색 텍스트
        elif "INFO" in log_message.upper():
            # 정보 - 흰색
            color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)  # 검은색 텍스트
        elif "DEBUG" in log_message.upper():
            # 디버그 - 밝은 회색
            color = QColor(245, 245, 245)
            text_color = QColor(0, 0, 0)  # 검은색 텍스트
        else:
            # 기본 - 흰색
            color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)  # 검은색 텍스트

        # 필터 규칙 적용 (파싱 실패가 아닌 경우에만)
        if not is_parse_failed and not is_partial_parse:
            highlight_bg_color, highlight_text_color = self._apply_filter_rules(
                process_name, pid_str, log_message
            )
            # 필터 규칙이 적용된 경우 해당 색상 사용
            if highlight_bg_color != QColor(
                255, 255, 255
            ) or highlight_text_color != QColor(0, 0, 0):
                color = highlight_bg_color
                text_color = highlight_text_color

        for col in range(self.full_log_table_widget.columnCount()):
            item = self.full_log_table_widget.item(row, col)
            if item:
                item.setBackground(color)
                item.setForeground(text_color)

    def _add_to_highlight_table(self, parsed_data, original_log, bg_color, text_color):
        """하이라이트된 로그를 하이라이트 테이블에 추가 (ANSI 컬러 코드 제거하여 표시)"""
        highlight_row_count = self.highlight_log_table_widget.rowCount()
        self.highlight_log_table_widget.insertRow(highlight_row_count)

        # ANSI 컬러 코드 제거된 텍스트 준비
        host_time = self._strip_ansi(parsed_data.get("host_time", ""))
        target_time = self._strip_ansi(parsed_data.get("target_time", ""))
        hostname = self._strip_ansi(parsed_data.get("hostname", ""))
        process_name = self._strip_ansi(parsed_data.get("process_name", ""))
        pid = self._strip_ansi(parsed_data.get("pid", ""))
        message = self._strip_ansi(parsed_data.get("log_message", ""))

        # 파싱된 데이터를 하이라이트 테이블에 추가 (표시용 텍스트는 ANSI 제거)
        self.highlight_log_table_widget.setItem(
            highlight_row_count, 0, self._create_table_item(host_time)
        )
        self.highlight_log_table_widget.setItem(
            highlight_row_count, 1, self._create_table_item(target_time)
        )
        self.highlight_log_table_widget.setItem(
            highlight_row_count, 2, self._create_table_item(hostname)
        )
        self.highlight_log_table_widget.setItem(
            highlight_row_count, 3, self._create_table_item(process_name)
        )
        self.highlight_log_table_widget.setItem(
            highlight_row_count, 4, self._create_table_item(pid)
        )
        self.highlight_log_table_widget.setItem(
            highlight_row_count, 5, self._create_table_item(message, True)
        )
        self.highlight_log_table_widget.setItem(
            highlight_row_count, 6, self._create_table_item(original_log)
        )  # 원본 로그 (숨김)

        # 지정된 색상으로 행 설정
        for col in range(self.highlight_log_table_widget.columnCount()):
            item = self.highlight_log_table_widget.item(highlight_row_count, col)
            if item:
                item.setBackground(bg_color)
                item.setForeground(text_color)

        # 하이라이트 테이블도 자동 스크롤
        self._auto_scroll_highlight_to_bottom()

    def _auto_scroll_to_bottom(self):
        """전체 로그 테이블 자동 스크롤 to bottom"""
        scrollbar = self.full_log_table_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _auto_scroll_highlight_to_bottom(self):
        """하이라이트 로그 테이블 자동 스크롤 to bottom"""
        scrollbar = self.highlight_log_table_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _enforce_max_lines_limit(self):
        """최대 라인 수 제한 - 두 테이블 모두 적용"""
        # 전체 로그 테이블 제한
        full_row_count = self.full_log_table_widget.rowCount()
        if full_row_count > self.max_log_lines:
            rows_to_remove = full_row_count - self.max_log_lines
            for _ in range(rows_to_remove):
                self.full_log_table_widget.removeRow(0)

        # 하이라이트 로그 테이블 제한 (최대 라인 수의 절반으로 설정)
        highlight_max_lines = self.max_log_lines // 2
        highlight_row_count = self.highlight_log_table_widget.rowCount()
        if highlight_row_count > highlight_max_lines:
            rows_to_remove = highlight_row_count - highlight_max_lines
            for _ in range(rows_to_remove):
                self.highlight_log_table_widget.removeRow(0)

    def _on_max_lines_changed(self, value: int):
        """최대 라인 수 스피너 값 변경 시 처리"""
        # 실제 적용은 Apply 버튼 클릭 시 수행
        pass

    def _on_apply_max_lines_clicked(self):
        """최대 라인 수 적용 버튼 클릭 시 처리"""
        new_max_lines = self.max_lines_spinbox.value()
        if new_max_lines != self.max_log_lines:
            self.max_log_lines = new_max_lines

            # 새로운 버퍼 생성 및 기존 데이터 복사
            new_buffer = deque(maxlen=self.max_log_lines)
            new_buffer.extend(self.log_buffer)
            self.log_buffer = new_buffer

            # UI 업데이트
            self._refresh_log_display()

            LOGD(f"DeviceWidget: Max log lines updated to {self.max_log_lines}")

    def _on_clear_log_clicked(self):
        """로그 지우기 버튼 클릭 시 처리"""
        self.log_buffer.clear()
        self.full_log_table_widget.setRowCount(0)
        self.highlight_log_table_widget.setRowCount(0)
        LOGD(f"DeviceWidget: Log display cleared")

    def _on_filter_btn_clicked(self):
        """Message Filter 버튼 클릭 시 처리"""
        # 버튼 클릭 시점에 항상 최신 규칙을 설정 파일에서 재로딩하여 동기화
        try:
            saved_rules = self.settings_manager.get_filter_rules() or []
            loaded_rules = []
            for r in saved_rules:
                if isinstance(r, dict):
                    loaded_rules.append(HighlightRule.from_dict(r))
                elif isinstance(r, HighlightRule):
                    loaded_rules.append(r)
                else:
                    # 알 수 없는 형식은 무시
                    continue
            # 메모리 상태 갱신
            self.filter_rules = loaded_rules
        except Exception as e:
            LOGD(f"DeviceWidget: Failed to reload filter rules on button click: {e}")

        if not self.filter_config_dialog:
            self.filter_config_dialog = HighlightConfigDialog(self, self.filter_rules)
            self.filter_config_dialog.rules_changed.connect(
                self._on_filter_rules_changed
            )
        else:
            # 기존 다이얼로그 테이블도 최신 규칙으로 갱신
            try:
                if hasattr(self.filter_config_dialog, "set_rules"):
                    self.filter_config_dialog.set_rules(self.filter_rules)
            except Exception as e:
                LOGD(f"DeviceWidget: Failed to update dialog rules: {e}")

        # 다이얼로그 표시 (이미 열려있더라도 포커스 주기)
        try:
            self.filter_config_dialog.show()
            self.filter_config_dialog.raise_()
            self.filter_config_dialog.activateWindow()
        except Exception:
            pass

    def _on_filter_rules_changed(self, new_rules):
        """필터 규칙 변경 시 처리"""
        self.filter_rules = new_rules
        # 저장소에 즉시 영속화
        try:
            serialized = [rule.to_dict() for rule in self.filter_rules]
            self.settings_manager.set_filter_rules(serialized)
            LOGD(f"DeviceWidget: Persisted {len(self.filter_rules)} filter rules")
        except Exception as e:
            LOGD(f"DeviceWidget: Failed to persist filter rules: {e}")
        # 현재 표시된 로그를 새로고침하여 새 규칙 적용
        self._refresh_log_display()
        LOGD(
            f"DeviceWidget: Filter rules updated, {len(self.filter_rules)} rules loaded"
        )

    def _apply_filter_rules(
        self, process_name: str, pid_str: str, log_message: str
    ) -> tuple:
        """필터 규칙을 적용하여 색상을 반환"""
        default_bg_color = QColor(255, 255, 255)  # 기본 흰색 배경
        default_text_color = QColor(0, 0, 0)  # 기본 검은색 텍스트

        # 규칙을 순서대로 적용 (먼저 일치하는 규칙이 우선)
        for rule in self.filter_rules:
            if rule.matches(process_name, pid_str, log_message):
                return rule.bg_color, rule.text_color

        return default_bg_color, default_text_color

    def _on_save_highlight_clicked(self):
        """하이라이트 로그 저장 버튼 클릭 시 처리"""
        if self.highlight_log_table_widget.rowCount() == 0:
            QMessageBox.information(self, "저장", "저장할 하이라이트 로그가 없습니다.")
            return

        # 파일 저장 다이얼로그 열기
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "하이라이트 로그 저장",
            f"highlight_log_{self.serial}.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    # 하이라이트 테이블의 모든 행에 대해 원본 로그(6번 컬럼)를 저장
                    for row in range(self.highlight_log_table_widget.rowCount()):
                        original_log_item = self.highlight_log_table_widget.item(row, 6)
                        if original_log_item:
                            original_log = original_log_item.text()
                            f.write(original_log + "\n")

                QMessageBox.information(
                    self,
                    "저장 완료",
                    f"하이라이트 로그가 {file_path}에 저장되었습니다.",
                )
                LOGD(f"DeviceWidget: Highlight logs saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self, "저장 실패", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}"
                )
                LOGD(f"DeviceWidget: Error saving highlight logs: {str(e)}")

    def _on_save_full_clicked(self):
        """전체 로그 저장 버튼 클릭 시 처리"""
        if self.full_log_table_widget.rowCount() == 0:
            QMessageBox.information(self, "저장", "저장할 전체 로그가 없습니다.")
            return

        # 파일 저장 다이얼로그 열기
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "전체 로그 저장",
            f"full_log_{self.serial}.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    # 전체 로그 테이블의 모든 행에 대해 원본 로그(6번 컬럼)를 저장
                    for row in range(self.full_log_table_widget.rowCount()):
                        original_log_item = self.full_log_table_widget.item(row, 6)
                        if original_log_item:
                            original_log = original_log_item.text()
                            f.write(original_log + "\n")

                QMessageBox.information(
                    self, "저장 완료", f"전체 로그가 {file_path}에 저장되었습니다."
                )
                LOGD(f"DeviceWidget: Full logs saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self, "저장 실패", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}"
                )
                LOGD(f"DeviceWidget: Error saving full logs: {str(e)}")

    def _refresh_log_display(self):
        """로그 디스플레이를 새로고침합니다."""
        self.full_log_table_widget.setRowCount(0)
        self.highlight_log_table_widget.setRowCount(0)

        # 버퍼의 모든 로그 라인을 다시 표시
        for log_line in self.log_buffer:
            self._update_log_display(self, log_line)

    # ADB 상태 스타일 설정은 BaseDeviceWidget에서 구현되었으므로 제거
