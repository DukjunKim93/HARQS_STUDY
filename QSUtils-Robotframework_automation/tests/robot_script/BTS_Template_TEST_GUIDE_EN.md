# BTS_Template.robot Test Guide (EN)

## Overview
`BTS_Template.robot` is a minimal template for creating new BTS-based Robot Framework test suites. It shows typical
library imports, device settings, and suite/test setup blocks, but only contains a single example test case
(`Example Hello BTS`).【F:tests/robot_script/BTS_Template.robot†L1-L62】

## Main Dependencies
- Device settings are loaded from `BTS_Variable.py` and `BTS_Device_Settings.ini`/`.py`.
- BTS libraries are listed but commented out; you enable only the ones you need for your test suite.【F:tests/robot_script/BTS_Template.robot†L16-L46】

## How to Run

```bash
python -m robot.run tests/robot_script/BTS_Template.robot
```

## Expected Results
- By default, the suite logs “Hello BTS” and should pass without any connected hardware.
- If you uncomment BTS libraries or add device-dependent steps, ensure the corresponding hardware is configured.
