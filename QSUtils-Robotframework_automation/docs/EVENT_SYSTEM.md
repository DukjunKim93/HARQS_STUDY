# Event System

The QSMonitor dump system relies heavily on an event-driven architecture to communicate between disparate modules.

## Key Events

### Common Events (`CommonEventType`)

Defined in `src/QSUtils/UIFramework/base/CommonEvents.py`.

- **`UNIFIED_DUMP_REQUESTED`**
    - **Payload**: `{"triggered_by": str, "request_device_id": str, "upload_enabled": bool, "issue_dir": str}`
    - **Description**: Triggered by any component to start a unified dump process.
- **`DUMP_COMPLETED`**
    - **Payload**: `{"device_id": str, "success": bool, "dump_path": str, ...}`
    - **Description**: Emitted by `DumpProcessManager` when a specific device finishes its dump.
- **`DUMP_ERROR`**
    - **Payload**: `{"error_message": str}`
    - **Description**: Emitted when a device dump fails.

#### Status Bar Events

- **`DEVICE_CONNECTION_CHANGED`**
    - **Payload**: `{"connected": bool, "device_serial": str, "connection_type": str}`
    - **Description**: Emitted when device connection status changes (USB/WiFi/Network).
- **`SESSION_STATE_CHANGED`**
    - **Payload**: `{"state": str, "manual": bool, "previous_state": str}`
    - **Description**: Emitted when monitoring session state changes (running/paused/stopped).
- **`DUMP_PROGRESS_UPDATED`**
    - **Payload**: `{"progress": int, "stage": str, "message": str, "dump_id": str}`
    - **Description**: Emitted during dump extraction to provide real-time progress (0-100%).
- **`DUMP_STATUS_CHANGED`**
    - **Payload**: `{"status": str, "dump_id": str, "triggered_by": str, "error_message": str}`
    - **Description**: Emitted when dump status changes (in_progress/completed/failed/cancelled).
- **`STATUS_UPDATE_REQUESTED`**
    - **Payload**: `{}`
    - **Description**: Generic event to request status bar updates.

### Global Events (`GlobalEventType`)

Defined in `src/QSUtils/QSMonitor/core/GlobalEvents.py`.

- **`GLOBAL_DUMP_COMPLETED`**
    - **Payload**: `{"issue_id": str, "success_count": int, "fail_count": int, "issue_dir": str}`
    - **Description**: Emitted by `UnifiedDumpCoordinator` when *all* target devices have finished their dumps.
- **`JFROG_UPLOAD_STARTED`**
    - **Payload**: `{"issue_id": str, "show_dialog": bool, "issue_root": str, "targets": list, ...}`
    - **Description**: Signal to start the JFrog upload process.
- **`JFROG_UPLOAD_COMPLETED`**
    - **Payload**: `{"issue_id": str, "success": bool, "message": str, "jfrog_links": dict, ...}`
    - **Description**: Signal that the upload process (either dialog or background) has finished.

## Event Flow Diagram

1. **Trigger Component** (e.g., `AutoRebootGroup`) → emits `UNIFIED_DUMP_REQUESTED`.
2. **UnifiedDumpCoordinator** → receives `UNIFIED_DUMP_REQUESTED`.
3. **UnifiedDumpCoordinator** → emits `DUMP_REQUESTED` (Device-scope) for each device.
4. **DumpProcessManager** (on device) → receives `DUMP_REQUESTED`, performs dump.
5. **DumpProcessManager** → emits `DUMP_COMPLETED`.
6. **UnifiedDumpCoordinator** → receives `DUMP_COMPLETED`, updates progress.
7. **UnifiedDumpCoordinator** → emits `GLOBAL_DUMP_COMPLETED` once all devices are done.
8. **UnifiedDumpCoordinator** → emits `JFROG_UPLOAD_STARTED`.
9. **BaseMainWindow** or **Worker Thread** → handles upload.
10. **Upload Handler** → emits `JFROG_UPLOAD_COMPLETED`.
11. **UnifiedDumpCoordinator** → updates `manifest.json` with final status.

## Concurrency Control

The `UnifiedDumpCoordinator` maintains a queue of `DeviceContext` objects and processes them based on the
`_max_concurrency` limit (default: 3). It uses the `DUMP_COMPLETED` event to trigger the next item in the queue.
