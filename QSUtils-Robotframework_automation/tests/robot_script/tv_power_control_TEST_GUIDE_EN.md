# tv_power_control.robot Test Guide (EN)

## Overview
`tv_power_control.robot` controls TV power through an ATHub IR device. It sends discrete power-on/off IR commands and a
toggle power sequence (KEY_POWER) with waits between actions.【F:tests/robot_script/tv_power_control.robot†L1-L23】

## Main Dependencies
- `BTS.BTS_ATHub` library with ATHub device settings loaded from `BTS_Device_Settings.py`.
- ATHub device connected via serial (e.g., `/dev/ttyUSB1`).【F:tests/robot_script/tv_power_control.robot†L1-L23】

## How to Run

```bash
python -m robot.run tests/robot_script/tv_power_control.robot
```

## Expected Results
- **Power On TV** and **Power Off TV** send repeated IR commands and should pass if ATHub + TV are configured correctly.
- **Power On Off Test** toggles power using `KEY_POWER` with delays and should pass when the TV responds to IR signals.

## Notes
For a deeper walkthrough (including IDE setup and troubleshooting), see `TV_POWER_CONTROL_TEST_GUIDE.md` at the
repository root.
