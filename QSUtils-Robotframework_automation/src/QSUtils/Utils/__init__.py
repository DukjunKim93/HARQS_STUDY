"""
QSMonitor utilities package.

This package contains enhanced utility modules for ADB device management,
audio log parsing, file operations, and logging functionality.

The package provides:
- Enhanced logging with singleton pattern and configurable handlers
- Platform-independent file operations with strategy pattern
- File management utilities with comprehensive error handling
- Timestamp generation utilities
- Context managers for safe file operations
"""

# Version info
__version__ = "1.2.0"
__author__ = "WaLyong Cho"

# Import datetime utilities
from QSUtils.Utils.DateTimeUtils import TimestampGenerator

# Import file utilities
from QSUtils.Utils.FileUtils import (
    FileOperationResult,
    FileManager,
    get_file_manager,
    open_file_browser,
    ensure_directory_exists,
)

# Import logging utilities
from QSUtils.Utils.Logger import (
    Logger,
    LogLevel,
    LogConfig,
    get_logger,
    set_log_level,
    LOGD,
    LOGI,
    LOGW,
    LOGE,
    LOGC,
    LOGEX,
)

# Define what gets imported with "from Utils import *"
__all__ = [
    # Logging
    "Logger",
    "LogLevel",
    "LogConfig",
    "get_logger",
    "set_log_level",
    "LOGD",
    "LOGI",
    "LOGW",
    "LOGE",
    "LOGC",
    "LOGEX",
    # File operations
    "FileOperationResult",
    "FileManager",
    "get_file_manager",
    "open_file_browser",
    "ensure_directory_exists",
    # DateTime utilities
    "TimestampGenerator",
]

# Package-level documentation
"""
Enhanced Utils Package for QSMonitor
=====================================

This package provides comprehensive utilities for the QSMonitor application
with improved architecture, error handling, and maintainability.

Logging Features:
- Singleton pattern for global logger instance
- Configurable log levels and formats
- Multiple handler support (console, file)
- Rotating file logs with size limits
- Thread-safe logging operations
- Backward compatibility with legacy functions

File Operations Features:
- Platform-independent file browser opening
- Strategy pattern for OS-specific operations
- Comprehensive error handling with result objects
- Context managers for safe file operations
- File management utilities (copy, delete, list, size)
- Timestamp generation utilities
- Directory creation and validation
- Log file path generation with timestamps

Usage Examples:
--------------
# Logging
from Utils import get_logger, LogLevel, LogConfig

logger = get_logger()
logger.debug("Debug message")
logger.info("Info message")

# Configure logging
config = LogConfig(
    level=LogLevel.DEBUG,
    enable_file=True,
    file_path="/path/to/logfile.log"
)
logger.configure(config)

# File operations
from Utils import get_file_manager, FileOperationResult

file_manager = get_file_manager()
result = file_manager.open_file_browser("/path/to/directory")
if result.success:
    print("Success:", result.message)
else:
    print("Error:", result.message)

# Safe file writing
with file_manager.safe_file_write("/path/to/file.txt") as f:
    f.write("Hello, World!")

# Legacy compatibility (still supported)
from Utils import LOGI, LOGE, open_file_browser
LOGI("This still works!")
success = open_file_browser("/path/to/directory")

Architecture:
------------
The package follows SOLID principles with:
- Single Responsibility: Each class has a clear, single purpose
- Open/Closed: Easy to extend with new strategies or handlers
- Liskov Substitution: Strategy implementations are interchangeable
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: High-level modules don't depend on low-level details

Error Handling:
--------------
All operations return FileOperationResult objects with:
- success: Boolean indicating operation success
- message: Descriptive message about the operation
- data: Operation result data (if applicable)
- error: Exception object (if operation failed)

This provides consistent error handling and detailed feedback
for all file and logging operations.
"""
