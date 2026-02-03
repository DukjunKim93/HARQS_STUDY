#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized logging configuration for QSMonitor apps.
This module standardizes logging using Python's logging module with
consistent format, handlers, and level policy.
"""

from __future__ import annotations

import logging
import logging.handlers
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_LOG_DIRNAME = "logs"
DEFAULT_LOG_FILENAME = "QSMonitor.log"
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%y%m%d_%H%M%S"


@dataclass
class LoggingConfig:
    app_name: str = "QSMonitor"
    level: str = DEFAULT_LOG_LEVEL
    log_dir: Optional[Path] = None
    log_file: Optional[str] = None
    to_console: bool = True
    max_bytes: int = 5 * 1024 * 1024
    backup_count: int = 5


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def configure_logging(config: Optional[LoggingConfig] = None) -> None:
    """Configure root logging once.

    If already configured (handlers exist on root logger), this will only
    adjust the level and return without adding duplicate handlers.
    """
    if config is None:
        config = LoggingConfig()

    root = logging.getLogger()

    # Determine log directory and file
    # Only use log_dir if explicitly specified in config
    log_dir = config.log_dir
    log_file = config.log_file or DEFAULT_LOG_FILENAME

    # Only create log_path if log_dir is specified
    log_path = None
    if log_dir:
        log_path = log_dir / log_file

    # Normalize level
    try:
        level_value = getattr(logging, str(config.level).upper())
    except AttributeError:
        level_value = logging.INFO

    # Basic formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    if not root.handlers:
        # File handler (rotating) - only add if log directory is valid AND log_file is specified
        if log_dir and config.log_file:
            try:
                # Ensure directory exists only when adding file handler
                _ensure_dir(log_dir)

                file_handler = logging.handlers.RotatingFileHandler(
                    log_path,
                    maxBytes=config.max_bytes,
                    backupCount=config.backup_count,
                    encoding="utf-8",
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(level_value)
                root.addHandler(file_handler)
            except Exception as e:
                # If file handler creation fails, log to console only
                print(f"Warning: Failed to create file handler for {log_path}: {e}")

        # Console handler
        if config.to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level_value)
            root.addHandler(console_handler)

    # Always set the root level (even if already had handlers)
    root.setLevel(level_value)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Convenience wrapper that returns a module logger."""
    return logging.getLogger(name if name else __name__)
