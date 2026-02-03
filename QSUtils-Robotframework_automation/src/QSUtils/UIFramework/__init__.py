"""
UI Framework Package

This package provides common UI components and base classes for applications.
"""

# Version info
__version__ = "1.0.0"
__author__ = "WaLyong Cho"

# Import base classes for easier access
from QSUtils.UIFramework.base.BaseMainWindow import BaseMainWindow
from QSUtils.UIFramework.base.BaseMonitor import BaseMonitorApplication
from QSUtils.UIFramework.base.MainController import MainController

# Define what gets imported with "from UIFramework import *"
__all__ = [
    "BaseMainWindow",
    "BaseMonitorApplication",
    "MainController",
]
