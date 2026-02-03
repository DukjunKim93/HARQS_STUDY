#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Filter Configuration Dialog
"""

import re
from typing import List, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QColorDialog,
    QLineEdit,
    QCheckBox,
    QMessageBox,
    QFrame,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
)


class HighlightRule:
    """하이라이트 규칙을 저장하는 클래스"""

    def __init__(
        self,
        name: str = "",
        process: str = "",
        pid: str = "",
        message: str = "",
        use_regex: bool = False,
        text_color: QColor = None,
        bg_color: QColor = None,
        enabled: bool = True,
    ):
        self.name = name
        self.process = process
        self.pid = pid
        self.message = message
        self.use_regex = use_regex
        self.text_color = text_color or QColor(0, 0, 0)  # 기본 검은색
        self.bg_color = bg_color or QColor(255, 255, 0)  # 기본 노란색 배경
        self.enabled = enabled

    def matches(self, process_name: str, pid_str: str, log_message: str) -> bool:
        """로그 라인이 이 규칙과 일치하는지 확인"""
        if not self.enabled:
            return False

        # Process 검사
        if self.process and process_name != self.process:
            return False

        # PID 검사
        if self.pid and pid_str != self.pid:
            return False

        # Message 검사
        if self.message:
            if self.use_regex:
                try:
                    if not re.search(self.message, log_message, re.IGNORECASE):
                        return False
                except re.error:
                    # 정규식 오류 시 무시
                    return False
            else:
                if self.message.lower() not in log_message.lower():
                    return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "process": self.process,
            "pid": self.pid,
            "message": self.message,
            "use_regex": self.use_regex,
            "text_color": self.text_color.name(),
            "bg_color": self.bg_color.name(),
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HighlightRule":
        """딕셔너리에서 객체 생성"""
        rule = cls()
        rule.name = data.get("name", "")
        rule.process = data.get("process", "")
        rule.pid = data.get("pid", "")
        rule.message = data.get("message", "")
        rule.use_regex = data.get("use_regex", False)
        rule.text_color = QColor(data.get("text_color", "#000000"))
        rule.bg_color = QColor(data.get("bg_color", "#ffff00"))
        rule.enabled = data.get("enabled", True)
        return rule


class HighlightConfigDialog(QDialog):
    """하이라이트 설정 다이얼로그"""

    rules_changed = Signal(list)  # 규칙 변경 시그널

    def __init__(self, parent=None, rules: List[HighlightRule] = None):
        super().__init__(parent)
        self.rules = rules or []
        self.setWindowTitle("Message Filter Configuration")
        self.setModal(True)
        self.resize(800, 600)

        self._setup_ui()
        self._load_rules()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()

        # 규칙 목록 테이블
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(8)
        self.rules_table.setHorizontalHeaderLabels(
            [
                "Enabled",
                "Name",
                "Process",
                "PID",
                "Message",
                "Regex",
                "Text Color",
                "BG Color",
            ]
        )
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rules_table.horizontalHeader().setStretchLastSection(True)

        # 컬럼 너비 설정
        header = self.rules_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Enabled
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Process
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # PID
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Message
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Regex
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Text Color
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # BG Color

        layout.addWidget(self.rules_table)

        # 버튼 프레임
        button_frame = QFrame()
        button_layout = QHBoxLayout()
        button_frame.setLayout(button_layout)

        self.add_btn = QPushButton("Add Rule")
        self.edit_btn = QPushButton("Edit Rule")
        self.delete_btn = QPushButton("Delete Selected")
        self.move_up_btn = QPushButton("Move Up")
        self.move_down_btn = QPushButton("Move Down")

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.move_up_btn)
        button_layout.addWidget(self.move_down_btn)
        button_layout.addStretch()

        layout.addWidget(button_frame)

        # 다이얼로그 버튼
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

        self.setLayout(layout)

        # 시그널 연결
        self.add_btn.clicked.connect(self._add_rule)
        self.edit_btn.clicked.connect(self._edit_rule)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.move_up_btn.clicked.connect(self._move_rule_up)
        self.move_down_btn.clicked.connect(self._move_rule_down)
        self.rules_table.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _load_rules(self):
        """규칙을 테이블에 로드"""
        self.rules_table.setRowCount(0)

        for rule in self.rules:
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)

            # Enabled
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(enabled_item.flags() & ~Qt.ItemIsEditable)
            enabled_item.setCheckState(Qt.Checked if rule.enabled else Qt.Unchecked)
            self.rules_table.setItem(row, 0, enabled_item)

            # Name
            name_item = QTableWidgetItem(rule.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.rules_table.setItem(row, 1, name_item)

            # Process
            process_item = QTableWidgetItem(rule.process)
            process_item.setFlags(process_item.flags() & ~Qt.ItemIsEditable)
            self.rules_table.setItem(row, 2, process_item)

            # PID
            pid_item = QTableWidgetItem(rule.pid)
            pid_item.setFlags(pid_item.flags() & ~Qt.ItemIsEditable)
            self.rules_table.setItem(row, 3, pid_item)

            # Message
            message_item = QTableWidgetItem(rule.message)
            message_item.setFlags(message_item.flags() & ~Qt.ItemIsEditable)
            self.rules_table.setItem(row, 4, message_item)

            # Regex
            regex_item = QTableWidgetItem("✓" if rule.use_regex else "")
            regex_item.setFlags(regex_item.flags() & ~Qt.ItemIsEditable)
            self.rules_table.setItem(row, 5, regex_item)

            # Text Color
            text_color_item = QTableWidgetItem()
            text_color_item.setBackground(rule.text_color)
            text_color_item.setFlags(text_color_item.flags() & ~Qt.ItemIsEditable)
            self.rules_table.setItem(row, 6, text_color_item)

            # BG Color
            bg_color_item = QTableWidgetItem()
            bg_color_item.setBackground(rule.bg_color)
            bg_color_item.setFlags(bg_color_item.flags() & ~Qt.ItemIsEditable)
            self.rules_table.setItem(row, 7, bg_color_item)

    def _add_rule(self):
        """새 규칙 추가"""
        dialog = HighlightRuleEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            rule = dialog.get_rule()
            self.rules.append(rule)
            self._load_rules()

    def _edit_rule(self):
        """선택된 규칙 편집"""
        current_row = self.rules_table.currentRow()
        if current_row >= 0:
            rule = self.rules[current_row]
            dialog = HighlightRuleEditDialog(self, rule)
            if dialog.exec() == QDialog.Accepted:
                self.rules[current_row] = dialog.get_rule()
                self._load_rules()

    def _delete_selected(self):
        """선택된 규칙 삭제"""
        selected_rows = set()
        for item in self.rules_table.selectedItems():
            selected_rows.add(item.row())

        if selected_rows:
            reply = QMessageBox.question(
                self,
                "Delete Rules",
                f"Delete {len(selected_rows)} selected rule(s)?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # 역순으로 삭제하여 인덱스 문제 방지
                for row in sorted(selected_rows, reverse=True):
                    del self.rules[row]
                self._load_rules()

    def _move_rule_up(self):
        """규칙을 위로 이동"""
        current_row = self.rules_table.currentRow()
        if current_row > 0:
            self.rules[current_row], self.rules[current_row - 1] = (
                self.rules[current_row - 1],
                self.rules[current_row],
            )
            self._load_rules()
            self.rules_table.setCurrentCell(current_row - 1, 0)

    def _move_rule_down(self):
        """규칙을 아래로 이동"""
        current_row = self.rules_table.currentRow()
        if 0 <= current_row < len(self.rules) - 1:
            self.rules[current_row], self.rules[current_row + 1] = (
                self.rules[current_row + 1],
                self.rules[current_row],
            )
            self._load_rules()
            self.rules_table.setCurrentCell(current_row + 1, 0)

    def _on_item_double_clicked(self, item):
        """아이템 더블클릭 시 편집"""
        if item:
            self._edit_rule()

    def get_rules(self) -> List[HighlightRule]:
        """현재 규칙 목록 반환"""
        return self.rules.copy()

    def set_rules(self, rules: List[HighlightRule]):
        """외부에서 규칙 목록을 설정하고 테이블을 갱신합니다."""
        self.rules = rules or []
        self._load_rules()

    def accept(self):
        """다이얼로그 확인 시 규칙 변경 시그널 발신"""
        self.rules_changed.emit(self.rules)
        super().accept()


class HighlightRuleEditDialog(QDialog):
    """하이라이트 규칙 편집 다이얼로그"""

    def __init__(self, parent=None, rule: HighlightRule = None):
        super().__init__(parent)
        self.rule = rule or HighlightRule()
        self.setWindowTitle("Edit Highlight Rule")
        self.setModal(True)

        self._setup_ui()
        self._load_rule()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()

        # 규칙 설정 폼
        form_group = QGroupBox("Rule Settings")
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.process_edit = QLineEdit()
        self.pid_edit = QLineEdit()
        self.message_edit = QLineEdit()
        self.regex_check = QCheckBox("Use Regular Expression")
        self.enabled_check = QCheckBox("Enabled")

        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Process:", self.process_edit)
        form_layout.addRow("PID:", self.pid_edit)
        form_layout.addRow("Message:", self.message_edit)
        form_layout.addRow("", self.regex_check)
        form_layout.addRow("", self.enabled_check)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # 색상 설정 폼
        color_group = QGroupBox("Color Settings")
        color_layout = QFormLayout()

        self.text_color_btn = QPushButton("Choose Text Color")
        self.bg_color_btn = QPushButton("Choose Background Color")
        self.text_color_preview = QLabel()
        self.text_color_preview.setMinimumHeight(20)
        self.bg_color_preview = QLabel()
        self.bg_color_preview.setMinimumHeight(20)

        color_layout.addRow("Text Color:", self.text_color_btn)
        color_layout.addRow("", self.text_color_preview)
        color_layout.addRow("Background Color:", self.bg_color_btn)
        color_layout.addRow("", self.bg_color_preview)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # 다이얼로그 버튼
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

        self.setLayout(layout)

        # 시그널 연결
        self.text_color_btn.clicked.connect(self._choose_text_color)
        self.bg_color_btn.clicked.connect(self._choose_bg_color)

    def _load_rule(self):
        """규칙 데이터 로드"""
        self.name_edit.setText(self.rule.name)
        self.process_edit.setText(self.rule.process)
        self.pid_edit.setText(self.rule.pid)
        self.message_edit.setText(self.rule.message)
        self.regex_check.setChecked(self.rule.use_regex)
        self.enabled_check.setChecked(self.rule.enabled)

        self._update_color_previews()

    def _choose_text_color(self):
        """텍스트 색상 선택"""
        color = QColorDialog.getColor(self.rule.text_color, self)
        if color.isValid():
            self.rule.text_color = color
            self._update_color_previews()

    def _choose_bg_color(self):
        """배경 색상 선택"""
        color = QColorDialog.getColor(self.rule.bg_color, self)
        if color.isValid():
            self.rule.bg_color = color
            self._update_color_previews()

    def _update_color_previews(self):
        """색상 미리보기 업데이트"""
        # 텍스트 색상 미리보기
        self.text_color_preview.setStyleSheet(
            f"background-color: {self.rule.text_color.name()}; "
            f"color: {'white' if self.rule.text_color.lightness() < 128 else 'black'};"
        )
        self.text_color_preview.setText(self.rule.text_color.name())

        # 배경 색상 미리보기
        self.bg_color_preview.setStyleSheet(
            f"background-color: {self.rule.bg_color.name()}; "
            f"color: {'white' if self.rule.bg_color.lightness() < 128 else 'black'};"
        )
        self.bg_color_preview.setText(self.rule.bg_color.name())

    def get_rule(self) -> HighlightRule:
        """편집된 규칙 반환"""
        self.rule.name = self.name_edit.text()
        self.rule.process = self.process_edit.text()
        self.rule.pid = self.pid_edit.text()
        self.rule.message = self.message_edit.text()
        self.rule.use_regex = self.regex_check.isChecked()
        self.rule.enabled = self.enabled_check.isChecked()

        return self.rule
