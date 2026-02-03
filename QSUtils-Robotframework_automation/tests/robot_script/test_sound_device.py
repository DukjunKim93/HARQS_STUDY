#!/usr/bin/env python3
"""
Test script to verify Sound01 device initialization with BTS_Sound library
"""

import sys
import os

# Add paths to find the modules
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package", "BTS"))

try:
    # Import the device settings
    from tests.robot_script.BTS_Device_Settings import Sound01

    # Import the BTS_Sound library
    from BTS.BTS_Sound import BTS_Sound

    print("Initializing Sound01 device with BTS_Sound library...")

    # Initialize the sound device
    sound_device = BTS_Sound(Sound01)

    # Get the device name
    device_name = sound_device.sound_get_device()
    print(f"Device name: {device_name}")

    # Verify that the device is correctly set
    expected_name = "마이크 (2- Sound BlasterX G6)"
    if device_name == expected_name:
        print("✓ Sound01 device successfully initialized with BTS_Sound library")
        print("✓ Device name matches expected Sound BlasterX G6 microphone")
    else:
        print(f"✗ Device name mismatch!")
        print(f"  Expected: {expected_name}")
        print(f"  Actual: {device_name}")

    # List available recording devices (this will help us understand what's available)
    print("\nChecking available recording devices...")
    try:
        devices = sound_device.get_record_devices_list()
        if devices:
            print(f"Found {len(devices)} recording devices:")
            for i, device in enumerate(devices):
                print(f"  {i}: {device}")
        else:
            print("No recording devices found")
    except Exception as e:
        print(f"Could not list recording devices: {e}")

    print("\nDevice is ready for:")
    print("  - Audio recording tests")
    print("  - TV mute detection")
    print("  - Sound quality verification")

except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure the required files exist in the correct locations")
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback

    traceback.print_exc()
