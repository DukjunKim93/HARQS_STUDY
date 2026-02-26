# db_level_test.robot Test Guide (EN)

## Overview
`db_level_test.robot` records audio from the configured sound device and prints detailed dBFS level information. It
runs two test cases: one that logs dB levels for multiple durations, and another that compares detection results across
different threshold values.【F:tests/robot_script/db_level_test.robot†L1-L86】

## Main Dependencies
- `BTS.BTS_Sound` (aliased as `SoundSensor`) for recording and dBFS analysis.
- `BTS_Device_Settings.py` must define `Sound01` for the target microphone/device.【F:tests/robot_script/db_level_test.robot†L9-L33】

## How to Run

```bash
python -m robot.run tests/robot_script/db_level_test.robot
```

## Expected Results
- Test case **Display Audio dB Levels** logs per-duration dBFS readings and PASS/FAIL based on threshold checks.
- Test case **Compare Different Thresholds** logs whether recorded audio is above each threshold value.
- Failures usually indicate missing audio devices or an invalid `Sound01` configuration.
