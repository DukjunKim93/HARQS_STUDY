# Sound01 Setup Guide for Sound BlasterX G6 Microphone

## Device Configuration

The Sound01 device is properly configured in the system to use the Sound BlasterX G6 microphone with Linux-compatible device names:

### Configuration Details
- **Device Name**: Sound01
- **Type**: Sound
- **Microphone**: alsa_input.usb-Creative_Technology_Ltd_Sound_BlasterX_G6_D800544758X-00.analog-stereo
- **Sound Device ID**: 2
- **Connection Type**: device_index
- **Connection Info**: alsa_input.usb-Creative_Technology_Ltd_Sound_BlasterX_G6_D800544758X-00.analog-stereo

### Configuration Files
The device is configured in:
1. `tests/robot_script/BTS_Device_Settings.py`
2. `tests/robot_script/BTS_Device_Settings.ini`

## System Requirements

To ensure proper operation on Linux, the following packages must be installed:

### Required Packages
```bash
# Install ffmpeg for audio processing
sudo apt install -y ffmpeg

# Install sox for audio analysis
sudo apt install -y sox

# Install Python packages
pip install ffmpeg-python
```

### Verification Commands
Check that the required tools are installed:
```bash
ffmpeg -version
sox --version
```

## Code Modifications

The BTS_Sound library has been modified to work properly on Linux systems:

### Path Configuration
The library now automatically detects the operating system and uses appropriate paths:
- **Linux/Unix**: Uses system-installed `ffmpeg` and `sox` commands
- **Windows**: Uses bundled Windows executables

This modification was made in the `BTS_Sound.py` file in both locations:
1. `robot-scripts-package/BTS/BTS_Sound.py`
2. `.venv/lib/python3.12/site-packages/BTS/BTS_Sound.py`

## Verification Steps

### 1. Check Device Configuration
Run the test script to verify the device is properly configured:
```bash
python test_sound01.py
```

Expected output:
```
✓ Sound01 is correctly configured for Sound BlasterX G6 microphone
✓ All required fields are present
```

### 2. Initialize Device with BTS_Sound Library
Verify that the device can be initialized with the BTS_Sound library:
```bash
python test_sound_device.py
```

Expected output:
```
✓ Sound01 device successfully initialized with BTS_Sound library
✓ Device name matches expected Sound BlasterX G6 microphone
```

## Using Sound01 for TV Mute Detection

To verify that the TV is not muted when using Sound01, you can use the following approaches:

### Robot Framework Test
Use the provided `sound_test.robot` file which includes tests for:
1. Verifying Sound01 device configuration
2. Testing audio recording from the Sound BlasterX G6 microphone
3. Checking that TV audio is not muted

Run with:
```bash
robot sound_test.robot
```

### Manual Verification
In your test scripts, you can use the "TV Should Not Mute" keyword which:
1. Records audio from the Sound01 device
2. Checks if the recording is mute
3. Fails the test if the TV is muted

## Key Points for Proper Operation

1. **Device Recognition**: The Sound BlasterX G6 must be properly connected to the system and recognized by the audio subsystem.

2. **Device Selection**: The BTS_Sound library automatically uses the device specified in the Sound01 configuration.

3. **Mute Detection**: The system uses audio analysis to determine if the TV is muted:
   - Records a short audio sample (typically 10 seconds)
   - Analyzes the audio for silence
   - Reports failure if the audio is determined to be muted

4. **TV Audio Requirements**: For accurate mute detection:
   - The TV must be playing audio content
   - The volume should be at a reasonable level
   - The Sound BlasterX G6 microphone should be positioned to capture TV audio

## Troubleshooting

### Common Issues
1. **Device Not Found**: Ensure the Sound BlasterX G6 is properly connected via USB
2. **Permission Issues**: Make sure the user has permission to access audio devices
3. **Audio Quality**: Position the microphone appropriately to capture TV audio

### Verification Commands
Check system audio devices:
```bash
arecord -l  # List capture devices
aplay -l    # List playback devices
```

Check PulseAudio sinks:
```bash
pactl list sinks short
```

## Conclusion

The Sound01 device is properly configured for the Sound BlasterX G6 microphone and ready to use for TV audio verification. The system will correctly detect if the TV is muted by analyzing audio captured through this device, ensuring that "Soundbar 소리 출력 확인" (Soundbar sound output verification) works as expected.

The modifications made to use system-installed ffmpeg and sox on Linux systems ensure compatibility with the Linux environment while maintaining the existing functionality on Windows systems.
