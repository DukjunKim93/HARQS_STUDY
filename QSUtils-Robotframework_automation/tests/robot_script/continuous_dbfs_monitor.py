#!/usr/bin/env python3
"""
Continuous dBFS Monitor for Sound Blaster Device
This script continuously monitors the dBFS level of the Sound Blaster device
and displays the changes in real-time.
"""

import sys
import os
import time
import threading
import queue
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))

from BTS.BTS_Sound import BTS_Sound
from tests.robot_script.BTS_Device_Settings import Sound01
from pydub import AudioSegment


class ContinuousDBFSMonitor:
    def __init__(self, interval=1.0, duration=5.0, show_graph=True):
        """
        Initialize the Continuous DBFS Monitor

        Args:
            interval (float): Time interval between measurements in seconds
            duration (float): Duration of each recording in seconds
            show_graph (bool): Whether to show real-time graph
        """
        self.interval = interval
        self.duration = duration
        self.show_graph = show_graph
        self.sound = BTS_Sound()
        self.dbfs_values = []
        self.timestamps = []
        self.running = False

        # Set the device from the configuration
        if Sound01.get("name"):
            self.sound.sound_set_device_name(Sound01["name"])
            print(f"Device set to: {Sound01['name']}")

        # Initialize graph if needed
        if self.show_graph:
            self.init_graph()

    def init_graph(self):
        """Initialize the real-time graph"""
        plt.ion()  # Turn on interactive mode
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        (self.line,) = self.ax.plot([], [], "b-", linewidth=2)
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("dBFS")
        self.ax.set_title("Real-time dBFS Monitoring")
        self.ax.grid(True)
        self.ax.set_ylim(-100, 10)  # Set y-axis range
        self.ax.axhline(
            y=-60, color="r", linestyle="--", alpha=0.7, label="Threshold (-60 dBFS)"
        )
        self.ax.legend()

    def get_dbfs_from_audio(self, filepath):
        """
        Calculate dBFS from audio file

        Args:
            filepath (str): Path to the audio file

        Returns:
            float: dBFS value or None if error
        """
        try:
            # Load audio with pydub
            audio = AudioSegment.from_wav(filepath)

            # Get raw samples
            samples = np.array(audio.get_array_of_samples())

            # Calculate dBFS
            max_amplitude = np.max(np.abs(samples))
            max_possible_amplitude = 32767  # for 16-bit audio

            if max_amplitude > 0:
                max_dbfs = 20 * np.log10(max_amplitude / max_possible_amplitude)
                return max_dbfs
            else:
                return float("-inf")

        except Exception as e:
            print(f"Error analyzing audio file: {e}")
            return None

    def record_and_analyze(self):
        """Record audio and analyze dBFS"""
        try:
            # Create temporary file path
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            record_file = f"/tmp/dbfs_monitor_{timestamp}.wav"

            # Record audio
            result = self.sound.sound_record(f"{self.duration}s", record_file)

            if result and os.path.exists(record_file):
                # Analyze dBFS
                dbfs = self.get_dbfs_from_audio(record_file)

                # Clean up temporary file
                try:
                    os.remove(record_file)
                except:
                    pass

                return dbfs
            else:
                return None

        except Exception as e:
            print(f"Error during recording: {e}")
            return None

    def update_graph(self):
        """Update the real-time graph"""
        if not self.show_graph or len(self.dbfs_values) == 0:
            return

        # Convert timestamps to seconds from start
        if len(self.timestamps) > 0:
            start_time = self.timestamps[0]
            x_data = [t - start_time for t in self.timestamps]
            y_data = self.dbfs_values

            # Update plot data
            self.line.set_data(x_data, y_data)

            # Adjust x-axis to show last 60 seconds of data
            if len(x_data) > 0:
                max_x = max(x_data)
                self.ax.set_xlim(max(0, max_x - 60), max_x + 5)

            # Redraw
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def print_status(self, dbfs):
        """Print current status"""
        current_time = datetime.now().strftime("%H:%M:%S")
        if dbfs is not None:
            if dbfs == float("-inf"):
                print(f"[{current_time}] dBFS: -inf")
            else:
                status = "AUDIO DETECTED" if dbfs > -60 else "NO SIGNIFICANT AUDIO"
                print(f"[{current_time}] dBFS: {dbfs:.2f} ({status})")
        else:
            print(f"[{current_time}] dBFS: ERROR")

    def start_monitoring(self):
        """Start continuous monitoring"""
        print("Starting continuous dBFS monitoring...")
        print("Press Ctrl+C to stop")
        print("-" * 50)

        self.running = True
        start_time = time.time()

        try:
            while self.running:
                # Record and analyze
                dbfs = self.record_and_analyze()

                # Store data
                current_time = time.time()
                self.timestamps.append(current_time)
                self.dbfs_values.append(dbfs if dbfs is not None else -100)

                # Print status
                self.print_status(dbfs)

                # Update graph
                self.update_graph()

                # Wait for next interval
                elapsed = time.time() - current_time
                sleep_time = max(0, self.interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nStopping monitoring...")
        finally:
            self.running = False
            if self.show_graph:
                plt.ioff()
                plt.show()

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.running = False


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Continuous dBFS Monitor for Sound Blaster Device"
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=1.0,
        help="Time interval between measurements in seconds (default: 1.0)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=5.0,
        help="Duration of each recording in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--no-graph", action="store_true", help="Disable real-time graph display"
    )

    args = parser.parse_args()

    # Create monitor instance
    monitor = ContinuousDBFSMonitor(
        interval=args.interval, duration=args.duration, show_graph=not args.no_graph
    )

    # Start monitoring
    monitor.start_monitoring()


if __name__ == "__main__":
    main()
