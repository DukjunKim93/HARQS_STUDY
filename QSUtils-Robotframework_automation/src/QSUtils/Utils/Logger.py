#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced logging utility for QSMonitor application.
Implements singleton pattern with configurable handlers and formatters.
"""

import logging
import logging.handlers
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union


class LogLevel(Enum):
    """Enumeration for log levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    NONE = 100  # Custom level to disable all logging


@dataclass
class LogConfig:
    """Configuration data class for logger settings."""

    level: LogLevel = LogLevel.INFO
    format_string: str = "%(asctime)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    enable_console: bool = True
    enable_file: bool = False
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    propagate: bool = False


class Logger:
    """
    Singleton logger class for QSMonitor application.
    Provides centralized logging with configurable handlers and formatters.
    """

    _instance: Optional["Logger"] = None
    _logger: Optional[logging.Logger] = None
    _config: LogConfig = LogConfig()

    def __new__(cls) -> "Logger":
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self) -> None:
        """Initialize the logger with default configuration.

        If root logger is already configured (handlers exist), do not add
        any handlers here. Let this named logger propagate to root so that
        a centralized configuration (Utils.logging_config) controls output.
        """
        self._logger = logging.getLogger("QSMonitor")
        root = logging.getLogger()

        # Always configure the logger
        self._logger.setLevel(self._config.level.value)
        self._logger.propagate = self._config.propagate

        # Remove existing handlers to avoid duplicates
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # Add console handler if enabled
        if self._config.enable_console:
            self._add_console_handler()

        # Add file handler if enabled
        if self._config.enable_file and self._config.file_path:
            self._add_file_handler()

    def _add_console_handler(self) -> None:
        """Add console handler to the logger."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._config.level.value)

        formatter = logging.Formatter(
            self._config.format_string, datefmt=self._config.date_format
        )
        console_handler.setFormatter(formatter)

        self._logger.addHandler(console_handler)

    def _add_file_handler(self) -> None:
        """Add rotating file handler to the logger."""
        try:
            # Ensure directory exists
            file_path = Path(self._config.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                self._config.file_path,
                maxBytes=self._config.max_file_size,
                backupCount=self._config.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(self._config.level.value)

            formatter = logging.Formatter(
                self._config.format_string, datefmt=self._config.date_format
            )
            file_handler.setFormatter(formatter)

            self._logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to console logging if file handler fails
            print(f"Failed to initialize file handler: {e}")

    def configure(self, config: LogConfig) -> None:
        """
        Configure the logger with new settings.

        Args:
            config: New configuration for the logger
        """
        self._config = config
        self._initialize_logger()

    def set_level(self, level: Union[LogLevel, str, int]) -> None:
        """
        Set the logging level.

        Args:
            level: Log level as enum, string, or integer
        """
        if isinstance(level, str):
            if level.upper() == "NONE":
                level = LogLevel.NONE
            else:
                level = LogLevel[level.upper()]
        elif isinstance(level, int):
            level = LogLevel(level)

        self._config.level = level
        if self._logger:
            self._logger.setLevel(level.value)

    def add_file_logging(
        self, file_path: str, level: Optional[LogLevel] = None
    ) -> bool:
        """
        Add file logging to the logger.

        Args:
            file_path: Path to the log file
            level: Optional log level for file handler (uses logger level if None)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._config.enable_file = True
            self._config.file_path = file_path

            if level:
                file_level = level.value
            else:
                file_level = self._config.level.value

            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self._config.max_file_size,
                backupCount=self._config.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(file_level)

            formatter = logging.Formatter(
                self._config.format_string, datefmt=self._config.date_format
            )
            file_handler.setFormatter(formatter)

            if self._logger:
                self._logger.addHandler(file_handler)

            return True
        except Exception as e:
            self.error(f"Failed to add file logging: {e}")
            return False

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        if self._logger and self._logger.isEnabledFor(LogLevel.DEBUG.value):
            # Remove null characters from message to prevent ValueError
            cleaned_message = message.replace("\x00", "?")
            # Use errors='ignore' to handle any remaining null characters
            try:
                self._logger.debug(cleaned_message, *args, **kwargs)
            except ValueError:
                # If ValueError still occurs, we'll encode/decode to remove null characters
                try:
                    final_message = cleaned_message.encode(
                        "utf-8", errors="ignore"
                    ).decode("utf-8")
                    self._logger.debug(final_message, *args, **kwargs)
                except Exception:
                    # If all else fails, we'll just log a generic message
                    self._logger.debug(
                        "Log message contained null characters and could not be processed",
                        *args,
                        **kwargs,
                    )

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        if self._logger and self._logger.isEnabledFor(LogLevel.INFO.value):
            self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        if self._logger and self._logger.isEnabledFor(LogLevel.WARNING.value):
            self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        if self._logger and self._logger.isEnabledFor(LogLevel.ERROR.value):
            self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        if self._logger and self._logger.isEnabledFor(LogLevel.CRITICAL.value):
            self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception message with traceback."""
        if self._logger and self._logger.isEnabledFor(LogLevel.ERROR.value):
            self._logger.exception(message, *args, **kwargs)

    def is_enabled_for(self, level: LogLevel) -> bool:
        """Check if a log level is enabled."""
        return self._config.level.value <= level.value

    def get_current_config(self) -> LogConfig:
        """Get current logger configuration."""
        return self._config


# Global logger instance
_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


# Legacy function wrappers for backward compatibility
def set_log_level(level: Union[LogLevel, str, int]) -> None:
    """
    Set the global log level.

    Args:
        level: Log level as enum, string, or integer
    """
    logger = get_logger()
    logger.set_level(level)


def LOGD(message: str) -> None:
    """DEBUG level logging function for backward compatibility."""
    # Check if message contains null characters and handle them
    if "\x00" in message:
        # If null characters are present, we need to handle them carefully
        # We'll try to clean the string by encoding/decoding
        try:
            # Attempt to encode to bytes and decode back, ignoring errors
            cleaned_message = message.encode("utf-8", errors="ignore").decode("utf-8")
        except Exception:
            # If encoding/decoding fails, we'll use a simple replacement
            cleaned_message = message.replace("\x00", "?")
    else:
        cleaned_message = message

    # Ensure cleaned_message does not contain null characters
    if "\x00" in cleaned_message:
        cleaned_message = cleaned_message.replace("\x00", "?")

    # Use errors='ignore' to handle any remaining null characters
    try:
        get_logger().debug(cleaned_message)
    except ValueError:
        # If ValueError still occurs, we'll encode/decode to remove null characters
        try:
            final_message = cleaned_message.encode("utf-8", errors="ignore").decode(
                "utf-8"
            )
            get_logger().debug(final_message)
        except Exception:
            # If all else fails, we'll just log a generic message
            get_logger().debug(
                "Log message contained null characters and could not be processed"
            )
    except SystemError:
        # If SystemError occurs, we'll just log a generic message
        get_logger().debug(
            "Log message contained null characters and could not be processed"
        )


def LOGI(message: str) -> None:
    """INFO level logging function for backward compatibility."""
    get_logger().info(message)


def LOGW(message: str) -> None:
    """WARNING level logging function."""
    get_logger().warning(message)


def LOGE(message: str) -> None:
    """ERROR level logging function for backward compatibility."""
    get_logger().error(message)


def LOGC(message: str) -> None:
    """CRITICAL level logging function."""
    get_logger().critical(message)


def LOGEX(message: str) -> None:
    """EXCEPTION level logging function with traceback."""
    get_logger().exception(message)


# Initialize logger with default configuration
if __name__ != "__main__":
    # Only initialize when imported, not when run directly
    get_logger()
