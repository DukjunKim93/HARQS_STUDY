#!/usr/bin/env python3

import sys
import os

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

from BTS.BTS_Sound import BTS_Sound
from tests.robot_script.BTS_Device_Settings import Sound01

# Create a BTS_Sound instance
sound = BTS_Sound()

# Set the device from the configuration
if Sound01.get("name"):
    sound.sound_set_device_name(Sound01["name"])
    print(f"Device set to: {Sound01['name']}")

# Get the current device name
current_device = sound.sound_get_device()
print(f"Current device name: '{current_device}'")

# Check if it matches what the test expects
expected_device = "마이크 (2- Sound BlasterX G6)"
print(f"Expected device name: '{expected_device}'")
print(f"Match: {current_device == expected_device}")
