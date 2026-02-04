# System Architecture & Flow (English)

This repository provides **QSUtils**, a Python-based toolkit that combines a device-monitoring GUI, ADB-driven device
management, Robot Framework automation libraries, and a unified dump + JFrog upload pipeline. The overall goal is to
support automated testing and diagnostics for Q-Symphony devices while keeping the monitoring UI responsive and
extensible.

## 1. Big Picture

QSUtils is organized into four primary layers:

1. **Applications (UI + UX)**
   - **QSMonitor**: Main monitoring application with a device-centric UI and status bar.
   - **QSLogger**: Log viewer for post-analysis.

2. **Core Services**
   - **Unified Dump System**: Centralized coordination of device dump capture and upload.
   - **Event System**: Global + device-scoped event buses to decouple UI and background work.
   - **Command Execution**: A pluggable command factory/executor system for device operations.

3. **Device & Integration Layer**
   - **ADBDevice**: Device communication, logging, and audio log parsing.
   - **Network Components**: WiFi/network interface management.
   - **JFrog Integration**: Upload manager, configuration dialog, and background upload worker.

4. **Automation & Tests**
   - **Robot Framework Libraries**: Reusable test keywords packaged under `QSUtils.RobotScripts`.
   - **Automated Tests**: Pytest coverage for dump flows, commands, and JFrog upload logic.

## 2. Key Repository Areas

- `src/QSUtils/QSMonitor/`: Main monitoring app (UI, features, dump system).
- `src/QSUtils/ADBDevice/`: ADB communication, device management, log parsing.
- `src/QSUtils/command/`: Device command execution framework.
- `src/QSUtils/JFrogUtils/`: JFrog upload logic and configuration.
- `src/QSUtils/RobotScripts/`: Robot Framework libraries, templates, and device settings.
- `tests/`: Pytest suite and Robot Framework examples.
- `docs/`: Deep-dive documentation (dump system, events, JFrog, path strategies, status bar).

## 3. Unified Dump & Upload Flow

The Unified Dump system standardizes how diagnostic dumps are captured and (optionally) uploaded to JFrog.

**High-Level Flow**

1. **Trigger**
   - A dump is requested via an event (manual, crash, or test failure).
2. **Coordination**
   - `UnifiedDumpCoordinator` creates an *Issue* directory and queues device tasks.
3. **Extraction**
   - Each device runs `DumpProcessManager` to extract logs and data.
4. **Completion**
   - The coordinator aggregates results and emits `GLOBAL_DUMP_COMPLETED`.
5. **Upload (Optional)**
   - `JFrogManager` validates setup and starts upload (headless or dialog).
6. **Manifest Update**
   - `manifest.json` is updated with per-device results and upload status.

```
Trigger Event
     │
     ▼
UnifiedDumpCoordinator
     │ (queue + issue dir)
     ▼
DumpProcessManager (per device)
     │ (DUMP_COMPLETED)
     ▼
GLOBAL_DUMP_COMPLETED
     │
     └─► JFrogManager (optional upload)
```

### 3.1. Code Walkthrough (Annotated)

Below is a short, **Code I–style** annotated snippet to show how the Unified Dump pipeline is conceptually wired. The
actual classes live under `src/QSUtils/QSMonitor/services/`, `src/QSUtils/DumpManager/`, and `src/QSUtils/JFrogUtils/`.

```python
# Pseudo-usage: Unified dump orchestration (annotated)
#
# 1) A component triggers a unified dump event
event_bus.emit("UNIFIED_DUMP_REQUESTED", {
    "triggered_by": "manual",   # comment: manual / crash / qs_failed
    "upload_enabled": True,     # comment: whether to upload to JFrog
})

# 2) UnifiedDumpCoordinator receives the event and creates an Issue folder
issue_dir = coordinator.create_issue_dir()   # comment: logs/issues/<timestamp>/
coordinator.enqueue_devices(devices)         # comment: queue devices for dump extraction

# 3) DumpProcessManager runs per-device extraction
for device in coordinator.next_devices():
    dump_manager = DumpProcessManager(device)
    dump_manager.run(issue_dir)              # comment: writes logs under issue_dir/device_id/

# 4) Coordinator aggregates results and emits completion
event_bus.emit("GLOBAL_DUMP_COMPLETED", {
    "issue_dir": issue_dir,
    "success_count": 3,
    "fail_count": 0,
})

# 5) If enabled, JFrogManager uploads the Issue folder
if upload_enabled:
    jfrog_manager.upload_issue(issue_dir)    # comment: may run in background thread
```

## 4. Event-Driven Architecture

QSUtils uses two scopes of events:

- **Common Events**: Device/local events (status bar, dump progress, connection state).
- **Global Events**: Application-wide coordination (dump completion, JFrog upload lifecycle).

This design keeps UI components lightweight and allows background tasks to run without blocking the main thread.

### 4.1. Code Walkthrough (Annotated)

```python
# Pseudo-usage: Event flow (annotated)
#
# Device-level dump completion
device_event_bus.emit("DUMP_COMPLETED", {
    "device_id": "TV-1234",
    "success": True,
    "dump_path": "/logs/issues/240113-120000/TV-1234/",
})

# Global completion after all device dumps
global_event_bus.emit("GLOBAL_DUMP_COMPLETED", {
    "issue_id": "240113-120000",
    "success_count": 3,
    "fail_count": 0,
})

# UI listens and updates status bar without blocking the UI thread
ui.on_event("GLOBAL_DUMP_COMPLETED", lambda payload: status_bar.show_done(payload))
```

## 5. Robot Framework Automation

Automation support is shipped as a Robot Framework library package:

- `QSUtils.RobotScripts.BTS.*` provides test keywords for mobile, Excel, video, and device setup workflows.
- Templates and examples in `src/QSUtils/RobotScripts/` and `tests/robot_script/` provide starting points for custom
  automation suites.

### 5.1. Code Walkthrough (Annotated)

```robotframework
*** Settings ***
Library    BTS.BTS_ATHub    ${ATHub01}   # comment: IR hub control for power on/off
Variables  BTS_Device_Settings.py       # comment: device connection details

*** Test Cases ***
Power On TV
    athub_connect
    athub_sendIR    DISCRET_POWER_ON    # comment: send IR code to power on
    athub_disconnect
```

## 6. Typical Usage Scenarios

### A. Manual Monitoring + Dump
1. Launch `qsmonitor`.
2. Connect a device and monitor status.
3. Trigger a manual dump from the UI.
4. Review results locally or upload through the JFrog dialog.

### B. Automated Test + Headless Upload
1. Run Robot Framework test suites.
2. On failure or crash, a dump is triggered automatically.
3. Upload proceeds in the background (no blocking dialog).
4. Results are tracked in the issue manifest.

## 7. Extensibility Points

- **New Commands**: Add `cmd_*.py` under `src/QSUtils/command/`.
- **New Monitoring Features**: Add a feature module under `QSMonitor/features/`.
- **Custom Dump Strategy**: Extend `DumpPathStrategy` to change how issue directories are generated.
- **Additional Robot Keywords**: Add new libraries under `QSUtils/RobotScripts/`.

## 8. Suggested Reading

- `docs/OVERVIEW.md`: Unified dump and JFrog overview.
- `docs/ARCHITECTURE.md`: Detailed component responsibilities.
- `docs/EVENT_SYSTEM.md`: Event flow and key payloads.
- `docs/JFROG_INTEGRATION.md`: Upload modes and configuration.
- `docs/STATUS_BAR.md`: Status bar behavior and priority logic.
- `docs/PATH_STRATEGY.md`: Dump path strategies.
