#!/usr/bin/env python3

import sys
import os
import numpy as np
import json
from datetime import datetime

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

from BTS.BTS_Sound import BTS_Sound
from tests.robot_script.BTS_Device_Settings import Sound01
from pydub import AudioSegment


def analyze_audio_detailed(filepath):
    """Analyze the audio file and provide detailed dB level information"""
    print(f"Audio Analysis Report for: {filepath}")
    print("=" * 60)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check if file exists
    if not os.path.exists(filepath):
        print("ERROR: File does not exist")
        return None

    try:
        # Load audio with pydub
        audio = AudioSegment.from_wav(filepath)

        # Basic file information
        print("FILE INFORMATION:")
        print(f"  Duration: {audio.duration_seconds:.2f} seconds")
        print(f"  Sample Rate: {audio.frame_rate} Hz")
        print(f"  Channels: {audio.channels}")
        print(f"  Sample Width: {audio.sample_width * 8} bits")
        print(f"  File Size: {os.path.getsize(filepath)} bytes")
        print()

        # Get raw samples
        samples = np.array(audio.get_array_of_samples())

        # Calculate various dB metrics
        max_amplitude = np.max(np.abs(samples))
        rms = audio.rms
        max_possible_amplitude = 32767  # for 16-bit audio

        print("AMPLITUDE ANALYSIS:")
        print(f"  Maximum Amplitude: {max_amplitude}")
        print(f"  RMS Amplitude: {rms}")
        print(f"  Mean Amplitude: {np.mean(samples):.2f}")
        print(f"  Std Deviation: {np.std(samples):.2f}")
        print()

        # Convert to dBFS
        if max_amplitude > 0:
            max_dbfs = 20 * np.log10(max_amplitude / max_possible_amplitude)
            print("DECIBEL LEVELS (dBFS):")
            print(f"  Peak Level: {max_dbfs:.2f} dBFS")
        else:
            max_dbfs = -np.inf
            print("DECIBEL LEVELS (dBFS):")
            print(f"  Peak Level: -inf dBFS")

        if rms > 0:
            rms_dbfs = 20 * np.log10(rms / max_possible_amplitude)
            print(f"  RMS Level: {rms_dbfs:.2f} dBFS")
        else:
            rms_dbfs = -np.inf
            print(f"  RMS Level: -inf dBFS")

        print()

        # Analyze by time segments
        print("TIME-BASED ANALYSIS:")
        segment_duration = 1.0  # 1 second segments
        samples_per_segment = int(audio.frame_rate * segment_duration)

        if len(samples.shape) > 1:  # Stereo
            left_samples = samples[:, 0]
            right_samples = samples[:, 1]

            num_segments = min(5, int(len(left_samples) / samples_per_segment))
            print(f"  Analyzing {num_segments} one-second segments (stereo):")

            for i in range(num_segments):
                start_idx = i * samples_per_segment
                end_idx = min((i + 1) * samples_per_segment, len(left_samples))

                left_segment = left_samples[start_idx:end_idx]
                right_segment = right_samples[start_idx:end_idx]

                left_max = np.max(np.abs(left_segment))
                right_max = np.max(np.abs(right_segment))

                if left_max > 0:
                    left_dbfs = 20 * np.log10(left_max / max_possible_amplitude)
                else:
                    left_dbfs = -np.inf

                if right_max > 0:
                    right_dbfs = 20 * np.log10(right_max / max_possible_amplitude)
                else:
                    right_dbfs = -np.inf

                print(
                    f"    Segment {i+1:2d} ({i:2d}-{i+1:2d}s): L={left_dbfs:6.2f} dBFS | R={right_dbfs:6.2f} dBFS"
                )
        else:  # Mono
            num_segments = min(5, int(len(samples) / samples_per_segment))
            print(f"  Analyzing {num_segments} one-second segments (mono):")

            for i in range(num_segments):
                start_idx = i * samples_per_segment
                end_idx = min((i + 1) * samples_per_segment, len(samples))

                segment = samples[start_idx:end_idx]
                segment_max = np.max(np.abs(segment))

                if segment_max > 0:
                    segment_dbfs = 20 * np.log10(segment_max / max_possible_amplitude)
                else:
                    segment_dbfs = -np.inf

                print(
                    f"    Segment {i+1:2d} ({i:2d}-{i+1:2d}s): {segment_dbfs:6.2f} dBFS"
                )

        print()

        # Threshold comparison
        thresholds = [-70.0, -60.0, -50.0, -40.0, -30.0]
        print("THRESHOLD COMPARISON:")
        for threshold in thresholds:
            is_above = max_dbfs > threshold if max_dbfs != -np.inf else False
            result = "PASS" if is_above else "FAIL"
            print(f"  {threshold:6.1f} dBFS: {result} (Peak: {max_dbfs:6.2f} dBFS)")

        print()

        # Summary
        print("SUMMARY:")
        if max_dbfs != -np.inf:
            print(f"  Overall Peak Level: {max_dbfs:.2f} dBFS")
            if max_dbfs > -60.0:
                print("  Result: AUDIO DETECTED (Above -60 dBFS threshold)")
            else:
                print("  Result: NO SIGNIFICANT AUDIO (Below -60 dBFS threshold)")
        else:
            print("  Overall Peak Level: No audio detected")
            print("  Result: NO AUDIO DETECTED")

        # Return analysis data
        analysis_data = {
            "file": filepath,
            "duration": audio.duration_seconds,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "max_amplitude": int(max_amplitude),
            "rms_amplitude": rms,
            "peak_dbfs": float(max_dbfs),
            "rms_dbfs": float(rms_dbfs) if rms_dbfs != -np.inf else None,
            "threshold_result": bool(
                max_dbfs > -60.0 if max_dbfs != -np.inf else False
            ),
        }

        return analysis_data

    except Exception as e:
        print(f"ERROR: Failed to analyze audio file: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    print("Audio File dB Level Analyzer")
    print("=" * 40)

    import sys
    import time

    if len(sys.argv) > 1:
        # Analyze the specified file
        filepath = sys.argv[1]
        print(f"Analyzing specified file: {filepath}")
        print()
        analysis = analyze_audio_detailed(filepath)

        if analysis:
            # Save analysis to JSON file
            json_file = filepath.replace(".wav", "_analysis.json")
            with open(json_file, "w") as f:
                json.dump(analysis, f, indent=2)
            print(f"Analysis saved to: {json_file}")
    else:
        # Look for recent recordings
        import glob

        # Look for recent test recordings
        test_files = glob.glob("/tmp/threshold_test_*.wav") + glob.glob(
            "/tmp/analysis_test_*.wav"
        )

        if test_files:
            # Get the most recent file
            latest_file = max(test_files, key=os.path.getctime)
            print(f"Analyzing most recent recording: {latest_file}")
            print()
            analysis = analyze_audio_detailed(latest_file)

            if analysis:
                # Save analysis to JSON file
                json_file = latest_file.replace(".wav", "_analysis.json")
                with open(json_file, "w") as f:
                    json.dump(analysis, f, indent=2)
                print(f"Analysis saved to: {json_file}")
        else:
            print("No recent recordings found.")
            print("Creating a new test recording...")

            # Create a new recording for analysis
            sound = BTS_Sound()

            if Sound01.get("name"):
                sound.sound_set_device_name(Sound01["name"])
                print(f"Device set to: {Sound01['name']}")

            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                record_file = f"/tmp/db_analysis_{timestamp}.wav"
                print(f"Recording 3 seconds to: {record_file}")

                result = sound.sound_record("3s", record_file)
                print(f"Recording result: {result}")

                if os.path.exists(record_file):
                    print()
                    analysis = analyze_audio_detailed(record_file)

                    if analysis:
                        # Save analysis to JSON file
                        json_file = record_file.replace(".wav", "_analysis.json")
                        with open(json_file, "w") as f:
                            json.dump(analysis, f, indent=2)
                        print(f"Analysis saved to: {json_file}")

            except Exception as e:
                print(f"Error during recording: {e}")
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    main()
