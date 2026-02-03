#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version Information Dialog for displaying device software version details.
"""

from PySide6.QtWidgets import (
    QDialog,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QMessageBox,
    QApplication,
)

from QSUtils.Utils.Logger import LOGD


class VersionInfoDialog(QDialog):
    """
    Dialog for displaying device version information.
    Provides functionality to view and copy version details.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Version Information")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Text editor for version information
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.text_edit)

        # Button layout
        button_layout = QHBoxLayout()

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        # Copy button
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self._copy_to_clipboard)
        button_layout.addWidget(self.copy_button)

        layout.addLayout(button_layout)

    def set_version_content(self, content: str):
        """
        Set the version information content to display.

        Args:
            content: Version information content as string
        """
        self.text_edit.setPlainText(content)

    def _copy_to_clipboard(self):
        """Copy the version information to clipboard."""
        try:
            text = self.text_edit.toPlainText()
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(
                self, "Copied", "Version information copied to clipboard."
            )
        except Exception as e:
            LOGD(f"VersionInfoDialog: Error copying to clipboard: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to copy to clipboard:\n{str(e)}"
            )

    @staticmethod
    def show_version_dialog(parent, content: str):
        """
        Static method to create and show version dialog.

        Args:
            parent: Parent widget
            content: Version information content

        Returns:
            VersionInfoDialog instance
        """
        dialog = VersionInfoDialog(parent)
        dialog.set_version_content(content)
        dialog.exec()
        return dialog
