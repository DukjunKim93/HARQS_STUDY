# TV Power Control Robot Test Guide

This document explains how to run `tv_power_control.robot`, what dependencies it requires, and what results to expect.
It is intentionally separate from the system-architecture overviews.

## 1. Test Overview

`tv_power_control.robot` defines three Robot Framework test cases that control TV power via an ATHub IR device:

- **Power On TV**: Connect to ATHub and send `DISCRET_POWER_ON` multiple times.
- **Power Off TV**: Connect to ATHub and send `DISCRET_POWER_OFF` multiple times, then wait 5 seconds.
- **Power On Off Test**: Toggle power using `KEY_POWER`, with sleeps between actions.

These tests depend on the `BTS.BTS_ATHub` library and device settings from `BTS_Device_Settings.py` (referenced via the
suite settings).【F:tests/robot_script/tv_power_control.robot†L1-L23】

## 2. Required Hardware & Environment

### Hardware
- **ATHub device** connected to the host via serial (e.g., `/dev/ttyUSB1`).
- **Target TV** that can receive IR commands sent by the ATHub.

### Device Settings
The ATHub connection details are expected to be defined in `tests/robot_script/BTS_Device_Settings.py`.
Key fields include:

- `port` / `connection_info1`: serial device path (e.g., `/dev/ttyUSB1`)
- `athub_dev_id`: hub device identifier

Update these values to match your local environment before running the test.【F:tests/robot_script/BTS_Device_Settings.py†L1-L10】

## 3. Software Dependencies

### Core Python Dependencies
The ATHub library is part of the BTS package, which is installed via the **robot-scripts-package** as documented in
`BTS_INSTALLATION.md`. The standard installation uses:

```bash
pip install -e robot-scripts-package/
```

This makes `BTS.BTS_ATHub` available to Robot Framework.【F:BTS_INSTALLATION.md†L1-L46】

### System Dependencies (from BTS package)
Some BTS features require system packages (e.g., ffmpeg, sox, zbar). While `tv_power_control.robot` does not directly
use audio or QR features, the overall BTS stack expects those dependencies to be available in the environment described
in the installation guide.【F:BTS_INSTALLATION.md†L52-L99】

## 4. Running the Test

From the repository root, run:

```bash
python -m robot.run tests/robot_script/tv_power_control.robot
```

Robot Framework resolves `Variables    BTS_Device_Settings.py` relative to the suite file, so running from the repo root
is fine as long as the file remains alongside the test suite.【F:tests/robot_script/tv_power_control.robot†L1-L23】

## 5. Expected Results

### Expected Success Case
If the ATHub is connected and configured properly, all three test cases should pass:

- **Power On TV**: PASS
- **Power Off TV**: PASS
- **Power On Off Test**: PASS

### Common Failure Cases
- **Missing device variables**: If `BTS_Device_Settings.py` is not found or not loaded, you may see failures like
  `Variable '${ATHub01}' not found.` in Robot output logs.【F:results/output.xml†L35-L71】
- **Hardware connection issues**: If the ATHub is not connected or the serial path is incorrect, `athub_connect` will
  fail, causing subsequent test steps to fail (library exception or connection error).
- **IR control mismatch**: If the TV IR codes differ from the expected set (`DISCRET_POWER_ON`,
  `DISCRET_POWER_OFF`, `KEY_POWER`), the TV may not respond even though the test keywords execute without error.

## 6. Troubleshooting Checklist

1. Verify the ATHub serial path matches the local device (`/dev/ttyUSB1` is only an example).【F:tests/robot_script/BTS_Device_Settings.py†L1-L10】
2. Confirm the BTS package is installed and `BTS.BTS_ATHub` is importable (see installation guide).【F:BTS_INSTALLATION.md†L1-L46】
3. Re-run the test with `--loglevel DEBUG` if you need detailed connection logs.

```bash
python -m robot.run --loglevel DEBUG tests/robot_script/tv_power_control.robot
```

## 7. Running in an IDE (PyCharm Example)

You can run the same Robot Framework tests from an IDE like PyCharm by configuring a virtual environment and a Run
Configuration.

### 7.1. Create and Select a `.venv`

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
```

Then install project dependencies (and BTS robot scripts if needed):

```bash
pip install -e .
pip install -e robot-scripts-package/
```

The BTS install step is required so that `BTS.BTS_ATHub` is available to Robot Framework.【F:BTS_INSTALLATION.md†L1-L46】

### 7.2. PyCharm Interpreter Setup

1. **Settings → Project → Python Interpreter**.
2. Click **Add Interpreter** → **Existing**.
3. Select the interpreter at `<repo>/.venv/bin/python`.

### 7.3. Run Configuration (Robot Framework)

Create a new **Python** run configuration:

- **Script path**: `<repo>/.venv/bin/python`
- **Parameters**: `-m robot.run tests/robot_script/tv_power_control.robot`
- **Working directory**: `<repo>`

Alternatively, use a **Shell** configuration with the same command:

```bash
python -m robot.run tests/robot_script/tv_power_control.robot
```

### 7.4. Notes for IDE Runs

- Ensure the ATHub serial device path in `tests/robot_script/BTS_Device_Settings.py` matches your machine before
  launching from the IDE.【F:tests/robot_script/BTS_Device_Settings.py†L1-L10】
- If you see `Variable '${ATHub01}' not found.`, verify that the test suite can locate `BTS_Device_Settings.py` and that
  the IDE working directory is set to the repository root.【F:results/output.xml†L35-L71】
