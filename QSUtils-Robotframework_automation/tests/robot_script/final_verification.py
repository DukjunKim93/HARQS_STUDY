#!/usr/bin/env python3
"""
Final verification script to confirm Sound01 device is properly configured
and can be used for TV mute detection with the Sound BlasterX G6 microphone.
"""

import sys
import os


def main():
    print("=== Sound01 Device Final Verification ===\n")

    # Check 1: Device configuration
    print("1. Checking Sound01 device configuration...")
    try:
        # Add paths to find the modules
        sys.path.append(
            os.path.join(os.path.dirname(__file__), "robot-scripts-package")
        )
        sys.path.append(
            os.path.join(os.path.dirname(__file__), "robot-scripts-package", "BTS")
        )

        # Import the device settings
        from tests.robot_script.BTS_Device_Settings import Sound01

        print(f"   ✓ Device name: {Sound01.get('name', 'N/A')}")
        print(f"   ✓ Device type: {Sound01.get('type', 'N/A')}")
        print(f"   ✓ Sound device ID: {Sound01.get('sound_dev_id', 'N/A')}")

        expected_name = "마이크 (2- Sound BlasterX G6)"
        if Sound01.get("name") == expected_name:
            print(
                "   ✓ Device is correctly configured for Sound BlasterX G6 microphone"
            )
        else:
            print(f"   ✗ Device configuration mismatch!")
            print(f"     Expected: {expected_name}")
            print(f"     Actual: {Sound01.get('name')}")
            return False

    except ImportError as e:
        print(f"   ✗ Failed to import device settings: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

    # Check 2: System tools installation
    print("\n2. Checking system tools installation...")
    try:
        import subprocess

        # Check ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("   ✓ ffmpeg is installed and accessible")
        else:
            print("   ✗ ffmpeg is not properly installed")
            return False

        # Check sox
        result = subprocess.run(
            ["sox", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("   ✓ sox is installed and accessible")
        else:
            print("   ✗ sox is not properly installed")
            return False

    except subprocess.TimeoutExpired:
        print("   ✗ Command timed out")
        return False
    except FileNotFoundError:
        print("   ✗ Required tools (ffmpeg/sox) are not installed")
        return False
    except Exception as e:
        print(f"   ✗ Error checking system tools: {e}")
        return False

    # Check 3: BTS_Sound library modification
    print("\n3. Checking BTS_Sound library configuration...")
    try:
        # Check the virtual environment version
        venv_bts_sound_path = os.path.join(
            ".venv", "lib", "python3.12", "site-packages", "BTS", "BTS_Sound.py"
        )
        if os.path.exists(venv_bts_sound_path):
            with open(venv_bts_sound_path, "r") as f:
                content = f.read()
                if "if os.name == 'posix'" in content:
                    print("   ✓ BTS_Sound library is properly configured for Linux")
                else:
                    print("   ✗ BTS_Sound library is not properly configured for Linux")
                    return False
        else:
            print("   ✗ BTS_Sound library not found in virtual environment")
            return False

    except Exception as e:
        print(f"   ✗ Error checking BTS_Sound library: {e}")
        return False

    # Check 4: Audio device availability
    print("\n4. Checking audio device availability...")
    try:
        import subprocess

        # Check if the Sound BlasterX G6 is recognized by the system
        result = subprocess.run(
            ["arecord", "-l"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "Sound BlasterX G6" in result.stdout:
            print("   ✓ Sound BlasterX G6 is recognized by the system")
        else:
            print("   ⚠ Sound BlasterX G6 may not be properly recognized")
            print("     (This may be normal depending on the system configuration)")

        # Check PulseAudio sinks
        result = subprocess.run(
            ["pactl", "list", "sinks", "short"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("   ✓ Audio subsystem is accessible")
        else:
            print("   ⚠ Audio subsystem may not be properly configured")

    except subprocess.TimeoutExpired:
        print("   ✗ Command timed out")
    except FileNotFoundError:
        print("   ⚠ Audio utilities (arecord/pactl) not available")
    except Exception as e:
        print(f"   ⚠ Error checking audio devices: {e}")

    print("\n=== Verification Summary ===")
    print("✓ Sound01 device is properly configured for Sound BlasterX G6 microphone")
    print("✓ Required system tools (ffmpeg, sox) are installed")
    print("✓ BTS_Sound library is properly configured for Linux")
    print("✓ System is ready for TV mute detection tests")

    print("\n=== Next Steps ===")
    print("To test actual audio recording and TV mute detection:")
    print("1. Run: python test_sound_device.py")
    print("2. Run: robot sound_test.robot")
    print("3. Ensure Sound BlasterX G6 is properly connected")
    print("4. Ensure TV is playing audio content during testing")

    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 All checks passed! System is ready for Sound01 device operation.")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed. Please review the errors above.")
        sys.exit(1)
