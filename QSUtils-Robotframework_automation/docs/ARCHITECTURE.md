# Architecture & Components

The QSMonitor dump system is composed of several core components working together across different scopes (Global vs.
Device).

## Core Components

### 1. UnifiedDumpCoordinator

Located in `src/QSUtils/QSMonitor/services/UnifiedDumpCoordinator.py`.

- **Scope**: Global (Application-wide).
- **Role**: The orchestrator of the entire dump and upload process.
- **Responsibilities**:
    - Listens for `UNIFIED_DUMP_REQUESTED` and `GLOBAL_DUMP_REQUESTED` events.
    - Creates the "Issue" directory structure.
    - Manages concurrency (e.g., maximum 3 parallel extractions).
    - Writes and updates `manifest.json`.
    - Triggers JFrog uploads after dumps are completed.

### 2. DumpProcessManager

Located in `src/QSUtils/DumpManager/DumpProcessManager.py`.

- **Scope**: Device-specific (one per device).
- **Role**: Executes the actual dump extraction on a specific device.
- **Responsibilities**:
    - Executes ADB-based dump scripts.
    - Handles timeouts and process errors.
    - Emits `DUMP_COMPLETED` or `DUMP_ERROR` events upon finishing.
    - Can be overridden to save logs directly into an issue directory.

### 3. Event Bus

- **Global Event Bus**: Used for application-wide coordination (e.g., between `UnifiedDumpCoordinator` and
  `BaseMainWindow`).
- **Device Event Manager**: Used for device-local communication (e.g., between `DumpProcessManager` and its parent
  widget).

### 4. Status Bar System

Located in `src/QSUtils/UIFramework/base/BaseDeviceWindow.py` and `src/QSUtils/QSMonitor/ui/DeviceWindow.py`.

- **Scope**: Device-specific (one per device window).
- **Role**: Provides real-time status display for device operations.
- **Responsibilities**:
    - Displays connection status (Connected/Disconnected).
    - Shows session state (Running/Paused/Stopped).
    - Provides real-time dump progress and status.
    - Handles AutoReboot status display with priority management.
    - Event-driven updates using CommonEventType events.

### 5. JFrogManager & JFrogUploader

Located in `src/QSUtils/JFrogUtils/`.

- **JFrogManager**: High-level interface for verification and starting uploads.
- **JFrogUploader**: Handles the `jf-cli` commands.
- **JFrogUploadWorker**: A `QThread` based worker that performs uploads in the background to prevent UI freezing.
- **JFrogConfigDialog**: Configuration dialog for JFrog upload settings, accessible from MainWindow.

### 6. JFrog Configuration System

Located in `src/QSUtils/JFrogUtils/JFrogConfig.py` and `src/QSUtils/JFrogUtils/JFrogConfigDialog.py`.

- **JFrogConfig**: Configuration class with dynamic loading from settings.
- **JFrogConfigDialog**: User interface for configuring JFrog settings.
- **Settings Integration**: All JFrog settings stored under `dump.upload_settings` key.

## The "Issue" Concept

Unlike traditional individual dumps, the system organizes data into **Issues**.

- An Issue is identified by a timestamp (`YYMMDD-HHMMSS`).
- Directory: `logs/{local_directory_prefix}/{timestamp}/` (configurable prefix, default: "issues")
- Structure:
    ```
    logs/issues/240113-120000/
    ├── manifest.json
    ├── Device_Serial_1/
    │   └── (dump files)
    ├── Device_Serial_2/
    │   └── (dump files)
    └── logs/
        └── (global or specific logs)
    ```
- **Configuration**: Directory prefix is configurable via `dump.upload_settings.local_directory_prefix`
- **Upload Path**: JFrog upload uses `{upload_directory_prefix}/{issue_id}` (configurable, default: "issues")

## Manifest File (`manifest.json`)

The manifest acts as a single source of truth for an issue:

- `issue_id`: The timestamp.
- `triggered_by`: manual, crash_monitor, or qs_failed.
- `targets`: List of devices involved.
- `results`: Success/Failure status and details for each device.
- `upload_result`: Status of the JFrog upload, including repository links.
