# -*- coding: utf-8 -*-
"""
Microphone Test Feature for QSMonitor
Provides functionality for testing microphone input, including interface selection
and real-time dB level monitoring.
"""

import os
import sys
import time
import subprocess
import threading
import tempfile
import numpy as np
from typing import List, Optional, Callable
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QLineEdit,
)

from QSUtils.Utils.Logger import LOGD, LOGE
from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.DumpManager.DumpTypes import DumpTriggeredBy


class MicrophoneTestFeature(QWidget):
    """
    Microphone test feature providing interface selection and real-time dB monitoring.
    """

    # Signal for updating dB level in UI thread
    db_level_updated = Signal(float)
    # Signal for updating device list in UI thread
    devices_updated = Signal(list)

    def __init__(self, parent: QWidget = None, device_context = None):
        """
        Initialize the microphone test feature.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext for accessing event manager and other services
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.device_context = device_context

        # Audio recording parameters
        self.recording_duration = 1.0  # seconds
        self.recording_interval = 0.5  # seconds
        self.sample_rate = 44100  # Hz
        self.channels = 2  # Stereo (more universally supported)

        # Recording state
        self.is_recording = False
        self.recording_thread = None
        self.stop_recording_event = threading.Event()

        # dB level tracking
        self.current_db_level = -100.0  # Initialize to very low level
        self.db_history = []  # Store recent dB levels for analysis
        self.max_history_size = 10  # Keep last 10 measurements

        # Threshold tracking
        self.threshold_db = -30.0  # Default threshold
        self.last_threshold_time = None  # Time when threshold was last met
        self.test_start_time = None  # Time when test started
        self.threshold_violation_logged = False  # Whether we've logged the violation

        # UI elements
        self.device_combo = None
        self.refresh_btn = None
        self.start_stop_btn = None
        self.db_progress_bar = None
        self.db_label = None
        self.status_text = None
        self.threshold_edit = None

        # Connect signals
        self.db_level_updated.connect(self._update_db_ui)
        self.devices_updated.connect(self._update_device_list)

        # Setup UI
        self._setup_ui()

        # Load available devices
        self._refresh_devices()

    def _setup_ui(self):
        """Setup the user interface for microphone testing."""
        layout = QVBoxLayout(self)

        # Device selection group
        device_group = QGroupBox("Microphone Interface Selection")
        device_layout = QHBoxLayout()
        
        device_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        device_layout.addWidget(self.device_combo)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_devices)
        device_layout.addWidget(self.refresh_btn)
        
        device_layout.addStretch()
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)

        # Test configuration group
        config_group = QGroupBox("Test Configuration")
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("Threshold dB:"))
        self.threshold_edit = QLineEdit("-30.0")
        self.threshold_edit.setValidator(QDoubleValidator(-100.0, 0.0, 2))
        self.threshold_edit.setMaximumWidth(100)
        config_layout.addWidget(self.threshold_edit)
        
        config_layout.addStretch()
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Monitoring group
        monitor_group = QGroupBox("Real-time dB Monitoring")
        monitor_layout = QVBoxLayout()
        
        # dB level display
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Current dB Level:"))
        self.db_label = QLabel("-100.00 dB")
        self.db_label.setMinimumWidth(100)
        db_layout.addWidget(self.db_label)
        db_layout.addStretch()
        monitor_layout.addLayout(db_layout)
        
        # Threshold timer display
        timer_layout = QHBoxLayout()
        timer_layout.addWidget(QLabel("Time since last threshold:"))
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setMinimumWidth(100)
        timer_layout.addWidget(self.timer_label)
        timer_layout.addStretch()
        monitor_layout.addLayout(timer_layout)
        
        # dB progress bar
        self.db_progress_bar = QProgressBar()
        self.db_progress_bar.setRange(-100, 0)  # dB range from -100 to 0
        self.db_progress_bar.setValue(-100)
        self.db_progress_bar.setFormat("Silence")
        monitor_layout.addWidget(self.db_progress_bar)
        
        # Start/Stop button
        button_layout = QHBoxLayout()
        self.start_stop_btn = QPushButton("Start Monitoring")
        self.start_stop_btn.clicked.connect(self._toggle_monitoring)
        button_layout.addWidget(self.start_stop_btn)
        button_layout.addStretch()
        monitor_layout.addLayout(button_layout)
        
        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # Status display
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Add stretch to push everything to the top
        layout.addStretch()

    def _refresh_devices(self):
        """Refresh the list of available audio input devices."""
        try:
            # Use arecord to list available devices
            result = subprocess.run(
                ["arecord", "-l"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            # Store device information as tuples (device_id, display_name)
            devices = []
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Parse device information
                    # Example: card 1: AT2020USB [AT2020USB+], device 0: USB Audio [USB Audio]
                    if line.startswith('card ') and 'device' in line and ':' in line:
                        # Extract card number
                        # Format: card X: NAME [FULL NAME], device Y: DESCRIPTION
                        parts = line.split(',')
                        if len(parts) >= 2:
                            # Extract card information from first part
                            card_part = parts[0]  # e.g., "card 1: AT2020USB [AT2020USB+]"
                            device_part = parts[1]  # e.g., " device 0: USB Audio [USB Audio]"
                            
                            # Extract card number
                            card_number = card_part.split(':')[0].replace('card ', '').strip()
                            
                            # Extract card name
                            if '[' in card_part and ']' in card_part:
                                card_name = card_part.split('[')[0].split(':', 1)[1].strip()
                            else:
                                card_name = card_part.split(':', 1)[1].strip()
                            
                            # Extract device number
                            device_number = device_part.split(':')[0].replace('device', '').strip()
                            
                            # Create device identifier in correct format: hw:card,device
                            device_id = f"hw:{card_number},{device_number}"
                            
                            # Create a more descriptive name for the device
                            display_name = f"{card_name} (hw:{card_number},{device_number})"
                            
                            # Store both the device ID and display name
                            devices.append((device_id, display_name))
            
            # Also check for default devices
            devices.append(("default", "Default Audio Device"))
            devices.append(("pulse", "PulseAudio Sound Server"))
            
            # Update UI in main thread with device tuples
            self.devices_updated.emit(devices)
            
        except Exception as e:
            LOGE(f"MicrophoneTestFeature: Error refreshing devices: {e}")
            self._log_status(f"Error refreshing devices: {e}")

    def _update_device_list(self, devices: List[tuple]):
        """Update the device combo box with available devices."""
        current_device = self.device_combo.currentData() if self.device_combo.count() > 0 else ""
        
        self.device_combo.clear()
        for device_id, display_name in devices:
            self.device_combo.addItem(display_name, device_id)
        
        # Restore previous selection if it still exists
        if current_device:
            index = self.device_combo.findData(current_device)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)

    def _toggle_monitoring(self):
        """Toggle microphone monitoring on/off."""
        if self.is_recording:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        """Start microphone monitoring."""
        if self.is_recording:
            return
            
        selected_device = self.device_combo.currentData()
        if not selected_device:
            QMessageBox.warning(self, "Microphone Test", "Please select a microphone device first.")
            return
            
        # Get threshold value from UI
        try:
            self.threshold_db = float(self.threshold_edit.text())
        except ValueError:
            self.threshold_db = -30.0  # Default value
            
        display_name = self.device_combo.currentText()
        self.is_recording = True
        self.start_stop_btn.setText("Stop Monitoring")
        self._log_status(f"Starting microphone monitoring on device: {display_name} ({selected_device})")
        self._log_status(f"Threshold set to: {self.threshold_db:.2f} dB")
        
        # Initialize test tracking variables
        self.test_start_time = time.time()
        self.last_threshold_time = self.test_start_time
        self.threshold_violation_logged = False
        
        # Start recording thread
        self.stop_recording_event.clear()
        self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.recording_thread.start()

    def _stop_monitoring(self):
        """Stop microphone monitoring."""
        if not self.is_recording:
            return
            
        self._log_status("Stopping microphone monitoring...")
        self.stop_recording_event.set()
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
            
        self.is_recording = False
        self.start_stop_btn.setText("Start Monitoring")
        self._log_status("Microphone monitoring stopped.")

    def _recording_loop(self):
        """Main recording loop running in a separate thread."""
        try:
            while not self.stop_recording_event.is_set():
                db_level = self._record_and_analyze()
                if db_level is not None:
                    # Update UI in main thread
                    self.db_level_updated.emit(db_level)
                
                # Wait for next recording interval
                if self.stop_recording_event.wait(self.recording_interval):
                    break
                    
        except Exception as e:
            LOGE(f"MicrophoneTestFeature: Error in recording loop: {e}")
            self._log_status(f"Error in recording loop: {e}")
        finally:
            self.is_recording = False

    def _record_and_analyze(self) -> Optional[float]:
        """Record audio and analyze dB level."""
        try:
            # Create temporary file for recording
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_filename = tmp_file.name
            
            selected_device = self.device_combo.currentData()
            
            # Record audio using arecord
            cmd = [
                "arecord",
                "-D", selected_device,
                "-f", "S16_LE",  # 16-bit signed little endian
                "-r", str(self.sample_rate),
                "-c", str(self.channels),
                "-d", str(int(self.recording_duration)),
                temp_filename
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.recording_duration + 2)
            
            if result.returncode != 0:
                LOGE(f"MicrophoneTestFeature: arecord failed: {result.stderr}")
                self._log_status(f"Recording failed: {result.stderr}")
                return None
                
            # Analyze the recorded audio file
            db_level = self._calculate_db_level(temp_filename)
            
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except Exception:
                pass
                
            return db_level
            
        except subprocess.TimeoutExpired:
            LOGE("MicrophoneTestFeature: Recording timed out")
            self._log_status("Recording timed out")
            return None
        except Exception as e:
            LOGE(f"MicrophoneTestFeature: Error recording/analyzing audio: {e}")
            self._log_status(f"Error: {e}")
            return None

    def _calculate_db_level(self, audio_file: str) -> Optional[float]:
        """Calculate dB level from audio file using pydub."""
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = AudioSegment.from_wav(audio_file)
            
            # Convert to raw samples
            samples = np.array(audio.get_array_of_samples())
            
            # Handle stereo to mono conversion if needed
            if audio.channels > 1:
                samples = samples.reshape((-1, audio.channels)).mean(axis=1)
            
            # Calculate RMS (Root Mean Square)
            if len(samples) == 0:
                return -100.0  # Very low dB for silence
            
            # Check for valid samples
            if not np.all(np.isfinite(samples)):
                return -100.0  # Invalid samples, treat as silence
                
            # Calculate RMS
            mean_square = np.mean(samples**2)
            if mean_square <= 0:
                return -100.0  # No energy, silence
            
            rms = np.sqrt(mean_square)
            
            # Convert to dBFS (dB Full Scale)
            # For 16-bit audio, max amplitude is 32767
            if rms > 0:
                max_amplitude = 32767
                dbfs = 20 * np.log10(rms / max_amplitude)
                return max(dbfs, -100.0)  # Clamp to -100 dB minimum
            else:
                return -100.0  # Silence
                
        except Exception as e:
            LOGE(f"MicrophoneTestFeature: Error calculating dB level: {e}")
            return None

    def _update_db_ui(self, db_level: float):
        """Update the UI with the current dB level."""
        self.current_db_level = db_level
        
        # Update dB label
        self.db_label.setText(f"{db_level:.2f} dB")
        
        # Update progress bar
        self.db_progress_bar.setValue(int(db_level))
        
        # Update progress bar format based on level
        if db_level < -60:
            self.db_progress_bar.setFormat("Silence")
        elif db_level < -40:
            self.db_progress_bar.setFormat("Very Low")
        elif db_level < -20:
            self.db_progress_bar.setFormat("Low")
        elif db_level < -10:
            self.db_progress_bar.setFormat("Medium")
        else:
            self.db_progress_bar.setFormat("High")
        
        # Add to history for analysis
        self.db_history.append(db_level)
        if len(self.db_history) > self.max_history_size:
            self.db_history.pop(0)
        
        # Check for silence (continuous low levels)
        if len(self.db_history) >= 5:
            avg_db = sum(self.db_history[-5:]) / 5
            if avg_db < -60:
                self._log_status("Silence detected (continuous low audio levels)")
        
        # Check threshold conditions if test is running
        if self.is_recording and self.test_start_time is not None:
            current_time = time.time()
            
            # Update timer display
            if self.last_threshold_time is not None:
                time_since_last_threshold = current_time - self.last_threshold_time
                # Convert to hours:minutes:seconds
                hours = int(time_since_last_threshold // 3600)
                minutes = int((time_since_last_threshold % 3600) // 60)
                seconds = int(time_since_last_threshold % 60)
                self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Check if current level meets threshold
            if db_level >= self.threshold_db:
                # Threshold met, update last threshold time
                self.last_threshold_time = current_time
                self.threshold_violation_logged = False
            else:
                # Threshold not met, check if it's been 3 minutes
                time_since_last_threshold = current_time - self.last_threshold_time
                time_since_test_start = current_time - self.test_start_time
                
                # If it's been 3 minutes since last threshold or 3 minutes since test start
                # and we haven't logged the violation yet
                if time_since_last_threshold >= 180 and not self.threshold_violation_logged:
                    self._log_status(f"Threshold not met for 3 minutes (current: {db_level:.2f} dB, threshold: {self.threshold_db:.2f} dB)")
                    self._log_status("Test failed - triggering dump upload")
                    self.threshold_violation_logged = True
                    
                    # Trigger dump upload
                    self._trigger_dump_upload()

    def _log_status(self, message: str):
        """Add a message to the status log."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        
        # Scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_widget(self) -> QWidget:
        """Get the widget for this feature."""
        return self

    def cleanup(self):
        """Clean up resources."""
        if self.is_recording:
            self._stop_monitoring()
            
    def _trigger_dump_upload(self):
        """Trigger dump upload when test fails."""
        try:
            # Log the trigger
            self._log_status("Triggering dump upload due to microphone test failure")
            
            # Check if we have device context and event manager
            if self.device_context and hasattr(self.device_context, 'event_manager'):
                # Emit DUMP_REQUESTED event with MANUAL trigger type
                # This follows the event-driven architecture and is the most efficient approach
                self.device_context.event_manager.emit_event(
                    CommonEventType.DUMP_REQUESTED,
                    {
                        "triggered_by": DumpTriggeredBy.MANUAL.value,
                        "upload_enabled": True  # Enable upload for this dump
                    }
                )
                self._log_status("Dump upload request sent via event system")
            else:
                # Fallback if device context is not available
                self._log_status("Dump upload triggered - this would normally upload diagnostic data")
            
        except Exception as e:
            LOGE(f"MicrophoneTestFeature: Error triggering dump upload: {e}")
            self._log_status(f"Error triggering dump upload: {e}")
