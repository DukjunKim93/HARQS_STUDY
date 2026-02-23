# -*- coding: utf-8 -*-
"""
Microphone Test Tab for QSMonitor
Provides a dedicated tab for microphone testing functionality.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout

from QSUtils.QSMonitor.features.MicrophoneTest.MicrophoneTestFeature import MicrophoneTestFeature
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.base.CommandHandler import CommandHandler


class MicrophoneTestTab(QWidget):
    """
    Microphone test tab providing interface selection and real-time dB monitoring.
    """

    def __init__(
        self,
        parent: QWidget,
        device_context: DeviceContext,
        command_handler: CommandHandler
    ):
        """
        Initialize the microphone test tab.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext instance for device management
            command_handler: CommandHandler for executing commands
        """
        super().__init__(parent)
        
        self.device_context = device_context
        self.command_handler = command_handler
        
        # Setup UI
        self._setup_ui()
        
        # Register with device context
        self.device_context.register_app_component("microphone_test_tab", self)

    def _setup_ui(self):
        """Setup the user interface for the microphone test tab."""
        layout = QVBoxLayout(self)
        
        # Create and add the microphone test feature widget
        self.microphone_test_feature = MicrophoneTestFeature(self, self.device_context)
        layout.addWidget(self.microphone_test_feature.get_widget())
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.setLayout(layout)

    def get_widget(self) -> QWidget:
        """Get the widget for this tab."""
        return self

    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, "microphone_test_feature") and self.microphone_test_feature:
                self.microphone_test_feature.cleanup()
        except Exception:
            pass

    def apply_session_state(self, enabled: bool):
        """
        Apply session state to the tab.
        
        Args:
            enabled: Whether the session is enabled
        """
        # The microphone test feature operates independently of session state
        pass

    def set_enabled(self, enabled: bool):
        """
        Enable or disable the tab.
        
        Args:
            enabled: Whether to enable the tab
        """
        # The microphone test feature operates independently
        pass
