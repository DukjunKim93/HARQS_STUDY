# BTS Package Installation Guide

## Overview

The BTS (Broadcast Testing System) packages are installed as part of the robot-scripts-package installation. There are two main BTS-related packages installed in the virtual environment:

1. **BTS** - Main testing framework with various device control libraries
2. **BTSReferenceEditor** - Reference editor for managing test references

## Installation Process

### 1. Package Structure

The BTS packages are located in the `robot-scripts-package/` directory:

```
robot-scripts-package/
├── BTS/                    # Main BTS libraries
│   ├── BTS_Sound.py        # Audio testing library (modified for Linux)
│   ├── BTS_ATHub.py        # ATHub device control
│   ├── BTS_Sdb.py          # SDB (Samsung Debug Bridge) interface
│   ├── BTS_Video.py        # Video capture and analysis
│   ├── BTS_WebCam.py       # Webcam control
│   └── ...                 # Many other device control libraries
├── BTSReferenceEditor/     # Reference editor tools
│   ├── ReferenceEditor.py
│   └── ...                 # Reference management tools
└── setup.py               # Package setup configuration
```

### 2. Installation Command

The BTS packages are installed using pip in editable mode:

```bash
# Install the robot-scripts package (includes BTS packages)
pip install -e robot-scripts-package/
```

This command:
- Installs the `qsutils-robot-scripts` package in editable mode
- Copies the BTS and BTSReferenceEditor directories to the virtual environment
- Makes the packages available for import in Python scripts

### 3. Installed Location

After installation, the packages are available in the virtual environment:

```
.venv/lib/python3.12/site-packages/
├── BTS/                    # Installed BTS libraries
│   ├── BTS_Sound.py        # Audio testing library
│   └── ...                 # All other BTS libraries
├── BTSReferenceEditor/     # Reference editor tools
└── qsutils_robot_scripts.egg-link  # Editable installation link
```

## Package Dependencies

The BTS packages require several system and Python dependencies:

### System Dependencies
- **ffmpeg** - Audio/video processing (for BTS_Sound)
- **sox** - Audio processing (for BTS_Sound)
- **zbar** - QR code scanning

### Python Dependencies
The main dependencies are specified in `robot-scripts-package/setup.py`:

```python
install_requires=[
    "robotframework",
    "xlwings",
    "appium-python-client",
    "opencv-python",
    "numpy",
    "scikit-image",
    "requests",
    "bleak",
    "pycryptodome",
    "qdrant-client",
    "wakeonlan",
    "getmac",
    "imagehash",
    "pyzbar",
    "pyqrcode",
    "matplotlib",
    "pytesseract",
    "aiohttp",
    # Audio-related dependencies (added for Sound01 functionality)
    "ffmpeg-python",
    "noisereduce",
    "pydub",
    # Serial communication dependency
    "pyserial",
]
```

## Audio Package Modifications

For the Sound01 device functionality, specific modifications were made to:

### 1. BTS_Sound.py
- Modified to use Linux-compatible audio capture methods
- Updated device listing to use PulseAudio/ALSA commands
- Changed recording commands to use PulseAudio format
- Maintained Windows compatibility with conditional code paths

### 2. Device Configuration
- Updated Sound01 device name from Korean text to proper PulseAudio identifier
- Changed to: `alsa_input.usb-Creative_Technology_Ltd_Sound_BlasterX_G6_D800544758X-00.analog-stereo`

## Usage Examples

### Importing BTS Libraries
```python
# Import BTS Sound library
from BTS.BTS_Sound import BTS_Sound

# Import device settings
from tests.robot_script.BTS_Device_Settings import Sound01

# Initialize and use
sound_device = BTS_Sound(Sound01)
sound_device.sound_record("10s", "/tmp/recording.wav")
```

### Robot Framework Usage
```robotframework
*** Settings ***
Library    BTS.BTS_Sound    WITH NAME    SoundSensor

*** Test Cases ***
Record Audio
    SoundSensor.Sound Record    10s    ${record_file}
    SoundSensor.Sound Is Mute    ${record_file}
```

## Troubleshooting

### 1. Package Not Found
If BTS packages are not available:
```bash
# Reinstall the robot-scripts package
pip install -e robot-scripts-package/
```

### 2. Audio Device Issues
Ensure system dependencies are installed:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg sox libzbar0

# Check if devices are recognized
pactl list sources short
arecord -l
```

### 3. Device Configuration
Verify Sound01 device configuration in:
- `tests/robot_script/BTS_Device_Settings.py`
- `tests/robot_script/BTS_Device_Settings.ini`

The device name should match the actual PulseAudio device identifier.
