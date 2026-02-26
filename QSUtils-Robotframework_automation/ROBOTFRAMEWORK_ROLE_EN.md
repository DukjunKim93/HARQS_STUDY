# Robot Framework Role in This Repository (EN)

This document explains how **Robot Framework** is used in this repository and how it connects to the project’s
internal structure.

## 1. Is Robot Framework a custom package?

No. Robot Framework is a standard Python package installed via pip, and it is declared as a dependency in this
repository. It is included in the `robot` extra (optional dependencies) and also listed in `requirements.txt`.

- `pyproject.toml` → `project.optional-dependencies.robot` includes `robotframework`.
- `requirements.txt` includes `robotframework>=4.0`.

These declarations mean the project expects Robot Framework to be installed from PyPI when running robot tests.
【F:pyproject.toml†L30-L78】【F:requirements.txt†L1-L13】

## 2. Why Robot Framework is used here

Robot Framework provides a **test runner + keyword-driven DSL** for device automation scenarios. In this repository,
Robot Framework is used to:

- Run `.robot` test suites under `tests/robot_script/`.
- Bind BTS device control libraries (e.g., ATHub, SDB, Sound) as Robot Framework keywords.
- Provide a readable, repeatable automation layer for Q‑Symphony test workflows.

The README lists Robot Framework as a core automation dependency and shows how `.robot` suites are executed from the
CLI.【F:README.md†L124-L187】

## 3. How Robot Framework connects to repo structure

### 3.1. Robot test suites

Robot test suites live in:

- `tests/robot_script/*.robot`

These suites import BTS libraries and device settings. Example from `tv_power_control.robot`:

```robotframework
*** Settings ***
Variables   BTS_Device_Settings.py
Library     BTS.BTS_ATHub    ${ATHub01}
```

This shows Robot Framework loading device settings and exposing ATHub keywords to test cases.
【F:tests/robot_script/tv_power_control.robot†L1-L23】

### 3.2. BTS libraries (custom device keywords)

BTS libraries are **custom code** provided by the `robot-scripts-package/` installation. The repository documents that
installing the package makes modules like `BTS.BTS_ATHub` and `BTS.BTS_Sound` available to Robot Framework.

- BTS packages are installed by `pip install -e robot-scripts-package/`.
- BTS libraries provide the actual keyword implementations used by the `.robot` suites.
【F:BTS_INSTALLATION.md†L1-L66】

## 4. Execution model (high level)

1. **Robot Framework runner** (`python -m robot.run`) loads a `.robot` suite.
2. The suite imports device settings (Python or INI files).
3. The suite imports BTS libraries as Robot Framework keywords.
4. Robot executes test cases by calling those keywords.

Example CLI usage is shown in the README’s “Test Execution Examples.”
【F:README.md†L151-L187】

## 5. Relationship to the rest of QSUtils

Robot Framework sits **alongside** the QSUtils GUI/monitoring code. It does not replace QSMonitor, but it provides a
repeatable automation layer that can:

- Validate device behaviors with IR/ADB/SDB tooling.
- Automate audio/video checks using BTS libraries.
- Produce consistent test logs and reports for QA workflows.

In short, Robot Framework is the **automation harness**, while BTS libraries provide the **device‑level keywords** and
QSUtils provides the **broader tooling and utilities** around device monitoring and diagnostics.
