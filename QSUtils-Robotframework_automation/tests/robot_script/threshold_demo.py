#!/usr/bin/env python3

import sys
import os
import numpy as np

# Add the robot-scripts-package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "robot-scripts-package"))


def demonstrate_threshold_logic():
    """Demonstrate how threshold-based pass/fail logic would work"""

    print("Threshold-Based Pass/Fail Logic Demonstration")
    print("=" * 50)

    # Simulate different audio scenarios
    scenarios = [
        {
            "name": "Silent Environment",
            "max_amplitude": 3,
            "description": "No audio source",
        },
        {
            "name": "Very Quiet Background",
            "max_amplitude": 100,
            "description": "Minimal ambient noise",
        },
        {
            "name": "Normal TV Audio",
            "max_amplitude": 5000,
            "description": "Typical TV volume",
        },
        {
            "name": "Loud TV Audio",
            "max_amplitude": 15000,
            "description": "High TV volume",
        },
        {
            "name": "Very Loud Audio",
            "max_amplitude": 25000,
            "description": "Maximum comfortable volume",
        },
    ]

    # 16-bit audio maximum amplitude
    max_possible_amplitude = 32767

    print(
        f"{'Scenario':<25} {'Max Amp':<10} {'dBFS':<10} {'Threshold (-60dB)':<15} {'Result':<10}"
    )
    print("-" * 80)

    threshold = -60.0

    for scenario in scenarios:
        # Calculate dBFS
        if scenario["max_amplitude"] > 0:
            dbfs = 20 * np.log10(scenario["max_amplitude"] / max_possible_amplitude)
        else:
            dbfs = -np.inf

        # Check if above threshold
        is_above_threshold = dbfs > threshold

        # Determine pass/fail
        result = "PASS" if is_above_threshold else "FAIL"

        print(
            f"{scenario['name']:<25} {scenario['max_amplitude']:<10} {dbfs:<10.2f} {'Yes' if is_above_threshold else 'No':<15} {result:<10}"
        )

    print("\n" + "=" * 50)
    print("Threshold-Based Testing Logic:")
    print("1. Record audio for specified duration")
    print("2. Calculate maximum amplitude of the recording")
    print(f"3. Convert to dBFS (20 * log10(amplitude/{max_possible_amplitude}))")
    print(f"4. Compare with threshold ({threshold} dBFS)")
    print("5. PASS if dBFS > threshold, FAIL otherwise")
    print("\nIn a real test environment:")
    print("- A PASS indicates audio is detected above noise floor")
    print("- A FAIL indicates no significant audio (possible mute issue)")


def main():
    demonstrate_threshold_logic()


if __name__ == "__main__":
    main()
