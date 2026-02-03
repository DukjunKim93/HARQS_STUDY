#!/usr/bin/env python3

import sys
import os

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

from BTS.BTS_Sound import BTS_Sound
from tests.robot_script.BTS_Device_Settings import Sound01


def main():
    print("Final dBFS Level Demonstration")
    print("=" * 40)

    # Create a BTS_Sound instance
    sound = BTS_Sound()

    # Set the device from the configuration
    if Sound01.get("name"):
        sound.sound_set_device_name(Sound01["name"])
        print(f"Device set to: {Sound01['name']}")

    # Record a short test file
    import time

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    record_file = f"/tmp/final_demo_{timestamp}.wav"

    print(f"\nRecording 2 seconds of audio to: {record_file}")
    try:
        result = sound.sound_record("2s", record_file)
        print(f"Recording result: {result}")

        if os.path.exists(record_file) and os.path.getsize(record_file) > 0:
            print(
                f"File created successfully. Size: {os.path.getsize(record_file)} bytes"
            )

            # Get dBFS level using the fixed method
            dbfs_level = sound.sound_get_dbfs(record_file)
            print(f"\n--- dBFS Level Results ---")
            print(f"Audio file dBFS level: {dbfs_level}")

            # Test threshold functionality
            print(f"\n--- Threshold Testing ---")
            thresholds = [-90.0, -80.0, -70.0, -60.0, -50.0]

            for threshold in thresholds:
                has_sound = sound.sound_is_above_threshold(record_file, threshold)
                result_text = "PASS" if has_sound else "FAIL"
                print(
                    f"Threshold {threshold:6.1f} dBFS: {result_text} (Audio detected: {has_sound})"
                )

            # Show the actual dBFS value in context
            print(f"\n--- Analysis Summary ---")
            print(f"Recorded audio level: {dbfs_level:.2f} dBFS")
            print(f"This represents very quiet audio (near silence)")
            print(f"In a real test with actual TV audio, levels would be much higher")

        else:
            print("Failed to create recording file")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
