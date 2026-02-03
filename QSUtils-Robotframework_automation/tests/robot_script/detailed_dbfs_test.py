#!/usr/bin/env python3

import sys
import os
import numpy as np

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

from BTS.BTS_Sound import BTS_Sound
from tests.robot_script.BTS_Device_Settings import Sound01
from pydub import AudioSegment


def detailed_dbfs_analysis():
    """Perform detailed dBFS analysis to understand what's happening"""
    print("Detailed dBFS Analysis")
    print("=" * 50)

    # Create a BTS_Sound instance
    sound = BTS_Sound()

    # Set the device from the configuration
    if Sound01.get("name"):
        sound.sound_set_device_name(Sound01["name"])
        print(f"Device set to: {Sound01['name']}")

    # Try to record for 3 seconds
    try:
        import time

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        record_file = f"/tmp/detailed_dbfs_test_{timestamp}.wav"
        print(f"Recording to: {record_file}")

        result = sound.sound_record("3s", record_file)
        print(f"Recording result: {result}")

        if os.path.exists(record_file) and os.path.getsize(record_file) > 0:
            print(
                f"File created successfully. Size: {os.path.getsize(record_file)} bytes"
            )

            # Method 1: Using BTS_Sound's built-in method
            print("\n--- Method 1: BTS_Sound.sound_get_dbfs ---")
            try:
                dbfs_level = sound.sound_get_dbfs(record_file)
                print(f"dBFS Level: {dbfs_level}")
            except Exception as e:
                print(f"Error getting dBFS: {e}")

            # Method 2: Manual analysis
            print("\n--- Method 2: Manual Analysis ---")
            try:
                audio = AudioSegment.from_wav(record_file)
                samples = np.array(audio.get_array_of_samples())

                print(f"Audio duration: {audio.duration_seconds:.2f} seconds")
                print(f"Sample rate: {audio.frame_rate} Hz")
                print(f"Channels: {audio.channels}")
                print(f"Sample width: {audio.sample_width} bytes")
                print(f"Total samples: {len(samples)}")

                max_amplitude = np.max(np.abs(samples))
                rms_amplitude = audio.rms

                print(f"Max amplitude: {max_amplitude}")
                print(f"RMS amplitude: {rms_amplitude}")

                # Calculate dBFS manually
                max_possible_amplitude = 32767  # for 16-bit audio
                if max_amplitude > 0:
                    max_dbfs = 20 * np.log10(max_amplitude / max_possible_amplitude)
                    print(f"Calculated Max dBFS: {max_dbfs:.2f}")
                else:
                    print("Max dBFS: -inf (no audio)")

                if rms_amplitude > 0:
                    rms_dbfs = 20 * np.log10(rms_amplitude / max_possible_amplitude)
                    print(f"Calculated RMS dBFS: {rms_dbfs:.2f}")
                else:
                    print("RMS dBFS: -inf (no audio)")

            except Exception as e:
                print(f"Error in manual analysis: {e}")
                import traceback

                traceback.print_exc()

            # Method 3: Using scipy
            print("\n--- Method 3: Scipy Analysis ---")
            try:
                import scipy.io.wavfile

                sample_rate, data = scipy.io.wavfile.read(record_file)

                print(f"Scipy sample rate: {sample_rate}")
                print(f"Data shape: {data.shape}")
                print(f"Data type: {data.dtype}")

                if len(data.shape) == 1:
                    # Mono
                    max_val = np.max(np.abs(data))
                    print(f"Mono max value: {max_val}")
                else:
                    # Stereo
                    left_channel = data[:, 0]
                    right_channel = data[:, 1]
                    max_left = np.max(np.abs(left_channel))
                    max_right = np.max(np.abs(right_channel))
                    max_val = max(max_left, max_right)
                    print(f"Left max: {max_left}, Right max: {max_right}")
                    print(f"Overall max: {max_val}")

                if max_val > 0:
                    max_dbfs = 20 * np.log10(max_val / 32767)
                    print(f"Scipy calculated dBFS: {max_dbfs:.2f}")
                else:
                    print("Scipy dBFS: -inf (no audio)")

            except Exception as e:
                print(f"Error in scipy analysis: {e}")
                import traceback

                traceback.print_exc()

        else:
            print("File was not created or is empty")

    except Exception as e:
        print(f"Error during recording: {e}")
        import traceback

        traceback.print_exc()


def test_threshold_functionality():
    """Test the threshold functionality with different scenarios"""
    print("\n" + "=" * 50)
    print("Threshold Functionality Test")
    print("=" * 50)

    sound = BTS_Sound()
    if Sound01.get("name"):
        sound.sound_set_device_name(Sound01["name"])

    import time

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    record_file = f"/tmp/threshold_test_{timestamp}.wav"

    try:
        print(f"Recording to: {record_file}")
        result = sound.sound_record("3s", record_file)
        print(f"Recording result: {result}")

        if os.path.exists(record_file) and os.path.getsize(record_file) > 0:
            print("\nThreshold Testing:")
            thresholds = [-70.0, -60.0, -50.0, -40.0, -30.0]

            # Get dBFS level
            dbfs_level = sound.sound_get_dbfs(record_file)
            print(f"Audio file dBFS level: {dbfs_level}")

            for threshold in thresholds:
                has_sound = sound.sound_is_above_threshold(record_file, threshold)
                result_text = "PASS" if has_sound else "FAIL"
                print(
                    f"Threshold {threshold:6.1f} dBFS: {result_text} (Audio detected: {has_sound})"
                )
        else:
            print("No audio file to test thresholds")

    except Exception as e:
        print(f"Error in threshold testing: {e}")
        import traceback

        traceback.print_exc()


def main():
    detailed_dbfs_analysis()
    test_threshold_functionality()


if __name__ == "__main__":
    main()
