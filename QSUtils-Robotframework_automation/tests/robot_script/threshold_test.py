#!/usr/bin/env python3

import sys
import os
import time

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

from BTS.BTS_Sound import BTS_Sound
from tests.robot_script.BTS_Device_Settings import Sound01


def main():
    print("Testing threshold-based sound detection...")

    # Create a BTS_Sound instance
    sound = BTS_Sound()

    # Set the device from the configuration
    if Sound01.get("name"):
        sound.sound_set_device_name(Sound01["name"])
        print(f"Device set to: {Sound01['name']}")

    # Try to record for 5 seconds
    try:
        print("Attempting to record for 5 seconds...")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        record_file = f"/tmp/threshold_test_{timestamp}.wav"
        print(f"Recording to: {record_file}")

        result = sound.sound_record("5s", record_file)
        print(f"Recording result: {result}")

        if os.path.exists(record_file):
            file_size = os.path.getsize(record_file)
            print(f"File created successfully. Size: {file_size} bytes")

            if file_size > 0:
                # Test the new threshold-based method
                print("\n--- Testing threshold-based detection ---")
                has_sound = sound.sound_is_above_threshold(record_file, -60.0)
                dbfs = sound.sound_get_dbfs(record_file)

                print(f"Audio dBFS level: {dbfs}")
                print(f"Is above threshold (-60.0 dBFS): {has_sound}")

                # Determine pass/fail based on threshold
                if has_sound:
                    print("RESULT: PASS - Audio detected above threshold")
                else:
                    print("RESULT: FAIL - No significant audio detected")

                # Test with different thresholds
                print("\n--- Testing with different thresholds ---")
                thresholds = [-70.0, -60.0, -50.0, -40.0, -30.0]
                for threshold in thresholds:
                    has_sound = sound.sound_is_above_threshold(record_file, threshold)
                    print(
                        f"Threshold {threshold:5.1f} dBFS: {'PASS' if has_sound else 'FAIL'}"
                    )
            else:
                print("File created but is empty.")
        else:
            print("File was not created.")

    except Exception as e:
        print(f"Error during recording: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
