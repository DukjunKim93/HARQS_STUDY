# JFrog Integration

The system supports automatic and manual uploading of dump issues to JFrog Artifactory using the `jf-cli`.

## Upload Modes

### 1. Headless (Background) Mode

- **Triggers**: `QS_FAILED`, `CRASH_MONITOR`.
- **Behavior**: Uploads start automatically in a background thread once the dump is completed.
- **UI**: Status bar messages are shown in `BaseMainWindow`, but no blocking dialogs appear.
- **Use Case**: Automated testing and unattended monitoring.

### 2. Dialog (Interactive) Mode

- **Triggers**: `MANUAL` dump requests, or any trigger where `upload_enabled` is explicitly set to `True`.
- **Behavior**: A `JFrogUploadDialog` is displayed, showing real-time progress, file counts, and transfer speeds.
- **UI**: Blocking dialog that allows the user to monitor or cancel the upload.
- **Use Case**: Reproducing specific issues manually.

## Configuration & Prerequisites

To use the JFrog integration, the following must be set up on the host machine:

1. **JFrog CLI (`jf`)**: Must be installed and available in the system PATH.
2. **Authentication**: The CLI must be authenticated using `jf c add` and `jf rt login`.
3. **Permissions**: The user must have "Upload" permissions for the target repository.

### Settings 연동

Path strategies and other global settings can be configured via the `SettingsManager`. The default repository and server
URL are typically defined in `JFrogConfig`.

## Configuration Management

### JFrog Upload Settings Dialog

The system provides a comprehensive configuration dialog accessible from the main window:

#### Access

- **Location**: MainWindow → "Upload Config" button (next to "Auto-upload dumps" checkbox)
- **Trigger**: Click the "Upload Config" button to open the configuration dialog

#### Configuration Options

1. **Auto-upload Settings**
    - **Auto-upload dumps**: Toggle automatic upload functionality (managed in MainWindow)
    - **Default**: Enabled

2. **JFrog Server Settings**
    - **Server URL**: JFrog Artifactory server URL
    - **Default**: `https://bart.sec.samsung.net/artifactory`
    - **Repository**: Target repository for uploads
    - **Default**: `oneos-qsymphony-issues-generic-local`
    - **Server Name**: JFrog CLI server configuration name
    - **Default**: `qsutils-server`

3. **Directory Settings**
    - **Local Directory Prefix**: Prefix for local storage directories
    - **Default**: `issues` (creates `logs/{prefix}/{timestamp}/`)
    - **Upload Directory Prefix**: Prefix for JFrog upload paths
    - **Default**: `issues` (creates `{prefix}/{issue_id}/`)

#### Configuration Persistence

- All settings are stored in the application settings under `dump.upload_settings`
- Settings are automatically loaded when the application starts
- "Set to Default" button restores all values to their defaults

### Dynamic Configuration

The JFrog configuration system supports dynamic updates:

- **JFrogConfig**: Loads settings from `SettingsManager` at runtime
- **UnifiedDumpCoordinator**: Uses configured directory prefixes for path generation
- **BaseMainWindow**: Manages auto-upload checkbox state and configuration dialog

### Example Configuration

```json
{
  "dump": {
    "upload_settings": {
      "auto_upload_enabled": true,
      "jfrog_server_url": "https://bart.sec.samsung.net/artifactory",
      "jfrog_default_repo": "oneos-qsymphony-issues-generic-local",
      "jfrog_server_name": "qsutils-server",
      "local_directory_prefix": "issues",
      "upload_directory_prefix": "issues"
    }
  }
}
```

## Upload Lifecycle

1. **Verification**: `JFrogManager.verify_setup()` checks CLI installation and authentication.
2. **Event Emission**: `UnifiedDumpCoordinator` emits `JFROG_UPLOAD_STARTED`.
3. **UI Handling**: `BaseMainWindow` receives the event and decides whether to show the `JFrogUploadDialog` based on the
   `show_dialog` flag.
4. **Execution**:
    - **Dialog Path**: `JFrogUploadDialog` creates a worker and handles the upload.
    - **Headless Path**: `UnifiedDumpCoordinator` submits the task to a `ThreadPoolExecutor`.
5. **Completion**: A `JFROG_UPLOAD_COMPLETED` event is emitted.
6. **Persistence**: The result is written back to the `manifest.json` in the issue directory.

## Troubleshooting

- **No Dialog Appearing**: Ensure the event handler in `BaseMainWindow` is correctly registered and that the
  `show_dialog` flag is `True`.
- **Upload Fails silently**: Check the `manifest.json` for error messages or the application logs.
- **Python Not Responding**: This issue was resolved by using background threads (`QThread` or `ThreadPoolExecutor`).
  Ensure no heavy network operations are running on the main UI thread.
