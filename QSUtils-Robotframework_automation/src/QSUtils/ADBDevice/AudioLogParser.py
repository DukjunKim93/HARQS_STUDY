#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Log Parser for QSMonitor application.
Parses ACM audio logs and extracts relevant metrics for monitoring.
"""

import re
from dataclasses import dataclass
from typing import Dict, Optional, List

from PySide6.QtCore import QObject, Signal


@dataclass
class AudioMetrics:
    """Data class to hold extracted audio metrics."""

    # From AUDIO OUTPUT line
    midbuffer_level: Optional[int] = None
    count: Optional[int] = None
    id: Optional[int] = None
    delay: Optional[int] = None
    delay_sub: Optional[int] = None
    bmc_mode: Optional[int] = None

    # From jitter line
    jitter: Optional[int] = None
    start: Optional[int] = None
    tstamp: Optional[int] = None
    curr: Optional[int] = None
    send: Optional[int] = None
    decoder: Optional[int] = None

    # From buffer line
    buffer: Optional[int] = None
    buffer_sub: Optional[int] = None
    pdelay: Optional[int] = None
    queue: Optional[int] = None
    current: Optional[int] = None
    sec_10: Optional[int] = None

    # From 10sec_max line
    sec_10_max: Optional[int] = None
    local_time: Optional[int] = None
    ptc: Optional[int] = None
    pts: Optional[int] = None
    diff_time: Optional[int] = None

    timestamp: Optional[str] = None  # Log line timestamp


class AudioLogParser(QObject):
    """
    Parser for ACM audio logs.
    Extracts audio metrics from journalctl log lines.
    """

    # Signal emitted when new metrics are parsed
    metrics_updated = Signal(AudioMetrics)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Regular expressions for parsing different log line types
        self.audio_output_pattern = re.compile(
            r"\[\^\^\^ACM\]:AUDIO OUTPUT \(ES\) :\s+MidBuffer Level=(\d+), count=(\d+), id=(\d+), delay=(\d+)\((\d+)\),BMC Mode\[(\d+)\]"
        )

        self.jitter_pattern = re.compile(
            r"\[\^\^\^ACM\]:jitter=(\d+), start=(\d+), tstamp=(\d+), curr=(\d+), send=(\d+), decoder=(\d+)"
        )

        self.buffer_pattern = re.compile(
            r"\[\^\^\^ACM\]:buffer=(\d+)\((\d+)\), pdelay=(\d+), queue=(\d+), current=(\d+), 10sec=(\d+)"
        )

        self.sec_max_pattern = re.compile(
            r"\[\^\^\^ACM\]:10sec_max=(\d+),local_time=(\d+), PTC \[(\d+)\], PTS \[(\d+)\], Diff Time \[(\d+)\]"
        )

        # Timestamp pattern for log lines
        self.timestamp_pattern = re.compile(r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})")

        self.current_metrics = AudioMetrics()

    def parse_log_line(self, line: str) -> Optional[AudioMetrics]:
        """
        Parse a single log line and extract audio metrics.
        Emit metrics immediately for each line to provide real-time updates.

        Args:
            line: Log line to parse

        Returns:
            AudioMetrics object if line contains relevant data, None otherwise
        """
        line = line.strip()
        if not line:
            return None

        # Create a new metrics object for each line to ensure immediate updates
        metrics = AudioMetrics()

        # Extract timestamp
        timestamp_match = self.timestamp_pattern.match(line)
        if timestamp_match:
            metrics.timestamp = timestamp_match.group(1)

        # Check for AUDIO OUTPUT line
        audio_match = self.audio_output_pattern.search(line)
        if audio_match:
            metrics.midbuffer_level = int(audio_match.group(1))
            metrics.count = int(audio_match.group(2))
            metrics.id = int(audio_match.group(3))
            metrics.delay = int(audio_match.group(4))
            metrics.delay_sub = int(audio_match.group(5))
            metrics.bmc_mode = int(audio_match.group(6))

            # Emit metrics immediately for real-time updates
            self.metrics_updated.emit(metrics)
            return metrics

        # Check for jitter line
        jitter_match = self.jitter_pattern.search(line)
        if jitter_match:
            metrics.jitter = int(jitter_match.group(1))
            metrics.start = int(jitter_match.group(2))
            metrics.tstamp = int(jitter_match.group(3))
            metrics.curr = int(jitter_match.group(4))
            metrics.send = int(jitter_match.group(5))
            metrics.decoder = int(jitter_match.group(6))

            # Emit metrics immediately for real-time updates
            self.metrics_updated.emit(metrics)
            return metrics

        # Check for buffer line
        buffer_match = self.buffer_pattern.search(line)
        if buffer_match:
            metrics.buffer = int(buffer_match.group(1))
            metrics.buffer_sub = int(buffer_match.group(2))
            metrics.pdelay = int(buffer_match.group(3))
            metrics.queue = int(buffer_match.group(4))
            metrics.current = int(buffer_match.group(5))
            metrics.sec_10 = int(buffer_match.group(6))

            # Emit metrics immediately for real-time updates
            self.metrics_updated.emit(metrics)
            return metrics

        # Check for 10sec_max line (usually the last line)
        sec_max_match = self.sec_max_pattern.search(line)
        if sec_max_match:
            metrics.sec_10_max = int(sec_max_match.group(1))
            metrics.local_time = int(sec_max_match.group(2))
            metrics.ptc = int(sec_max_match.group(3))
            metrics.pts = int(sec_max_match.group(4))
            metrics.diff_time = int(sec_max_match.group(5))

            # Emit metrics immediately for real-time updates
            self.metrics_updated.emit(metrics)
            return metrics

        return None

    def parse_log_lines(self, lines: List[str]) -> List[AudioMetrics]:
        """
        Parse multiple log lines and return list of extracted metrics.

        Args:
            lines: List of log lines to parse

        Returns:
            List of AudioMetrics objects
        """
        metrics_list = []
        for line in lines:
            metrics = self.parse_log_line(line)
            if metrics:
                metrics_list.append(metrics)

        return metrics_list

    def reset_metrics(self):
        """Reset current metrics to default values."""
        self.current_metrics = AudioMetrics()

    def get_metrics_as_dict(self, metrics: AudioMetrics) -> Dict[str, str]:
        """
        Convert AudioMetrics to dictionary for UI display.

        Args:
            metrics: AudioMetrics object

        Returns:
            Dictionary with formatted string values
        """
        return {
            "timestamp": metrics.timestamp or "N/A",
            "midbuffer_level": (
                str(metrics.midbuffer_level)
                if metrics.midbuffer_level is not None
                else "N/A"
            ),
            "count": str(metrics.count) if metrics.count is not None else "N/A",
            "id": str(metrics.id) if metrics.id is not None else "N/A",
            "delay": (
                f"{metrics.delay}({metrics.delay_sub})"
                if metrics.delay is not None
                else "N/A"
            ),
            "bmc_mode": (
                str(metrics.bmc_mode) if metrics.bmc_mode is not None else "N/A"
            ),
            "jitter": str(metrics.jitter) if metrics.jitter is not None else "N/A",
            "start": str(metrics.start) if metrics.start is not None else "N/A",
            "tstamp": str(metrics.tstamp) if metrics.tstamp is not None else "N/A",
            "curr": str(metrics.curr) if metrics.curr is not None else "N/A",
            "send": str(metrics.send) if metrics.send is not None else "N/A",
            "decoder": str(metrics.decoder) if metrics.decoder is not None else "N/A",
            "buffer": (
                f"{metrics.buffer}({metrics.buffer_sub})"
                if metrics.buffer is not None
                else "N/A"
            ),
            "pdelay": str(metrics.pdelay) if metrics.pdelay is not None else "N/A",
            "queue": str(metrics.queue) if metrics.queue is not None else "N/A",
            "current": str(metrics.current) if metrics.current is not None else "N/A",
            "sec_10": str(metrics.sec_10) if metrics.sec_10 is not None else "N/A",
            "sec_10_max": (
                str(metrics.sec_10_max) if metrics.sec_10_max is not None else "N/A"
            ),
            "local_time": (
                str(metrics.local_time) if metrics.local_time is not None else "N/A"
            ),
            "ptc": str(metrics.ptc) if metrics.ptc is not None else "N/A",
            "pts": str(metrics.pts) if metrics.pts is not None else "N/A",
            "diff_time": (
                str(metrics.diff_time) if metrics.diff_time is not None else "N/A"
            ),
        }
