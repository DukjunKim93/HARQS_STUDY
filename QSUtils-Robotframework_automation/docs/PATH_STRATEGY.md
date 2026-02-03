# Path Strategies

The system uses the **Strategy Pattern** to determine where dump files are stored on the local filesystem. This is
managed by `DumpPathStrategy` subclasses in `UnifiedDumpCoordinator.py`.

## Available Strategies

### 1. UnifiedPathStrategy (`unified`)

- **Behavior**: Groups all devices into a single directory named after the issue timestamp.
- **Path Structure**: `logs/{local_directory_prefix}/{timestamp}/{device_serial}/`
- **Use Case**: This is the **default** strategy and is recommended for most cases as it keeps related logs together.
- **Configuration**: Uses `local_directory_prefix` from `dump.upload_settings` (default: "issues")

### 2. IndividualPathStrategy (`individual`)

- **Behavior**: Saves dumps into device-specific folders regardless of when they were triggered.
- **Path Structure**: `logs/dumps/{device_serial}/`
- **Use Case**: Simple scenarios where cross-device correlation is not required.

### 3. HybridPathStrategy (`hybrid`)

- **Behavior**: Switches between `Unified` and `Individual` based on the trigger type.
- **Logic**:
    - `QS_FAILED` → Uses `UnifiedPathStrategy`.
    - Others → Uses `IndividualPathStrategy`.
- **Use Case**: When automated test failures need grouping but manual dumps can be kept separate.

## Configuration

The strategy can be changed via the `SettingsManager` using the key `dump.path_strategy`.
Values: `"unified"`, `"individual"`, `"hybrid"`.

## Implementation Details

The `UnifiedDumpCoordinator` instantiates the appropriate strategy at startup. When a dump is requested, it calls
`create_dump_directory()` on the strategy object.

### Overriding Paths

The `DumpProcessManager` supports an `_override_working_dir` property. If the `UnifiedDumpCoordinator` provides a
specific path (which it does for the `unified` strategy), the `DumpProcessManager` will use that path instead of its
default calculation.
