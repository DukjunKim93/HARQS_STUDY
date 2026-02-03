#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common types and utilities for the command layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Dict


@dataclass
class ExecutionContext:
    """Represents execution context for commands (minimal initial version)."""

    device: Any
    timeout_sec: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CommandError:
    code: str
    message: str
    detail: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code}: {self.message}"
