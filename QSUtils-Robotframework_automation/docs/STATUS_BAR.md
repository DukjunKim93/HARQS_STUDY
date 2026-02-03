# Status Bar System

The QSMonitor includes a comprehensive status bar system that provides real-time visibility into device operations,
connection states, and ongoing processes. This system is event-driven and integrated into the base device window
architecture.

## Architecture Overview

### Base Implementation

The status bar system is implemented in `BaseDeviceWindow` (`src/QSUtils/UIFramework/base/BaseDeviceWindow.py`) as a
core component that all device windows inherit. This ensures consistent status display across all device types.

### QSMonitor Extension

QSMonitor extends the base functionality in `DeviceWindow` (`src/QSUtils/QSMonitor/ui/DeviceWindow.py`) to add
application-specific status indicators like AutoReboot status.

## Status Display Layout

### Left Side (Progress Status)

- **Dump Status**: Shows current dump operation status and progress
- **AutoReboot Status**: Displays AutoReboot monitoring status (QSMonitor only)

### Right Side (Fixed Status)

- **Session State**: Shows monitoring session state (Running/Paused/Stopped)
- **Connection Status**: Displays device connection status (Connected/Disconnected)

## Priority System

The status bar implements a priority-based display system to manage multiple concurrent operations:

1. **Dump Status** (Highest Priority)
    - When dump operations are active, they take precedence
    - Shows progress percentage, stage information, and completion status
    - AutoReboot status is hidden during dump operations

2. **AutoReboot Status** (Medium Priority)
    - Displayed when no dump operation is in progress
    - Shows current AutoReboot monitoring state

## Event-Driven Updates

### Connection Events

- **Event**: `DEVICE_CONNECTION_CHANGED`
- **Triggers**: Device connects/disconnects via USB, WiFi, or Network
- **Display**: Updates connection status indicator with appropriate icon

### Session Events

- **Event**: `SESSION_STATE_CHANGED`
- **Triggers**: Monitoring session starts, pauses, or stops
- **Display**: Updates session state indicator with play/pause/stop icons

### Dump Progress Events

- **Event**: `DUMP_PROGRESS_UPDATED`
- **Triggers**: During dump extraction operations
- **Display**: Shows real-time progress (0-100%) and current stage

### Dump Status Events

- **Event**: `DUMP_STATUS_CHANGED`
- **Triggers**: Dump operation state changes
- **Display**: Updates dump status with completion indicators (✓, ✗, etc.)

## Status Indicators

### Connection Status

- **● Connected**: Device is properly connected and responsive
- **○ Disconnected**: Device is not connected or has lost connection

### Session State

- **▶ Running**: Active monitoring session in progress
- **⏸ Paused**: Monitoring session temporarily paused
- **■ Stopped**: No active monitoring session

### Dump Status

- **Dump...**: Dump operation in progress
- **Dump 50% (extracting)**: Progress with current stage
- **Dump ✓**: Dump completed successfully
- **Dump ✗**: Dump failed
- **Dump (Cancelled)**: Dump operation cancelled by user

### AutoReboot Status

- **AutoReboot: Monitoring**: AutoReboot is actively monitoring
- **AutoReboot: Waiting**: AutoReboot is waiting for trigger conditions
- **AutoReboot: Stopped**: AutoReboot is not active

## Integration Points

### JFrog Upload Integration

The status bar integrates with the JFrog upload system:

- Listens for `JFROG_UPLOAD_STARTED` global events
- Automatically clears dump status when upload begins for the current device
- Ensures proper status transition between dump and upload phases

### Multi-Device Synchronization

- Each device window maintains its own status bar instance
- Global events are properly filtered by device serial number
- Prevents status conflicts between multiple devices

## Customization Hooks

### Adding Custom Status Widgets

Subclasses can override `_add_custom_status_widgets()` to add application-specific status indicators:

```python
def _add_custom_status_widgets(self):
    """Add custom status widgets to the status bar"""
    self.custom_label = QLabel("")
    self.status_bar.addWidget(self.custom_label)
    
    # Register for custom events
    self.device_context.event_manager.register_event_handler(
        CustomEventType.CUSTOM_EVENT,
        self._on_custom_event
    )
```

### Layout Customization

The `_update_left_status_layout()` method can be overridden to implement custom priority logic or layout arrangements.

## Dark Theme Support

The status bar includes built-in dark theme compatibility:

- Uses neutral colors and borders that work with both light and dark themes
- Icons are selected for visibility across theme variations
- Proper contrast ratios maintained for accessibility

## Performance Considerations

- Event handlers are efficiently registered and unregistered to prevent memory leaks
- Status updates are throttled to prevent UI flooding during rapid operations
- Minimal overhead for status display operations

## Troubleshooting

### Status Not Updating

1. Verify event handlers are properly registered in `_setup_status_bar()`
2. Check that events are being emitted with correct payload structure
3. Ensure device context event manager is properly initialized

### Priority Conflicts

1. Review `_update_left_status_layout()` implementation
2. Verify priority logic matches expected behavior
3. Check for missing event emissions during state transitions

### Multi-Device Issues

1. Verify device serial number filtering in global event handlers
2. Check that device-specific event managers are used for local events
3. Ensure proper cleanup when devices are disconnected
