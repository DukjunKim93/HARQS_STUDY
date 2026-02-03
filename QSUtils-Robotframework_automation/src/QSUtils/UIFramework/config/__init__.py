"""
UI Framework Configuration

This module provides configuration management for UI framework components.
"""

from QSUtils.UIFramework.config.SettingsManager import SettingsManager

# Import configuration classes for easier access
from QSUtils.UIFramework.config.app_settings import AppSettings, WindowGeometry

# Define what gets imported with "from UIFramework.config import *"
__all__ = [
    "AppSettings",
    "WindowGeometry",
    "SettingsManager",
]
