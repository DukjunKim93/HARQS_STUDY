# sound_test.robot Test Guide (EN)

## Overview
`sound_test.robot` verifies that the `Sound01` device is configured correctly, can record audio, and can detect whether
TV audio is muted. It includes three test cases: configuration check, recording test, and a mute check using
`Sound Is Mute` after a 10-second capture.【F:tests/robot_script/sound_test.robot†L1-L53】

## Main Dependencies
- `BTS.BTS_Sound` (aliased as `SoundSensor`) for recording and mute detection.
- `BTS_Device_Settings.py` must define `Sound01` with the correct device name/path.【F:tests/robot_script/sound_test.robot†L11-L24】

## How to Run

```bash
python -m robot.run tests/robot_script/sound_test.robot
```

## Expected Results
- **Verify Sound01 Device Configuration** should log the detected device name.
- **Test Sound Recording From Sound01** should create a WAV file and validate it is non-empty.
- **Verify TV Is Not Muted** should pass when TV audio is present (i.e., `Sound Is Mute` returns false).
