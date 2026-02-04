# threshold_minus_5_test.robot Test Guide (EN)

## Overview
`threshold_minus_5_test.robot` records audio and evaluates whether the measured dBFS level is above a fixed
threshold. It includes a multi-duration test and a single 3-second test using a -5 dBFS threshold (with additional
logic comparing to -17 dBFS in the keyword implementation).【F:tests/robot_script/threshold_minus_5_test.robot†L1-L107】

## Main Dependencies
- `BTS.BTS_Sound` (aliased as `SoundSensor`) for recording and dBFS analysis.
- `BTS_Device_Settings.py` must define `Sound01` for the microphone/device path.【F:tests/robot_script/threshold_minus_5_test.robot†L7-L33】

## How to Run

```bash
python -m robot.run tests/robot_script/threshold_minus_5_test.robot
```

## Expected Results
- **Audio Detection With Threshold Minus 5** logs dBFS results for multiple durations.
- **Single Test With Threshold Minus 5** logs a single pass/fail based on recorded dBFS.
- Failures typically mean the input signal is too low or the device is not configured correctly.
