# BTS_Example.robot Test Guide (EN)

## Overview
`BTS_Example.robot` is a large example/cheatsheet suite demonstrating how to use BTS device libraries, common keywords,
media capture, and Robot Framework language features. It includes sample test cases for ATHub, DebugShell, SDB, Sound,
WebCam, Video, PatternGenerator, OCR/Image comparison, and runner variables, plus many syntax examples (loops, IF/ELSE,
variables).【F:tests/robot_script/BTS_Example.robot†L1-L382】

## Main Dependencies
This suite imports a wide range of BTS libraries and expects multiple devices to be configured via
`BTS_Device_Settings.py`/`.ini` and `BTS_Variable.py`.

Key library dependencies include:
- `BTS.BTS_ATHub`, `BTS.BTS_DebugShell`, `BTS.BTS_Sdb`, `BTS.BTS_Sound`, `BTS.BTS_WebCam`,
  `BTS.BTS_Video`, `BTS.BTS_KeySender`, `BTS.BTS_PatternGenerator`, and others.【F:tests/robot_script/BTS_Example.robot†L7-L33】

## How to Run
From the repository root:

```bash
python -m robot.run tests/robot_script/BTS_Example.robot
```

## Expected Results
- This suite is an examples/cheatsheet collection rather than a single stable test.
- Many test cases require real hardware (ATHub, SDB device, webcam, sound device, pattern generator), so failures are
  expected if devices are not connected or configured.
- Use it as reference or run individual test cases once hardware is available.

## Notes
- The suite uses `CommonKeyword.robot` as a shared keyword resource and relies on settings created by
  `BTS_Variable.py` + `BTS_Device_Settings.ini`/`.py`.
- For OCR/Image tests, reference lists (`BTS_ReferenceList_IMG.py`, `BTS_ReferenceList_OCR.py`) must be available and
  configured appropriately.【F:tests/robot_script/BTS_Example.robot†L12-L36】
