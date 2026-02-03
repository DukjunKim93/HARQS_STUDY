#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Manager for the QSMonitor application.
Manages application settings persistence.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from QSUtils.Utils.Logger import LOGD


class SettingsManager:
    """
    Manages application settings persistence.

    Handles loading, saving, and accessing application settings.
    """

    def __init__(self, config_file: Path, default_settings: Dict[str, Any]):
        """
        Initialize the settings manager.

        Args:
            config_file: Path to the configuration file
            default_settings: Default settings dictionary
        """
        self.config_file = config_file
        self._default_settings = default_settings
        self._settings: Dict[str, Any] = {}

        # Load settings from file
        self._load_settings()

    def _load_settings(self):
        """Load settings from JSON file or create default settings."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
                LOGD(f"SettingsManager: Loaded settings from {self.config_file}")
                return
            except (json.JSONDecodeError, IOError) as e:
                LOGD(
                    f"SettingsManager: Failed to load settings from {self.config_file}: {e}"
                )
                # fall through to defaults

        LOGD("SettingsManager: No settings found, using defaults")
        self._settings = self._get_default_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings."""
        return self._default_settings.copy()

    def save_settings(self) -> bool:
        """
        Save current settings to JSON file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Merge with existing on-disk settings to avoid clobbering keys
            existing: Dict[str, Any] = {}
            if self.config_file.exists():
                try:
                    with open(self.config_file, "r", encoding="utf-8") as rf:
                        existing = json.load(rf) or {}
                except Exception:
                    existing = {}

            merged = {**existing, **self._settings}
            self._settings = merged  # keep in-memory view consistent with what we write

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)

            LOGD(f"SettingsManager: Saved settings to {self.config_file}")
            return True
        except IOError as e:
            LOGD(f"SettingsManager: Failed to save settings: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value

        Returns:
            True if successful, False otherwise
        """
        self._settings[key] = value
        return self.save_settings()

    def get_window_geometry(
        self,
        geometry_key: str = "window_geometry",
        default_geometry: Optional[Dict[str, int]] = None,
    ) -> Dict[str, int]:
        """
        Get window geometry settings.

        Args:
            geometry_key: Key for geometry settings in the configuration
            default_geometry: Default geometry if not found

        Returns:
            Dictionary with width, height, x, y keys
        """
        if default_geometry is None:
            default_geometry = {"width": 770, "height": 980, "x": 100, "y": 100}
        return self.get(geometry_key, default_geometry)

    def set_window_geometry(
        self, geometry: Dict[str, int], geometry_key: str = "window_geometry"
    ) -> bool:
        """
        Set window geometry settings.

        Args:
            geometry: Dictionary with width, height, x, y keys
            geometry_key: Key for geometry settings in the configuration

        Returns:
            True if successful, False otherwise
        """
        return self.set(geometry_key, geometry)

    def get_log_level(self) -> str:
        """
        Get log level setting.

        Returns:
            Log level string
        """
        return self.get("log_level", "Error")

    def set_log_level(self, level: str) -> bool:
        """
        Set log level setting.

        Args:
            level: Log level string

        Returns:
            True if successful, False otherwise
        """
        return self.set("log_level", level)

    def get_log_directory(self) -> str:
        """
        Get log directory setting.

        Returns:
            Log directory path
        """
        return self.get("log_directory", str(Path.home() / "QSMonitor_logs"))

    def set_log_directory(self, directory: str) -> bool:
        """
        Set log directory setting.

        Args:
            directory: Log directory path

        Returns:
            True if successful, False otherwise
        """
        return self.set("log_directory", directory)

    # ---- Filter rules ----
    def get_filter_rules(self, filter_key: str = "filter_rules") -> Any:
        """
        Get persisted message filter rules.

        Args:
            filter_key: Key for filter rules in the configuration

        Returns:
            A list of dicts (serialized HighlightRule) or an empty list.
        """
        return self.get(filter_key, [])

    def set_filter_rules(self, rules: Any, filter_key: str = "filter_rules") -> bool:
        """
        Persist message filter rules.

        Args:
            rules: List of dicts (serialized HighlightRule)
            filter_key: Key for filter rules in the configuration

        Returns:
            True if successful, False otherwise
        """
        return self.set(filter_key, rules)

    def log_initialization_message(self):
        """Log initialization message with current settings."""
        LOGD("SettingsManager: Application initialized with settings:")
        LOGD(f"  - Log directory: {self.get_log_directory()}")
        LOGD(f"  - Log level: {self.get_log_level()}")
        LOGD(f"  - Window geometry: {self.get_window_geometry()}")
