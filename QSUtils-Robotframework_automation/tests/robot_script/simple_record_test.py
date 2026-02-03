#!/usr/bin/env python3

import sys
import os
import time

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

from BTS.BTS_Sound import BTS_Sound
from tests.robot_script.BTS_Device_Settings import Sound01


def main():
    print("Testing sound recording...")

    # Create a BTS_Sound instance
    sound = BTS_Sound()

    # Set the device from the configuration
    if Sound01.get("name"):
        sound.sound_set_device_name(Sound01["name"])
        print(f"Device set to: {Sound01['name']}")

    # Get the current device name
    current_device = sound.sound_get_device()
    print(f"Current device name: '{current_device}'")

    # Try to record for 5 seconds
    try:
        print("Attempting to record for 5 seconds...")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        record_file = f"/tmp/test_record_{timestamp}.wav"
        print(f"Recording to: {record_file}")

        result = sound.sound_record("5s", record_file)
        print(f"Recording result: {result}")

        if os.path.exists(record_file):
            file_size = os.path.getsize(record_file)
            print(f"File created successfully. Size: {file_size} bytes")
            if file_size > 0:
                print("Recording successful!")
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
