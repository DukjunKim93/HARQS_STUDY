# BTS Library Overview (EN)

This document explains the **BTS** (Broadcast Testing System) library used by Robot Framework test suites in this
repository, and how it fits into the automation stack.

## 1. What is BTS in this repository?

BTS is a **custom device‑control library package** installed from the repository’s `robot-scripts-package/` directory.
It provides Python modules such as `BTS.BTS_ATHub`, `BTS.BTS_Sound`, and `BTS.BTS_Sdb` that expose keywords to Robot
Framework suites under `tests/robot_script/`.

The installation guide describes BTS as the main testing framework package and lists its module layout and purpose.
【F:BTS_INSTALLATION.md†L1-L27】

## 2. How BTS is installed

BTS is installed in editable mode from the local `robot-scripts-package/` directory:

```bash
pip install -e robot-scripts-package/
```

This installs BTS into the active virtual environment so Robot Framework can import it as a library.
【F:BTS_INSTALLATION.md†L31-L46】

## 3. What BTS provides (examples)

The BTS package contains device‑specific libraries, for example:

- **BTS_ATHub**: IR hub device control
- **BTS_Sound**: audio recording and analysis
- **BTS_Sdb**: SDB (Samsung Debug Bridge) control
- **BTS_Video / BTS_WebCam**: video capture and webcam control

These modules are listed in the BTS package structure overview.
【F:BTS_INSTALLATION.md†L13-L27】

## 4. How Robot Framework uses BTS

Robot Framework suites import BTS libraries as keyword providers. For example:

```robotframework
*** Settings ***
Library    BTS.BTS_ATHub    ${ATHub01}
```

Robot Framework then executes test cases that call BTS keywords (e.g., `athub_connect`, `athub_sendIR`).
【F:tests/robot_script/tv_power_control.robot†L1-L23】

## 5. Device configuration

BTS keyword execution depends on device settings provided by `BTS_Device_Settings.py`/`.ini`. For ATHub, settings such
as `port` and `connection_info1` must match the actual serial device (e.g., `/dev/ttyUSB1`).
【F:tests/robot_script/BTS_Device_Settings.py†L1-L10】

## 6. Dependencies

BTS libraries rely on additional Python and system dependencies (e.g., audio/video tools). The installation guide lists
these dependencies and notes sound‑related modifications for Linux environments.
【F:BTS_INSTALLATION.md†L49-L114】

## 7. Summary

In this repository, **BTS is the custom device‑control layer** used by Robot Framework tests. Robot Framework provides
the runner/DSL, while BTS provides the concrete device keywords that drive actual hardware interactions.
