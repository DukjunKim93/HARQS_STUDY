# Audio dB Level Display and Analysis

## Overview
This document describes the implementation of detailed dB level display and analysis functionality for audio testing in the QSUtils project. The system provides comprehensive audio analysis with dBFS measurements and threshold-based pass/fail decisions.

## Key Features

### 1. Detailed Audio Analysis
The system provides comprehensive analysis including:
- File information (duration, sample rate, channels, bit depth)
- Amplitude analysis (maximum, RMS, mean, standard deviation)
- dBFS level measurements (peak and RMS)
- Time-based segment analysis
- Threshold comparison results

### 2. dB Level Display Examples

From our analysis of a recorded file, here's what the output looks like:

```
Audio Analysis Report for: /tmp/threshold_test_20260116_085352.wav
============================================================
Analysis Time: 2026-01-16 10:02:30

FILE INFORMATION:
  Duration: 5.02 seconds
  Sample Rate: 48000 Hz
  Channels: 2
  Sample Width: 16 bits
  File Size: 963770 bytes

AMPLITUDE ANALYSIS:
  Maximum Amplitude: 3
  RMS Amplitude: 0
  Mean Amplitude: -0.67
  Std Deviation: 0.71

DECIBEL LEVELS (dBFS):
  Peak Level: -80.77 dBFS
  RMS Level: -inf dBFS

TIME-BASED ANALYSIS:
  Analyzing 5 one-second segments (stereo):
    Segment  1 ( 0- 1s): L=-80.77 dBFS | R=-80.77 dBFS
    Segment  2 ( 1- 2s): L=-80.77 dBFS | R=-80.77 dBFS
    Segment  3 ( 2- 3s): L=-80.77 dBFS | R=-80.77 dBFS
    Segment  4 ( 3- 4s): L=-80.77 dBFS | R=-80.77 dBFS
    Segment  5 ( 4- 5s): L=-80.77 dBFS | R=-80.77 dBFS

THRESHOLD COMPARISON:
   -70.0 dBFS: FAIL (Peak: -80.77 dBFS)
   -60.0 dBFS: FAIL (Peak: -80.77 dBFS)
   -50.0 dBFS: FAIL (Peak: -80.77 dBFS)
   -40.0 dBFS: FAIL (Peak: -80.77 dBFS)
   -30.0 dBFS: FAIL (Peak: -80.77 dBFS)

SUMMARY:
  Overall Peak Level: -80.77 dBFS
  Result: NO SIGNIFICANT AUDIO (Below -60 dBFS threshold)
```

### 3. JSON Data Export
The analysis results are also saved in JSON format for programmatic access:

```json
{
  "file": "/tmp/threshold_test_20260116_085352.wav",
  "duration": 5.019229166666666,
  "sample_rate": 48000,
  "channels": 2,
  "max_amplitude": 3,
  "rms_amplitude": 0,
  "peak_dbfs": -80.76630852844073,
  "rms_dbfs": null,
  "threshold_result": false
}
```

## Robot Framework Integration

### Test Case Example
The dB level display is integrated into Robot Framework tests:

```robotframework
Display Audio dB Levels
    [Documentation]    Record audio and display dB level information
    [Setup]    Set Sound Device
    
    # Test with different durations
    @{test_durations} =    Create List    2s    3s    5s
    
    FOR    ${duration}    IN    @{test_durations}
        Log    \n--- Testing ${duration} recording ---
        ${dbfs_level}    ${has_sound} =    Analyze Audio With DB Levels    ${duration}
        Log    Duration: ${duration} | dBFS: ${dbfs_level} | Result: ${has_sound}
    END
```

### Keyword Implementation
Custom keywords provide detailed dB level information:

```robotframework
Analyze Audio With DB Levels
    [Documentation]    Record audio and display detailed dB level information
    [Arguments]    ${duration}=3s    ${threshold}=-60.0
    ${timestamp} =    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${record_file} =    Set Variable    /tmp/db_test_${timestamp}.wav
    
    # Record audio
    Log    Starting ${duration} audio recording...
    SoundSensor.Sound Record    ${duration}    ${record_file}
    
    # Get dBFS level
    ${dbfs_level} =    SoundSensor.Sound Get DBFS    ${record_file}
    ${has_sound} =    SoundSensor.Sound Is Above Threshold    ${record_file}    ${threshold}
    
    # Log detailed information
    Log    Audio Analysis Results:
    Log    | File: ${record_file}
    Log    | dBFS Level: ${dbfs_level}
    Log    | Threshold: ${threshold} dBFS
    Log    | Audio Detected: ${has_sound}
```

## Threshold Comparison Results

The system can compare audio levels against multiple thresholds:

```
Threshold Comparison Results:
dBFS Level: -80.76630852844073
------------------------
Threshold -70.0: FAIL (Audio False)
Threshold -60.0: FAIL (Audio False)
Threshold -50.0: FAIL (Audio False)
Threshold -40.0: FAIL (Audio False)
Threshold -30.0: FAIL (Audio False)
```

## dB Level Interpretation Guide

| dBFS Level | Description | Typical Scenario |
|------------|-------------|------------------|
| -80.77 dBFS | Very Quiet | Silent environment, no audio source |
| -50.31 dBFS | Quiet Background | Minimal ambient noise |
| -16.33 dBFS | Normal Audio | Typical TV volume |
| -6.79 dBFS | Loud Audio | High TV volume |
| -2.35 dBFS | Very Loud | Maximum comfortable volume |

## Usage Examples

### Command Line Analysis
```bash
python db_level_analyzer.py
```

### Robot Framework Test Execution
```bash
python -m robot db_level_test.robot
```

### Direct Python Usage
```python
from BTS.BTS_Sound import BTS_Sound

sound = BTS_Sound()
sound.sound_set_device_name("alsa_input.usb-Creative_Technology_Ltd_Sound_BlasterX_G6_D800544758X-00.analog-stereo")

# Record audio
sound.sound_record("3s", "/tmp/test.wav")

# Get dBFS level
dbfs_level = sound.sound_get_dbfs("/tmp/test.wav")
print(f"Audio level: {dbfs_level} dBFS")

# Check against threshold
has_sound = sound.sound_is_above_threshold("/tmp/test.wav", -60.0)
print(f"Audio detected: {has_sound}")
```

## Conclusion

The dB level display and analysis system provides:
1. **Comprehensive Audio Analysis**: Detailed measurements of all audio characteristics
2. **Clear dBFS Display**: Easy-to-understand decibel level reporting
3. **Threshold-Based Testing**: Configurable pass/fail decisions
4. **Multiple Output Formats**: Console display, JSON export, and Robot Framework integration
5. **Time-Based Analysis**: Segment-by-segment audio level monitoring

This implementation enables precise audio testing with detailed dB level information, making it easier to diagnose audio issues and verify proper audio functionality in automated testing scenarios.
