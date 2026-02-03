# Unified Dump & JFrog Integration Overview

The QSMonitor Dump system is a unified framework designed to capture device diagnostic information (dumps) and
optionally upload them to a JFrog Artifactory repository. This system integrates multiple components to ensure reliable
data collection, organized storage, and automated cloud synchronization.

## Key Features

- **Unified Entry Point**: All dump requests (manual, crash-triggered, or test-failed) are handled by a single
  `UnifiedDumpCoordinator`.
- **Intelligent Path Management**: Dumps are organized into "Issues" based on timestamps, allowing multi-device logs to
  be grouped together.
- **Event-Driven Architecture**: Uses a robust event bus system to decouple UI, business logic, and background
  processes.
- **JFrog Artifactory Integration**: Supports both background (silent) uploads for automation and interactive
  dialog-based uploads for manual sessions.
- **Multi-Device Support**: Capable of parallel dump extraction across multiple connected devices (default concurrency:
  3).
- **Manifest Tracking**: Every issue includes a `manifest.json` file that records the environment, results of each
  device dump, and upload status.
- **Real-time Status Bar**: Provides live status display for device connection, session state, dump progress, and
  AutoReboot status with priority-based layout management.
- **Configurable JFrog Settings**: Comprehensive configuration dialog for JFrog server settings, directory prefixes, and
  upload behavior, accessible directly from the main window.
- **Dynamic Directory Management**: Configurable local and upload directory prefixes allow flexible organization of dump
  files and JFrog upload paths.

## Workflow Summary

1. **Trigger**: A dump is requested via `UNIFIED_DUMP_REQUESTED` event (Common or Global).
2. **Coordination**: `UnifiedDumpCoordinator` creates an issue directory and manages the queue of devices.
3. **Extraction**: `DumpProcessManager` on each device executes the extraction scripts.
4. **Completion**: Once all devices are done, a `GLOBAL_DUMP_COMPLETED` event is issued.
5. **Upload**: Based on settings or trigger type, the `UnifiedDumpCoordinator` initiates a JFrog upload via
   `JFrogManager`.
6. **Notification**: The UI (BaseMainWindow) displays status updates or a progress dialog during the upload.

For more details, please refer to:

- [Architecture & Components](ARCHITECTURE.md)
- [JFrog Integration Details](JFROG_INTEGRATION.md)
- [Event System](EVENT_SYSTEM.md)
- [Status Bar System](STATUS_BAR.md)
- [Path Strategies](PATH_STRATEGY.md)
