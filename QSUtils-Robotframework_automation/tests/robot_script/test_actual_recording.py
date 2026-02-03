#!/usr/bin/env python3
"""
Test script to verify actual audio recording functionality with Sound01 device
"""

import sys
import os
import time

# Add paths to find the modules
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package", "BTS"))
sys.path.append(
    os.path.join(
        os.path.dirname(__file__), ".venv", "lib", "python3.12", "site-packages"
    )
)

try:
    # Import the device settings
    from tests.robot_script.BTS_Device_Settings import Sound01

    # Import the BTS_Sound library
    from BTS.BTS_Sound import BTS_Sound

    print("=== Testing Sound01 Device Recording Functionality ===\n")

    # Initialize the sound device
    print("1. Initializing Sound01 device...")
    sound_device = BTS_Sound(Sound01)

    # Get the device name
    device_name = sound_device.sound_get_device()
    print(f"   Device name: {device_name}")

    # List available recording devices
    print("\n2. Checking available recording devices...")
    try:
        devices = sound_device.get_record_devices_list()
        if devices:
            print(f"   Found {len(devices)} recording devices:")
            for i, device in enumerate(devices):
                print(f"     {i}: {device}")
        else:
            print("   No recording devices found")
    except Exception as e:
        print(f"   Error listing devices: {e}")

    # Test short recording
    print("\n3. Testing 5-second audio recording...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    record_file = f"/tmp/test_recording_{timestamp}.wav"

    try:
        print(f"   Recording to: {record_file}")
        # Record 5 seconds of audio
        result = sound_device.sound_record("5s", record_file)
        if result:
            print("   ✓ Recording successful!")

            # Check if file exists and has content
            if os.path.exists(record_file):
                file_size = os.path.getsize(record_file)
                print(f"   File size: {file_size} bytes")
                if file_size > 0:
                    print("   ✓ File created with content")
                else:
                    print("   ✗ File created but empty")
            else:
                print("   ✗ File not created")
        else:
            print("   ✗ Recording failed")

    except Exception as e:
        print(f"   ✗ Recording failed with error: {e}")
        import traceback

        traceback.print_exc()

    # Test mute detection
    print("\n4. Testing mute detection...")
    try:
        if os.path.exists(record_file) and os.path.getsize(record_file) > 0:
            is_muted = sound_device.sound_is_mute(record_file)
            print(f"   Mute detection result: {is_muted}")
            if is_muted:
                print("   ⚠ Audio appears to be muted")
            else:
                print("   ✓ Audio is not muted")
        else:
            print("   ⚠ Cannot test mute detection - no recording file")
    except Exception as e:
        print(f"   ✗ Mute detection failed with error: {e}")

    # Cleanup
    try:
        if os.path.exists(record_file):
            os.remove(record_file)
            print(f"\n5. Cleaned up test file: {record_file}")
    except Exception as e:
        print(f"   Warning: Could not clean up test file: {e}")

    print("\n=== Test Summary ===")
    print("If recording was successful, Sound01 device is now working properly!")
    print("The device can:")
    print("  - Record audio from Sound BlasterX G6 microphone")
    print("  - Detect if audio is muted")
    print("  - Work with TV mute detection functionality")

except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure the required files exist in the correct locations")
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback

    traceback.print_exc()
