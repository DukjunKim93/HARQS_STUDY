# -*- coding: utf-8 -*-
"""
Dump Manager Dialogs
Dump 관련 다이얼로그 클래스들
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QProgressDialog,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QRadioButton,
    QButtonGroup,
    QDialogButtonBox,
    QPushButton,
    QMessageBox,
    QCheckBox,
)

from QSUtils.DumpManager.DumpTypes import DumpMode


class DumpProgressDialog(QProgressDialog):
    """Dump 추적 진행 상황 다이얼로그"""

    def __init__(
        self,
        parent: Optional[QDialog] = None,
        dump_mode: Optional[DumpMode] = None,
        upload_enabled: bool = False,
    ):
        super().__init__(parent)
        self.dump_mode = dump_mode
        self.upload_enabled = upload_enabled
        self.upload_checkbox = None

        self.setWindowTitle("Coredump Processing in Progress")
        self.setMinimumWidth(450)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        # DIALOG 모드일 때만 취소 버튼 표시
        if dump_mode == DumpMode.DIALOG:
            cancel_button = QPushButton("Cancel Dump")
            self.setCancelButton(cancel_button)
        else:
            self.setCancelButton(None)

        # ESC 키로 닫히는 것 방지
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        # 업로드 체크박스 UI 추가
        self._setup_upload_ui()

    def _setup_upload_ui(self):
        """업로드 체크박스 UI 설정"""
        # DIALOG 모드일 때만 업로드 체크박스 표시
        if self.dump_mode == DumpMode.DIALOG:
            # 업로드 체크박스를 위한 레이아웃 생성
            upload_layout = QHBoxLayout()

            # 업로드 체크박스
            self.upload_checkbox = QCheckBox("Upload to JFrog after extraction")
            self.upload_checkbox.setChecked(self.upload_enabled)

            # 체크박스 스타일 설정
            self.upload_checkbox.setStyleSheet(
                "QCheckBox { "
                "   font-size: 12px; "
                "   padding: 5px; "
                "   color: #333; "
                "} "
                "QCheckBox:hover { "
                "   background-color: #f0f0f0; "
                "   border-radius: 3px; "
                "}"
            )

            # 체크박스 상태 변경 시그널 연결
            self.upload_checkbox.toggled.connect(self._on_upload_checkbox_changed)

            upload_layout.addWidget(self.upload_checkbox)
            upload_layout.addStretch()

            # 기존 레이아웃에 업로드 체크박스 추가
            # QProgressDialog의 레이아웃을 가져와서 체크박스 추가
            existing_layout = self.layout()
            if existing_layout:
                # 진행상황 레이블과 취소 버튼 사이에 체크박스 추가
                existing_layout.insertLayout(existing_layout.count() - 1, upload_layout)

    def _on_upload_checkbox_changed(self, checked: bool):
        """업로드 체크박스 상태 변경 처리"""
        self.upload_enabled = checked
        from QSUtils.Utils.Logger import LOGD

        LOGD(f"DumpProgressDialog: Upload checkbox changed to {checked}")

    def is_upload_enabled(self) -> bool:
        """업로드 활성화 상태 반환"""
        if self.upload_checkbox:
            return self.upload_checkbox.isChecked()
        return self.upload_enabled

    def set_upload_enabled(self, enabled: bool):
        """업로드 활성화 상태 설정"""
        self.upload_enabled = enabled
        if self.upload_checkbox:
            self.upload_checkbox.setChecked(enabled)


class DumpCancellationDialog(QDialog):
    """Dump 취소 확인 다이얼로그"""

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Dump Cancellation")
        self.setMinimumWidth(500)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self._cleanup_target = True  # 기본값: target cleanup 수행

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # 경고 메시지
        warning_label = QLabel("⚠️ Dump Extraction Cancellation")
        warning_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #d32f2f;"
        )
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)

        # 설명 텍스트
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        info_text.setHtml("""
        <p>You are about to cancel the dump extraction process. Please choose how to handle the remaining files:</p>
        <br>
        <p><b>Options:</b></p>
        <ul>
            <li><b>Stop process and clean target device:</b><br>
            • Terminates the current dump process<br>
            • Removes all coredump files from the target device<br>
            • Prevents repeated dump attempts</li>
            <br>
            <li><b>Stop process only:</b><br>
            • Terminates the current dump process<br>
            • Leaves coredump files on the target device<br>
            • May trigger repeated dump attempts</li>
        </ul>
        <br>
        <p><b>Recommendation:</b> Choose "Stop process and clean target device" to prevent repeated dump cycles.</p>
        """)
        layout.addWidget(info_text)

        # 옵션 버튼 그룹
        button_group = QButtonGroup(self)

        cleanup_radio = QRadioButton(
            "Stop process and clean target device (Recommended)"
        )
        cleanup_radio.setChecked(True)
        button_group.addButton(cleanup_radio, 1)
        layout.addWidget(cleanup_radio)

        stop_only_radio = QRadioButton("Stop process only")
        button_group.addButton(stop_only_radio, 2)
        layout.addWidget(stop_only_radio)

        # 버튼 클릭 연결
        cleanup_radio.toggled.connect(lambda checked: self._set_cleanup_option(checked))

        # 버튼 박스
        button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        yes_button = button_box.button(QDialogButtonBox.Yes)
        no_button = button_box.button(QDialogButtonBox.No)

        yes_button.setText("Confirm Cancellation")
        no_button.setText("Continue Dump")

        layout.addWidget(button_box)

        self.setLayout(layout)

    def _set_cleanup_option(self, cleanup_enabled: bool) -> None:
        """Target cleanup 옵션 설정"""
        self._cleanup_target = cleanup_enabled

    def should_cleanup_target(self) -> bool:
        """Target cleanup 수행 여부 반환"""
        return self._cleanup_target


class DumpCompletionDialog:
    """Dump 완료 다이얼로그 유틸리티"""

    @staticmethod
    def show_completion_dialog(
        parent: Optional[QDialog],
        success: bool,
        message: str,
        working_dir: Optional[Path] = None,
    ) -> None:
        """완료 다이얼로그 표시"""
        try:
            msg_box = QMessageBox(parent)

            if success:
                msg_box.setWindowTitle("Dump Extraction Complete")
                msg_box.setText("Coredump extraction has been completed successfully!")
                msg_box.setInformativeText(message)
                msg_box.setIcon(QMessageBox.Icon.Information)

                # 상세 정보 버튼 추가
                details_button = QPushButton("Show Details")
                msg_box.addButton(details_button, QMessageBox.ButtonRole.ActionRole)

                ok_button = msg_box.addButton(QMessageBox.StandardButton.Ok)
                msg_box.setDefaultButton(ok_button)

                result = msg_box.exec()

                if msg_box.clickedButton() == details_button:
                    # 상세 정보 표시
                    DumpCompletionDialog._show_dump_details_dialog(parent, working_dir)
            else:
                msg_box.setWindowTitle("Dump Extraction Failed")
                msg_box.setText("Coredump extraction failed!")
                msg_box.setInformativeText(message)
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.exec()

        except Exception as e:
            from QSUtils.Utils.Logger import LOGD

            LOGD(f"DumpCompletionDialog: Error showing completion dialog: {e}")

    @staticmethod
    def _show_dump_details_dialog(
        parent: Optional[QDialog], working_dir: Optional[Path]
    ) -> None:
        """Dump 상세 정보 다이얼로그 표시"""
        try:
            from pathlib import Path

            dialog = QDialog(parent)
            dialog.setWindowTitle("Dump Extraction Details")
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(400)

            layout = QVBoxLayout()

            # 작업 디렉토리 정보
            dir_label = QLabel(f"Working Directory: {working_dir}")
            dir_label.setWordWrap(True)
            layout.addWidget(dir_label)

            # 생성된 zip 파일 목록
            if working_dir:
                zip_files = list(Path(working_dir).glob("*.zip"))
                if zip_files:
                    files_label = QLabel("Generated ZIP Files:")
                    layout.addWidget(files_label)

                    files_text = QTextEdit()
                    files_text.setReadOnly(True)
                    files_text.setMaximumHeight(150)

                    files_info = ""
                    for zip_file in zip_files:
                        size_kb = zip_file.stat().st_size / 1024
                        files_info += f"• {zip_file.name} ({size_kb:.1f} KB)\n"

                    files_text.setPlainText(files_info)
                    layout.addWidget(files_text)

            # 닫기 버튼
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.setLayout(layout)
            dialog.exec()

        except Exception as e:
            from QSUtils.Utils.Logger import LOGD

            LOGD(f"DumpCompletionDialog: Error showing details dialog: {e}")
