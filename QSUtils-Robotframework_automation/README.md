# QSUtils

Q-Symphony Device Monitor - A tool for monitoring and managing Q-Symphony devices

## Description

QSUtils is a developer tool for monitoring and managing Q-Symphony devices. It provides core features needed for device development including ADB communication, real-time monitoring, and log analysis.

## Features

- **Device Monitoring**: Real-time Q-Symphony device status monitoring
- **ADB Integration**: 20+ device command execution system
- **Audio Log Analysis**: Audio log parsing and analysis
- **Audio Device Testing**: Sound BlasterX G6 microphone integration for TV mute detection
- **Network Management**: WiFi configuration and network interface management
- **AutoReboot**: Automatic reboot functionality
- **Modern GUI**: Intuitive interface based on PySide6

## Documentation

Comprehensive documentation for specific systems is available in the [docs/](docs/) directory:

- [Unified Dump & JFrog Integration Overview](docs/OVERVIEW.md)
- [Architecture & Components](docs/ARCHITECTURE.md)
- [JFrog Integration Details](docs/JFROG_INTEGRATION.md)
- [Event System](docs/EVENT_SYSTEM.md)
- [Path Strategies](docs/PATH_STRATEGY.md)

## Quick Start

```bash
# Install
./install.sh

# Run
qsmonitor          # Main monitoring app
qslogger          # Log viewer
```

### Installation Options

```bash
./install.sh              # Install (default)
./install.sh --uninstall   # Uninstall
./install.sh --force       # Force reinstall
./install.sh --help        # Help
```

## Architecture

```
QSUtils/
├── QSMonitor/              # Main monitoring application
│   ├── features/          # Monitoring feature modules
│   │   ├── DefaultMonitor/    # Basic device status monitoring
│   │   ├── NetworkMonitor/    # Network status monitoring
│   │   ├── SpeakerGrid/       # Speaker array monitoring
│   │   └── AutoReboot/        # Auto reboot functionality
│   ├── core/              # Core application logic
│   │   ├── CommandHandler.py
│   │   ├── DeviceCommandExecutor.py
│   │   └── Events.py
│   └── ui/                # UI components
│       ├── MainWindow.py
│       ├── DeviceWidget.py
│       └── DeviceWindow.py
├── QSLogger/              # Log viewer application
│   └── views/             # Log viewer UI components
├── ADBDevice/             # ADB device communication layer
│   ├── ADBDevice.py           # Individual device management
│   ├── ADBDeviceManager.py    # Multi-device management
│   ├── AudioLogParser.py      # Audio log parsing
│   └── DeviceLoggingManager.py
├── command/               # Device command execution system
│   ├── command_executor.py     # Command execution engine
│   ├── command_factory.py      # Command creation factory
│   ├── base_command.py         # Command base class
│   └── cmd_*.py               # 20+ specific command implementations
├── components/            # Reusable components
│   └── network/          # Network management components
├── UIFramework/           # UI framework and base classes
│   ├── base/             # Base UI components
│   ├── widgets/          # Reusable widgets
│   └── config/           # Configuration management
├── Utils/                 # Utility modules
│   ├── DateTimeUtils.py
│   ├── FileUtils.py
│   └── Logger.py
└── tests/                 # Test suite
```

## Development

### Setup
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Key Components

- **QSMonitor**: Main monitoring application
  - `DefaultMonitor`: Basic device status monitoring
  - `NetworkMonitor`: Network status monitoring
  - `SpeakerGrid`: Speaker array monitoring
  - `AutoReboot`: Auto reboot functionality

- **ADBDevice**: ADB communication layer
  - `ADBDeviceManager`: Multi-device management
  - `AudioLogParser`: Audio log parsing

- **Command**: Command execution system
  - `CommandExecutor`: Command execution engine
  - `CommandFactory`: Command creation factory
  - 20+ specific command implementations

## Dependencies

- **PySide6>=6.0.0** - GUI framework
- **pyudev** - Device event monitoring (Linux)
- **psutil>=5.0.0** - System utilities
- **PyYAML>=6.0** - Configuration file management
- **robotframework** - Automation framework for robotic process automation
- **robotframework-appiumlibrary** - Appium library for mobile testing with Robot Framework
- **xlwings** - Excel integration library
- **appium-python-client** - Appium client for mobile testing
- **opencv-python** - Computer vision library
- **numpy** - Numerical computing library
- **scikit-image** - Image processing library
- **requests** - HTTP library
- **bleak** - Bluetooth library
- **pycryptodome** - Cryptographic library
- **qdrant-client** - Vector database client
- **ffmpeg-python** - Python bindings for ffmpeg (audio processing)
- **noisereduce** - Audio noise reduction library
- **pydub** - Audio manipulation library

## Robot Scripts

The package includes a comprehensive set of robot framework scripts for automated testing. These scripts are organized in the `QSUtils.RobotScripts` package and can be used directly in robot framework test cases.

To use the robot scripts, install the robot dependencies:
```bash
pip install -e ".[robot]"
```

Then you can import and use the robot libraries in your test cases:
```robotframework
*** Settings ***
Library    QSUtils.RobotScripts.BTS.BTS_Mobile    ${Android01}
Library    QSUtils.RobotScripts.BTS.BTS_Excel
Library    QSUtils.RobotScripts.BTS.BTS_Video
```

### Test Execution Examples
To run specific test cases with spaces in their names, you need to either escape the spaces or wrap the test name in quotes:

```bash
# Running TV power control tests
python -m robot.run --test "tv_power_control.Power On TV" tests/robot_script/tv_power_control.robot
python -m robot.run --test tv_power_control.Power\ On\ TV tests/robot_script/tv_power_control.robot

# Running audio dB level tests
python -m robot.run --test "db_level_test.Display Audio dB Levels" tests/robot_script/db_level_test.robot
python -m robot.run --test "db_level_test.Compare Different Thresholds" tests/robot_script/db_level_test.robot
```

For more information about test execution and available test cases, please refer to the individual robot script files in the `tests/robot_script/` directory.

### Troubleshooting

If Robot Framework scripts are not working properly, you may need to manually copy the XML utility files:

```bash
cp -r robot-scripts-package/BTS/utility/xml .venv/lib/python3.12/site-packages/BTS/utility/
```

## Current Status

- **Version**: 1.2.0 (Stable)
- **Python**: 3.8+
- **Platform**: Windows, Linux, macOS

## License

MIT License - see LICENSE file for details.
