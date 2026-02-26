# Checklist_TestSuite Version 1.0.robot Test Guide (EN)

## Overview
`Checklist_TestSuite Version 1.0.robot` is a large end-to-end suite for TV ↔ Soundbar connection testing. It uses many
BTS device libraries (ATHub, DebugShell, SDB, Sound, WebCam, KeySender, Navigation, RedRat) and AppiumLibrary to drive
and validate behaviors such as power control, video capture, and navigation scenarios.【F:tests/robot_script/Checklist_TestSuite Version 1.0.robot†L1-L46】

## Main Dependencies
This suite relies on multiple hardware devices and settings from `BTS_Device_Settings.py`/`.ini` and
`BTS_Variable.py`:

- `BTS.BTS_ATHub`, `BTS.BTS_DebugShell`, `BTS.BTS_Sdb`, `BTS.BTS_Sound`, `BTS.BTS_WebCam`,
  `BTS.BTS_KeySender`, `BTS.BTS_Navigation`, `BTS.BTS_RedRat`, `BTS.BTS_Common`.
- `AppiumLibrary` for device automation integration.【F:tests/robot_script/Checklist_TestSuite Version 1.0.robot†L20-L46】

## How to Run

```bash
python -m robot.run "tests/robot_script/Checklist_TestSuite Version 1.0.robot"
```

## Expected Results
- This suite is hardware-heavy and environment-specific. Many test cases will fail without connected devices
  (ATHub/DebugShell/SDB/WebCam/Sound/RedRat) and proper TV/Soundbar setup.
- Use this suite as a full system validation once all hardware is available and configured.

## Notes
- The suite imports `CommonKeyword.robot` and uses suite setup/teardown keywords defined there.
- It expects reference images via `BTS_ReferenceList_IMG.py` if image-based checks are enabled.【F:tests/robot_script/Checklist_TestSuite Version 1.0.robot†L12-L53】
