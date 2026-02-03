#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced file utilities for QSMonitor application.
Provides platform-independent file operations using PySide.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Any

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
except ImportError:
    # Fallback for non-GUI environments
    QDesktopServices = None
    QUrl = None

from QSUtils.Utils.Logger import get_logger


@dataclass
class FileOperationResult:
    """Result data class for file operations."""

    success: bool
    message: str = ""
    data: Any = None
    error: Optional[Exception] = None


class FileManager:
    """Enhanced file manager with platform-independent operations."""

    def __init__(self):
        self.logger = get_logger()

    def open_file_browser(
        self, directory_path: Union[str, Path]
    ) -> FileOperationResult:
        """
        Open the specified directory in the system's file browser using PySide.

        Args:
            directory_path: Path to the directory to open

        Returns:
            FileOperationResult: Result of the operation
        """
        try:
            path = Path(directory_path)

            # Validate path
            if not path.exists():
                error_msg = f"Directory does not exist: {directory_path}"
                self.logger.error(error_msg)
                return FileOperationResult(success=False, message=error_msg)

            if not path.is_dir():
                error_msg = f"Path is not a directory: {directory_path}"
                self.logger.error(error_msg)
                return FileOperationResult(success=False, message=error_msg)

            # Use PySide's QDesktopServices for platform-independent file browser opening
            if QDesktopServices is None:
                error_msg = "PySide6 is not available. Cannot open file browser."
                self.logger.error(error_msg)
                return FileOperationResult(success=False, message=error_msg)

            url = QUrl.fromLocalFile(str(path.resolve()))
            success = QDesktopServices.openUrl(url)

            if success:
                success_msg = f"Opened file browser for directory: {directory_path}"
                self.logger.info(success_msg)
                return FileOperationResult(success=True, message=success_msg)
            else:
                error_msg = (
                    f"Failed to open file browser for directory: {directory_path}"
                )
                self.logger.error(error_msg)
                return FileOperationResult(success=False, message=error_msg)

        except Exception as e:
            error_msg = (
                f"Unexpected error in open_file_browser for {directory_path}: {str(e)}"
            )
            self.logger.error(error_msg)
            return FileOperationResult(success=False, message=error_msg, error=e)

    def ensure_directory_exists(
        self, directory_path: Union[str, Path]
    ) -> FileOperationResult:
        """
        Ensure that the specified directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory

        Returns:
            FileOperationResult: Result of the operation
        """
        try:
            path = Path(directory_path)
            path.mkdir(parents=True, exist_ok=True)

            success_msg = f"Directory ensured: {directory_path}"
            self.logger.debug(success_msg)
            return FileOperationResult(success=True, message=success_msg, data=path)
        except Exception as e:
            error_msg = f"Failed to create directory {directory_path}: {str(e)}"
            self.logger.error(error_msg)
            return FileOperationResult(success=False, message=error_msg, error=e)


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get the global file manager instance."""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager


# Legacy function wrappers for backward compatibility
def open_file_browser(directory_path: Union[str, Path]) -> bool:
    """
    Open the specified directory in the system's file browser.

    Args:
        directory_path: Path to the directory to open

    Returns:
        bool: True if successful, False otherwise
    """
    result = get_file_manager().open_file_browser(directory_path)
    return result.success


def ensure_directory_exists(directory_path: Union[str, Path]) -> bool:
    """
    Ensure that the specified directory exists, creating it if necessary.

    Args:
        directory_path: Path to the directory

    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    result = get_file_manager().ensure_directory_exists(directory_path)
    return result.success
