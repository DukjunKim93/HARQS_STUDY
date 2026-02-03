"""
UI Framework Widgets

This module contains reusable UI widgets for QSMonitor applications.
"""

# Import widget classes for easier access
from QSUtils.UIFramework.widgets.BaseDeviceWidget import BaseDeviceWidget
from QSUtils.UIFramework.widgets.BaseEventWidget import BaseEventWidget
from QSUtils.UIFramework.widgets.WiFiConfigDialog import WiFiConfigDialog

# Define what gets imported with "from UIFramework.widgets import *"
__all__ = [
    "BaseDeviceWidget",
    "BaseEventWidget",
    "WiFiConfigDialog",
]
