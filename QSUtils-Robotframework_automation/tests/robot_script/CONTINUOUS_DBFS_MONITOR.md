# Continuous dBFS Monitor

This script continuously monitors the dBFS level of the Sound Blaster device and displays the changes in real-time.

## Features

- Continuous monitoring of audio levels
- Real-time dBFS measurement
- Optional real-time graph display
- Configurable monitoring interval and recording duration
- Audio detection status indication (above/below -60 dBFS threshold)

## Requirements

- Python 3.x
- Sound Blaster device properly configured
- Required Python packages:
  - numpy
  - matplotlib
  - pydub

## Installation

1. Ensure your Sound Blaster device is properly connected and configured
2. Install required Python packages:
   ```bash
   pip install numpy matplotlib pydub
   ```

## Usage

### Basic Usage
```bash
python3 continuous_dbfs_monitor.py
```

### Command Line Options
```bash
python3 continuous_dbfs_monitor.py [options]
```

Options:
- `-i INTERVAL`, `--interval INTERVAL`: Time interval between measurements in seconds (default: 1.0)
- `-d DURATION`, `--duration DURATION`: Duration of each recording in seconds (default: 5.0)
- `--no-graph`: Disable real-time graph display

### Examples

1. Monitor with default settings (1 second interval, 5 second recording):
   ```bash
   python3 continuous_dbfs_monitor.py
   ```

2. Monitor every 2 seconds with 3 second recordings:
   ```bash
   python3 continuous_dbfs_monitor.py -i 2 -d 3
   ```

3. Monitor without graph display:
   ```bash
   python3 continuous_dbfs_monitor.py --no-graph
   ```

4. Monitor with custom interval and duration, no graph:
   ```bash
   python3 continuous_dbfs_monitor.py -i 0.5 -d 2 --no-graph
   ```

## Output

The script will display real-time dBFS measurements in the console:
```
Starting continuous dBFS monitoring...
Press Ctrl+C to stop
--------------------------------------------------
[10:09:42] dBFS: -56.33 (AUDIO DETECTED)
[10:09:48] dBFS: -55.66 (AUDIO DETECTED)
[10:09:53] dBFS: -55.82 (AUDIO DETECTED)
```

If the graph is enabled, it will show a real-time plot of dBFS levels over time with a threshold line at -60 dBFS.

## Stopping the Monitor

Press `Ctrl+C` to stop the monitoring process.

## Configuration

The script uses the device configuration from `tests/robot_script/BTS_Device_Settings.py`. Make sure your Sound Blaster device is properly configured in this file.

## Troubleshooting

1. **No audio detected**: Check that your Sound Blaster device is properly connected and configured
2. **Low dBFS values**: Adjust the input gain on your Sound Blaster device
3. **Recording errors**: Verify that the device is not being used by another application

## License

This script is part of the QSUtils project and is subject to the same licensing terms.
