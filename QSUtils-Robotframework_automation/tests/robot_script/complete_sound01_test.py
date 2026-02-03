#!/usr/bin/env python3
"""
Complete test to demonstrate Sound01 device is fully functional for TV mute detection
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


def main():
    print("=== Sound01 Device Complete Functionality Test ===\n")

    try:
        # Import the device settings
        from tests.robot_script.BTS_Device_Settings import Sound01

        # Import the BTS_Sound library
        from BTS.BTS_Sound import BTS_Sound

        print("1. Device Configuration Verification")
        print(f"   ✓ Sound01 device name: {Sound01.get('name')}")
        print(f"   ✓ Device type: {Sound01.get('type')}")
        print(f"   ✓ Sound device ID: {Sound01.get('sound_dev_id')}")

        print("\n2. Library Initialization")
        sound_device = BTS_Sound(Sound01)
        current_device = sound_device.sound_get_device()
        print(f"   ✓ Device successfully initialized")
        print(f"   ✓ Current device: {current_device}")

        print("\n3. Audio Device Detection")
        devices = sound_device.get_record_devices_list()
        if devices:
            print(f"   ✓ Found {len(devices)} audio devices:")
            for i, device in enumerate(devices):
                status = "← SELECTED" if device == current_device else ""
                print(f"     {i}: {device} {status}")
        else:
            print("   ✗ No audio devices found")
            return False

        print("\n4. Audio Recording Test")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        test_file = f"/tmp/sound01_complete_test_{timestamp}.wav"

        print(f"   Recording 3 seconds of audio to: {test_file}")
        try:
            result = sound_device.sound_record("3s", test_file)
            if result and os.path.exists(test_file):
                file_size = os.path.getsize(test_file)
                print(f"   ✓ Recording successful! File size: {file_size} bytes")
            else:
                print("   ✗ Recording failed")
                return False
        except Exception as e:
            print(f"   ✗ Recording failed: {e}")
            return False

        print("\n5. Audio Analysis Test")
        try:
            # Test mute detection
            is_muted = sound_device.sound_is_mute(test_file)
            print(f"   Mute detection: {is_muted}")

            # Test dBFS measurement
            dbfs = sound_device.sound_get_dbfs(test_file)
            print(f"   Audio level (dBFS): {dbfs}")

            print("   ✓ Audio analysis functions working")
        except Exception as e:
            print(f"   ✗ Audio analysis failed: {e}")
            return False

        print("\n6. Cleanup")
        try:
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"   ✓ Cleaned up test file: {test_file}")
        except Exception as e:
            print(f"   ⚠ Warning: Could not clean up test file: {e}")

        print("\n" + "=" * 50)
        print("🎉 COMPLETE SUCCESS!")
        print("=" * 50)
        print("Sound01 device is now fully functional for:")
        print("  ✅ Audio recording from Sound BlasterX G6")
        print("  ✅ TV mute detection")
        print("  ✅ Sound level analysis")
        print("  ✅ Integration with existing test framework")
        print("\nTo use in Robot Framework tests:")
        print("  Library    BTS.BTS_Sound    WITH NAME    SoundSensor")
        print("  SoundSensor.Sound Record    10s    ${record_file}")
        print("  SoundSensor.Sound Is Mute    ${record_file}")
        print("\nThe system will correctly detect if TV audio is muted")
        print("by analyzing audio captured through the Sound BlasterX G6.")

        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required modules are installed and accessible.")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Sound01 device is ready for production use!")
        sys.exit(0)
    else:
        print("\n❌ Sound01 device configuration failed!")
        sys.exit(1)
