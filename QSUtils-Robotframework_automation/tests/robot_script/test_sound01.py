#!/usr/bin/env python3
"""
Test script to verify Sound01 device configuration with Sound BlasterX G6 microphone
"""

import sys
import os

# Add the robot-scripts-package to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

try:
    # Import the device settings
    from tests.robot_script.BTS_Device_Settings import Sound01

    print("Sound01 Device Configuration:")
    print(f"  Title: {Sound01.get('title', 'N/A')}")
    print(f"  Type: {Sound01.get('type', 'N/A')}")
    print(f"  Name: {Sound01.get('name', 'N/A')}")
    print(f"  Sound Device ID: {Sound01.get('sound_dev_id', 'N/A')}")
    print(f"  Connection Type: {Sound01.get('connection_type', 'N/A')}")
    print(f"  Connection Info: {Sound01.get('connection_info1', 'N/A')}")

    # Verify that the device is configured for Sound BlasterX G6
    expected_name = "마이크 (2- Sound BlasterX G6)"
    if Sound01.get("name") == expected_name:
        print("\n✓ Sound01 is correctly configured for Sound BlasterX G6 microphone")
    else:
        print(f"\n✗ Sound01 configuration mismatch!")
        print(f"  Expected: {expected_name}")
        print(f"  Actual: {Sound01.get('name')}")

    # Check if all required fields are present
    required_fields = [
        "title",
        "type",
        "name",
        "sound_dev_id",
        "connection_type",
        "connection_info1",
    ]
    missing_fields = [field for field in required_fields if field not in Sound01]

    if missing_fields:
        print(f"\n✗ Missing required fields: {missing_fields}")
    else:
        print("\n✓ All required fields are present")

    print("\nDevice is ready to use with BTS_Sound library for:")
    print("  - Audio recording from Sound BlasterX G6 microphone")
    print("  - TV mute detection")
    print("  - Sound quality verification")

except ImportError as e:
    print(f"Error importing device settings: {e}")
    print("Make sure the BTS_Device_Settings.py file exists in the correct location")
except Exception as e:
    print(f"Unexpected error: {e}")
