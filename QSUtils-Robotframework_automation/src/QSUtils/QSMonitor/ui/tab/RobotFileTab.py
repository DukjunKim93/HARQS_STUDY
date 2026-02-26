# -*- coding: utf-8 -*-
"""
Robot File Tab for QSMonitor
Provides a dedicated tab for loading and executing .robot files with drag-and-drop reordering of test cases.
"""

import os
import re
import json
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QFileDialog, QLabel, QGroupBox, QMessageBox,
    QTextEdit, QSpinBox, QAbstractItemView, QMenu, QApplication
)
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag, QKeyEvent, QAction

from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.base.CommandHandler import CommandHandler
from QSUtils.Utils.Logger import LOGD


class TestCaseItem(QListWidgetItem):
    """Custom QListWidgetItem for test cases with repeat count"""
    
    def __init__(self, test_case_name: str, repeat_count: int = 1):
        super().__init__()
        self.test_case_name = test_case_name
        self.repeat_count = repeat_count
        self._update_text()
        
    def _update_text(self):
        """Update the display text with repeat count"""
        self.setText(f"{self.test_case_name} (x{self.repeat_count})")
        
    def set_repeat_count(self, count: int):
        """Set the repeat count and update display"""
        self.repeat_count = count
        self._update_text()


class DraggableListWidget(QListWidget):
    """Custom QListWidget with drag-and-drop functionality"""
    
    item_reordered = Signal(int, int)  # source_row, target_row
    delete_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setAcceptDrops(True)
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events for deletion"""
        if event.key() == Qt.Key.Key_Delete:
            self.delete_requested.emit()
        else:
            super().keyPressEvent(event)
            
    def dropEvent(self, event):
        """Handle drop events to implement custom reordering logic"""
        # Get the source row
        source_row = self.currentRow()
        
        # Call the parent drop event to perform the move
        super().dropEvent(event)
        
        # Get the target row
        target_row = self.currentRow()
        
        # Emit a signal to notify about the reordering
        if source_row != target_row:
            self.item_reordered.emit(source_row, target_row)


class RobotFileTab(QWidget):
    """
    Robot file tab providing interface for loading .robot files and reordering test cases.
    """

    def __init__(
        self,
        parent: QWidget,
        device_context: DeviceContext,
        command_handler: CommandHandler
    ):
        """
        Initialize the robot file tab.

        Args:
            parent: Parent Qt widget
            device_context: DeviceContext instance for device management
            command_handler: CommandHandler for executing commands
        """
        super().__init__(parent)
        
        self.device_context = device_context
        self.command_handler = command_handler
        self.current_robot_file = None
        self.test_cases = []  # List of test case names
        self.test_case_items = []  # List of TestCaseItem objects
        
        # Setup UI
        self._setup_ui()
        
        # Register with device context
        self.device_context.register_app_component("robot_file_tab", self)

    def _setup_ui(self):
        """Setup the user interface for the robot file tab."""
        layout = QVBoxLayout(self)
        
        # File selection group
        file_group = QGroupBox("Robot File Selection")
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.load_button = QPushButton("Load Robot File")
        self.load_button.clicked.connect(self._load_robot_file)
        
        self.save_config_button = QPushButton("Save Config")
        self.save_config_button.clicked.connect(self._save_config)
        self.save_config_button.setEnabled(False)
        
        self.load_config_button = QPushButton("Load Config")
        self.load_config_button.clicked.connect(self._load_config)
        
        self.execute_button = QPushButton("Execute Selected TCs")
        self.execute_button.clicked.connect(self._execute_test_cases)
        self.execute_button.setEnabled(False)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.load_button)
        file_layout.addWidget(self.save_config_button)
        file_layout.addWidget(self.load_config_button)
        file_layout.addWidget(self.execute_button)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Test cases group
        tc_group = QGroupBox("Test Cases (Drag to Reorder, Del to Remove)")
        tc_layout = QVBoxLayout()
        
        self.test_case_list = DraggableListWidget()
        self.test_case_list.item_reordered.connect(self._on_test_case_reordered)
        self.test_case_list.delete_requested.connect(self._delete_selected_items)
        self.test_case_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.test_case_list.customContextMenuRequested.connect(self._show_context_menu)
        
        tc_layout.addWidget(self.test_case_list)
        tc_group.setLayout(tc_layout)
        layout.addWidget(tc_group)
        
        # Repeat count controls
        repeat_group = QGroupBox("Repeat Count")
        repeat_layout = QHBoxLayout()
        
        repeat_layout.addWidget(QLabel("Selected TC Repeat Count:"))
        self.repeat_spinbox = QSpinBox()
        self.repeat_spinbox.setMinimum(1)
        self.repeat_spinbox.setMaximum(1000)
        self.repeat_spinbox.setValue(1)
        self.repeat_spinbox.valueChanged.connect(self._on_repeat_count_changed)
        repeat_layout.addWidget(self.repeat_spinbox)
        
        self.apply_repeat_button = QPushButton("Apply to Selected")
        self.apply_repeat_button.clicked.connect(self._apply_repeat_count)
        repeat_layout.addWidget(self.apply_repeat_button)
        
        repeat_group.setLayout(repeat_layout)
        layout.addWidget(repeat_group)
        
        # Output console
        console_group = QGroupBox("Output Console")
        console_layout = QVBoxLayout()
        
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setMaximumHeight(150)
        console_layout.addWidget(self.output_console)
        
        console_group.setLayout(console_layout)
        layout.addWidget(console_group)
        
        self.setLayout(layout)

    def _show_context_menu(self, position):
        """Show context menu for test case list"""
        menu = QMenu()
        delete_action = QAction("Delete Selected", self)
        delete_action.triggered.connect(self._delete_selected_items)
        menu.addAction(delete_action)
        menu.exec(self.test_case_list.mapToGlobal(position))

    def _delete_selected_items(self):
        """Delete selected test case items"""
        selected_items = self.test_case_list.selectedItems()
        if not selected_items:
            return
            
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Delete Test Cases", 
            f"Are you sure you want to delete {len(selected_items)} test case(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove items in reverse order to maintain indices
            for item in selected_items:
                row = self.test_case_list.row(item)
                self.test_case_list.takeItem(row)
                if row < len(self.test_case_items):
                    self.test_case_items.pop(row)
            self._update_test_cases_list()

    def _load_robot_file(self):
        """Load a .robot file and extract test cases."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Robot File", "", "Robot Files (*.robot)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Extract test cases using regex
            # Look for test case section and extract test case names
            test_cases = self._extract_test_cases(content)
            
            if not test_cases:
                QMessageBox.warning(self, "No Test Cases", "No test cases found in the selected file.")
                return
                
            # Update UI
            self.current_robot_file = file_path
            self.test_cases = test_cases
            self.file_label.setText(f"File: {os.path.basename(file_path)}")
            self.execute_button.setEnabled(True)
            self.save_config_button.setEnabled(True)
            
            # Populate the list with default repeat count of 1
            self.test_case_list.clear()
            self.test_case_items = []
            for tc_name in test_cases:
                item = TestCaseItem(tc_name, 1)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make non-editable
                self.test_case_list.addItem(item)
                self.test_case_items.append(item)
                
            self.output_console.append(f"Loaded {len(test_cases)} test cases from {os.path.basename(file_path)}")
            LOGD(f"RobotFileTab: Loaded {len(test_cases)} test cases from {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load robot file: {str(e)}")
            self.output_console.append(f"Error loading robot file: {str(e)}")
            LOGD(f"RobotFileTab: Error loading robot file: {e}")

    def _extract_test_cases(self, content: str) -> List[str]:
        """
        Extract test case names from robot file content.
        
        Args:
            content: Content of the robot file
            
        Returns:
            List of test case names
        """
        test_cases = []
        
        # Find the Test Cases section
        test_cases_section = re.search(
            r'\*{3}\s*Test Cases\s*\*{3}.*?(?=\*{3}|\Z)', 
            content, 
            re.DOTALL | re.IGNORECASE
        )
        
        if not test_cases_section:
            return test_cases
            
        section_content = test_cases_section.group(0)
        
        # Extract test case names (lines that are not comments, settings, or empty)
        lines = section_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Skip section header line
            if line.lower().startswith('*** test cases ***'):
                i += 1
                continue
                
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                i += 1
                continue
                
            # Skip documentation, tags, setup, teardown lines
            if (line.lower().startswith('[documentation]') or 
                line.lower().startswith('[tags]') or 
                line.lower().startswith('[setup]') or 
                line.lower().startswith('[teardown]') or
                line.lower().startswith('[template]') or
                line.lower().startswith('[timeout]')):
                # Skip the next line if it's a continuation
                i += 1
                while i < len(lines) and (lines[i].startswith('    ') or lines[i].startswith('\t')):
                    i += 1
                continue
                
            # If line doesn't start with space or tab, and is not a setting, it's a test case name
            if (not line.startswith(' ') and 
                not line.startswith('\t') and 
                line and 
                not line.startswith('[') and
                not line.lower().startswith('test template')):
                # Clean the test case name (remove trailing comments)
                tc_name = line.split('  ')[0].split('\t')[0].strip()
                if tc_name:
                    test_cases.append(tc_name)
                    
            i += 1
            
        return test_cases

    def _on_test_case_reordered(self, source_row: int, target_row: int):
        """
        Handle test case reordering.
        
        Args:
            source_row: Original position of the item
            target_row: New position of the item
        """
        # Update our internal test_case_items list to match the new order
        if (0 <= source_row < len(self.test_case_items) and 
            0 <= target_row < len(self.test_case_items)):
            # Move the test case item from source to target position
            moved_item = self.test_case_items.pop(source_row)
            self.test_case_items.insert(target_row, moved_item)
            
            self.output_console.append(f"Test case reordered from position {source_row} to {target_row}")
            LOGD(f"RobotFileTab: Test case reordered from {source_row} to {target_row}")

    def _on_repeat_count_changed(self, value: int):
        """Handle repeat count spinbox changes"""
        # This is just for the UI, actual application happens when Apply button is clicked
        pass

    def _apply_repeat_count(self):
        """Apply repeat count to selected items"""
        selected_items = self.test_case_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select test cases to apply repeat count.")
            return
            
        repeat_count = self.repeat_spinbox.value()
        for item in selected_items:
            if isinstance(item, TestCaseItem):
                item.set_repeat_count(repeat_count)
                
        self.output_console.append(f"Applied repeat count {repeat_count} to {len(selected_items)} test case(s)")

    def _update_test_cases_list(self):
        """Update the internal test cases list from the UI items"""
        self.test_cases = [item.test_case_name for item in self.test_case_items]

    def _execute_test_cases(self):
        """Execute the selected test cases in order."""
        if not self.current_robot_file or not self.test_case_items:
            return
            
        # Build execution plan with repeat counts
        execution_plan = []
        for item in self.test_case_items:
            for _ in range(item.repeat_count):
                execution_plan.append(item.test_case_name)
        
        # Execute the robot test cases
        self.output_console.append(f"Starting execution of {len(execution_plan)} test case instances...")
        self.output_console.append("=" * 50)
        
        try:
            import subprocess
            import os
            import threading
            from PySide6.QtCore import QTimer
            
            # Get the directory of the robot file
            robot_dir = os.path.dirname(self.current_robot_file)
            
            # Create a temporary robot file with only the selected test cases in the same directory
            temp_robot_file = os.path.join(robot_dir, "temp_test.robot")
            
            # Read the original robot file
            with open(self.current_robot_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Extract the test cases section
            test_cases_section = re.search(
                r'(\*{3}\s*Test Cases\s*\*{3}.*?)(?=\*{3}|\Z)', 
                original_content, 
                re.DOTALL | re.IGNORECASE
            )
            
            if not test_cases_section:
                raise Exception("Could not find Test Cases section")
            
            # Get the part before test cases
            before_test_cases = original_content[:test_cases_section.start(1)]
            
            # Build new test cases section with only selected test cases
            new_test_cases_content = "*** Test Cases ***\n"
            
            # Parse all test cases to find the ones we want
            all_test_cases = self._parse_all_test_cases(original_content)
            
            # Add only the selected test cases in order
            for tc_name in execution_plan:
                if tc_name in all_test_cases:
                    new_test_cases_content += all_test_cases[tc_name] + "\n\n"
            
            # Create the new content
            new_content = before_test_cases + new_test_cases_content
            
            # Write to temporary file in the same directory as the original robot file
            with open(temp_robot_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Execute robot with real-time output streaming
            self.output_console.append(f"Executing: robot {os.path.basename(temp_robot_file)}")
            self.output_console.append(f"Working directory: {robot_dir}")
            self.output_console.append("-" * 50)
            
            # Disable buttons during execution
            self.execute_button.setEnabled(False)
            self.load_button.setEnabled(False)
            self.save_config_button.setEnabled(False)
            self.load_config_button.setEnabled(False)
            
            # Function to run robot command with real-time output
            def run_robot_command():
                try:
                    # Run robot command with real-time output and timeout
                    process = subprocess.Popen(
                        ['robot', '--loglevel', 'DEBUG', '--consolecolors', 'off', '--nostatusrc', '--outputdir', '.', os.path.basename(temp_robot_file)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=robot_dir,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Store output lines to be processed in batches
                    output_lines = []
                    
                    # Read output in real-time with timeout handling
                    while True:
                        try:
                            # Use a small timeout to prevent hanging
                            output = process.stdout.readline()
                            if output == '' and process.poll() is not None:
                                break
                            if output:
                                output_lines.append(output.strip())
                                # Update UI in batches to avoid too many Qt calls
                                if len(output_lines) >= 5:
                                    # Use QTimer to safely update UI from thread
                                    def update_ui_batch(lines):
                                        for line in lines:
                                            self.output_console.append(line)
                                    QTimer.singleShot(0, lambda lines=output_lines[:]: update_ui_batch(lines))
                                    output_lines.clear()
                        except Exception as e:
                            # Handle read errors
                            break
                    
                    # Process remaining output lines
                    if output_lines:
                        def update_ui_remaining(lines):
                            for line in lines:
                                self.output_console.append(line)
                        QTimer.singleShot(0, lambda lines=output_lines: update_ui_remaining(lines))
                    
                    # Read any remaining stderr output
                    try:
                        stderr_output = process.stderr.read()
                        if stderr_output:
                            QTimer.singleShot(0, lambda err=stderr_output: self.output_console.append(f"STDERR: {err}"))
                    except Exception as e:
                        QTimer.singleShot(0, lambda err=str(e): self.output_console.append(f"Error reading stderr: {err}"))
                    
                    # Get return code with timeout
                    try:
                        return_code = process.poll()
                        if return_code is None:
                            # Process is still running, terminate it
                            process.terminate()
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
                            return_code = -1
                            QTimer.singleShot(0, lambda: self.output_console.append("Process terminated due to timeout"))
                    except Exception as e:
                        return_code = -1
                        QTimer.singleShot(0, lambda err=str(e): self.output_console.append(f"Error getting return code: {err}"))
                    
                    # Clean up temporary file
                    try:
                        os.remove(temp_robot_file)
                    except Exception as e:
                        QTimer.singleShot(0, lambda err=str(e): self.output_console.append(f"Warning: Could not clean up temp file: {err}"))
                    
                    # Re-enable buttons and show final message
                    def finalize_execution():
                        self.execute_button.setEnabled(True)
                        self.load_button.setEnabled(True)
                        self.save_config_button.setEnabled(True)
                        self.load_config_button.setEnabled(True)
                        self.output_console.append("=" * 50)
                        self.output_console.append(f"Execution completed with return code: {return_code}")
                        self.output_console.append("Execution finished")
                    
                    QTimer.singleShot(0, finalize_execution)
                    
                except Exception as e:
                    # Re-enable buttons and show error
                    def handle_error(error_msg):
                        self.execute_button.setEnabled(True)
                        self.load_button.setEnabled(True)
                        self.save_config_button.setEnabled(True)
                        self.load_config_button.setEnabled(True)
                        self.output_console.append(f"Error during execution: {error_msg}")
                        LOGD(f"RobotFileTab: Error executing test cases: {error_msg}")
                    
                    QTimer.singleShot(0, lambda msg=str(e): handle_error(msg))
            
            # Run the robot command in a separate thread to avoid blocking the UI
            thread = threading.Thread(target=run_robot_command)
            thread.daemon = True
            thread.start()
                
        except Exception as e:
            # Re-enable buttons
            self.execute_button.setEnabled(True)
            self.load_button.setEnabled(True)
            self.save_config_button.setEnabled(True)
            self.load_config_button.setEnabled(True)
            
            self.output_console.append(f"Error during execution: {str(e)}")
            LOGD(f"RobotFileTab: Error executing test cases: {e}")

    def _parse_all_test_cases(self, content: str) -> Dict[str, str]:
        """
        Parse all test cases from robot file content.
        
        Args:
            content: Content of the robot file
            
        Returns:
            Dictionary mapping test case names to their full content
        """
        test_cases = {}
        
        # Find the Test Cases section
        test_cases_section = re.search(
            r'\*{3}\s*Test Cases\s*\*{3}.*?(?=\*{3}|\Z)', 
            content, 
            re.DOTALL | re.IGNORECASE
        )
        
        if not test_cases_section:
            return test_cases
            
        section_content = test_cases_section.group(0)
        
        # Split by lines and parse test cases
        lines = section_content.split('\n')
        current_test_case = None
        current_content = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped_line = line.lstrip()  # Only strip left to preserve indentation
            
            # Skip section header line
            if stripped_line.lower().startswith('*** test cases ***'):
                i += 1
                continue
            
            # Check if this is a new test case (doesn't start with space or tab)
            if (stripped_line and 
                not line.startswith(' ') and 
                not line.startswith('\t') and 
                not stripped_line.startswith('[') and
                not stripped_line.lower().startswith('[documentation]') and
                not stripped_line.lower().startswith('[tags]') and
                not stripped_line.lower().startswith('[setup]') and
                not stripped_line.lower().startswith('[teardown]') and
                not stripped_line.lower().startswith('[template]') and
                not stripped_line.lower().startswith('[timeout]') and
                not stripped_line.lower().startswith('test template')):
                
                # Save previous test case if exists
                if current_test_case:
                    test_cases[current_test_case] = '\n'.join(current_content).rstrip()
                
                # Start new test case
                current_test_case = stripped_line.split('  ')[0].split('\t')[0].strip()
                current_content = [line]  # Include the original line with formatting
            elif current_test_case:
                # Add line to current test case
                current_content.append(line)
            
            i += 1
        
        # Save the last test case
        if current_test_case:
            test_cases[current_test_case] = '\n'.join(current_content).rstrip()
            
        return test_cases

    def _save_config(self):
        """Save test case configuration to a file"""
        if not self.test_case_items:
            QMessageBox.warning(self, "No Test Cases", "No test cases to save.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "JSON Files (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            config = {
                "robot_file": self.current_robot_file,
                "test_cases": [
                    {
                        "name": item.test_case_name,
                        "repeat_count": item.repeat_count
                    }
                    for item in self.test_case_items
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            self.output_console.append(f"Configuration saved to {os.path.basename(file_path)}")
            LOGD(f"RobotFileTab: Configuration saved to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
            self.output_console.append(f"Error saving configuration: {str(e)}")
            LOGD(f"RobotFileTab: Error saving configuration: {e}")

    def _load_config(self):
        """Load test case configuration from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON Files (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Load robot file if specified
            robot_file = config.get("robot_file")
            if robot_file and os.path.exists(robot_file):
                self.current_robot_file = robot_file
                self.file_label.setText(f"File: {os.path.basename(robot_file)}")
            else:
                QMessageBox.warning(self, "File Not Found", "Robot file not found. Loading test cases only.")
                
            # Load test cases
            test_case_configs = config.get("test_cases", [])
            self.test_case_list.clear()
            self.test_case_items = []
            
            for tc_config in test_case_configs:
                name = tc_config.get("name", "")
                repeat_count = tc_config.get("repeat_count", 1)
                item = TestCaseItem(name, repeat_count)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.test_case_list.addItem(item)
                self.test_case_items.append(item)
                
            self._update_test_cases_list()
            self.execute_button.setEnabled(True)
            self.save_config_button.setEnabled(True)
            
            self.output_console.append(f"Configuration loaded from {os.path.basename(file_path)}")
            LOGD(f"RobotFileTab: Configuration loaded from {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")
            self.output_console.append(f"Error loading configuration: {str(e)}")
            LOGD(f"RobotFileTab: Error loading configuration: {e}")

    def get_widget(self) -> QWidget:
        """Get the widget for this tab."""
        return self

    def cleanup(self):
        """Clean up resources."""
        try:
            # No specific cleanup needed for now
            pass
        except Exception:
            pass

    def apply_session_state(self, enabled: bool):
        """
        Apply session state to the tab.
        
        Args:
            enabled: Whether the session is enabled
        """
        # Enable/disable UI elements based on session state
        self.load_button.setEnabled(enabled)
        self.load_config_button.setEnabled(enabled)
        self.execute_button.setEnabled(enabled and self.current_robot_file is not None)
        self.save_config_button.setEnabled(enabled and self.test_case_items)

    def set_enabled(self, enabled: bool):
        """
        Enable or disable the tab.
        
        Args:
            enabled: Whether to enable the tab
        """
        self.apply_session_state(enabled)
