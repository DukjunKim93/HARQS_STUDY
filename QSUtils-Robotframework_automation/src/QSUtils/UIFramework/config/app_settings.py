#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataclass-based application settings loaded from YAML (~/.qsmonitor.yaml).
Falls back to sensible defaults when file is missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    yaml = None  # type: ignore


@dataclass
class WindowGeometry:
    width: int = 770
    height: int = 980
    x: int = 100
    y: int = 100


@dataclass
class AppSettings:
    log_directory: Optional[Path] = (
        None  # Changed to None - no default log directory creation
    )
    log_level: str = "DEBUG"
    qsmonitor_window_geometry: WindowGeometry = field(default_factory=WindowGeometry)
    qslogmonitor_window_geometry: WindowGeometry = field(
        default_factory=lambda: WindowGeometry(x=200, y=200)
    )

    @staticmethod
    def load(path: Optional[Path] = None) -> "AppSettings":
        if path is None:
            raise ValueError("Path must be provided")

        cfg_path = path
        if yaml is None or not cfg_path.exists():
            return AppSettings()
        try:
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}

        def parse_win(d: Dict[str, Any], default: WindowGeometry) -> WindowGeometry:
            return WindowGeometry(
                width=int(d.get("width", default.width)),
                height=int(d.get("height", default.height)),
                x=int(d.get("x", default.x)),
                y=int(d.get("y", default.y)),
            )

        default_qs = WindowGeometry()
        default_log = WindowGeometry(x=200, y=200)

        # Only set log_directory if explicitly specified in config
        log_dir = data.get("log_directory")
        if log_dir:
            log_directory = Path(str(log_dir))
        else:
            log_directory = None

        return AppSettings(
            log_directory=log_directory,
            log_level=str(data.get("log_level", "DEBUG")),
            qsmonitor_window_geometry=parse_win(
                data.get("qsmonitor_window_geometry", {}), default_qs
            ),
            qslogmonitor_window_geometry=parse_win(
                data.get("qslogmonitor_window_geometry", {}), default_log
            ),
        )
