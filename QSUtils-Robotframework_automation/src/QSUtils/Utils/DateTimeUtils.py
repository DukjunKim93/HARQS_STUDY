#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Date and time utilities for QSMonitor application.
Provides timestamp generation and other datetime-related functionality.
"""

from datetime import datetime


class TimestampGenerator:
    """Utility class for generating timestamps."""

    @staticmethod
    def get_log_timestamp() -> str:
        """Get timestamp formatted for log files."""
        return datetime.now().strftime("%y%m%d-%H%M%S")

    @staticmethod
    def get_detailed_timestamp() -> str:
        """Get detailed timestamp with milliseconds for logging."""
        current_time = datetime.now()
        return current_time.strftime("%y%m%d-%H:%M:%S.%f")[:-3]

    @staticmethod
    def get_iso_timestamp() -> str:
        """Get ISO format timestamp."""
        return datetime.now().isoformat()
