# Threshold-Based Audio Testing Implementation

## Overview
This document describes the implementation of threshold-based pass/fail logic for audio testing in the QSUtils project. The implementation allows for more flexible and reliable audio detection compared to the previous mute detection approach.

## Implementation Details

### 1. New BTS_Sound Library Method

A new method `sound_is_above_threshold` was added to the `BTS_Sound` class:

```python
@keyword(types={'filepath': str, 'threshold': float, 'direction_mode': str})
def sound_is_above_threshold(self, filepath, threshold=-60.0, direction_mode='ALL'):
    '''
    This API checks if the audio file's dBFS is above a specified threshold.
    Returns True if audio level is above threshold (indicating sound is present), False if below.
    Example:
     | ${has_sound} =   | SOUND IS ABOVE THRESHOLD   |  ${audio_path}  |  -50.0  |
    :param filepath: Path to the audio file
    :param threshold: dBFS threshold value (default: -60.0)
    :param direction_mode: Audio channel selection (default: 'ALL')
    :return: Boolean indicating if audio is above threshold
    '''
    dbfs = self.sound_get_dbfs(filepath, direction_mode)
    if dbfs is None:
        return False
    return dbfs > threshold
```

### 2. How It Works

1. **Audio Recording**: The system records audio for a specified duration using the configured sound device
2. **dBFS Calculation**: The maximum amplitude of the recorded audio is converted to dBFS (decibels relative to full scale)
3. **Threshold Comparison**: The dBFS value is compared against a configurable threshold
4. **Pass/Fail Decision**: 
   - PASS: If dBFS > threshold (audio detected above noise floor)
   - FAIL: If dBFS ≤ threshold (no significant audio detected)

### 3. Threshold Values

Based on our analysis, here are recommended threshold values:

| Scenario | Max Amplitude | dBFS | Recommendation |
|----------|---------------|------|----------------|
| Silent Environment | 3 | -80.77 | FAIL (threshold = -60.0) |
| Very Quiet Background | 100 | -50.31 | PASS (threshold = -60.0) |
| Normal TV Audio | 5000 | -16.33 | PASS (threshold = -60.0) |
| Loud TV Audio | 15000 | -6.79 | PASS (threshold = -60.0) |
| Very Loud Audio | 25000 | -2.35 | PASS (threshold = -60.0) |

### 4. Test Results Demonstration

Our testing shows that:
- In a silent environment, the maximum amplitude was only 3, resulting in -80.77 dBFS
- This would correctly FAIL with a threshold of -60.0 dBFS
- In a real testing scenario with actual audio, the dBFS would be much higher and PASS

### 5. Advantages Over Previous Approach

1. **More Reliable**: Uses amplitude-based detection rather than complex silence detection algorithms
2. **Configurable**: Threshold can be adjusted based on environment and requirements
3. **Simpler Logic**: Direct comparison rather than analyzing silence patterns
4. **Better for Automation**: More predictable results in automated testing

## Usage Examples

### Robot Framework Test Case
```robotframework
Verify TV Audio Present
    [Documentation]    Check that TV audio is present using threshold-based detection
    [Setup]    Set Sound Device
    ${timestamp} =    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${sound_file} =    Set Variable    /tmp/audio_check_${timestamp}.wav
    
    # Record audio to check if TV is producing sound
    SoundSensor.Sound Record    5s    ${sound_file}
    
    # Check if the recording has audio above threshold
    ${has_sound} =    SoundSensor.Sound Is Above Threshold    ${sound_file}    -60.0
    Log    Audio detected: ${has_sound}    console=yes
    Should Be True    ${has_sound}
    Log    TV audio is present - test passed
```

### Python Direct Usage
```python
from BTS.BTS_Sound import BTS_Sound

sound = BTS_Sound()
sound.sound_set_device_name("alsa_input.usb-Creative_Technology_Ltd_Sound_BlasterX_G6_D800544758X-00.analog-stereo")

# Record audio
sound.sound_record("5s", "/tmp/test.wav")

# Check if audio is above threshold
has_sound = sound.sound_is_above_threshold("/tmp/test.wav", -60.0)
if has_sound:
    print("PASS: Audio detected")
else:
    print("FAIL: No significant audio detected")
```

## dB Level Display and Analysis

The system also provides detailed dB level display and analysis functionality:

### Detailed Audio Analysis
- File information (duration, sample rate, channels, bit depth)
- Amplitude analysis (maximum, RMS, mean, standard deviation)
- dBFS level measurements (peak and RMS)
- Time-based segment analysis
- Threshold comparison results

### Example Output
```
DECIBEL LEVELS (dBFS):
  Peak Level: -80.77 dBFS
  RMS Level: -inf dBFS

TIME-BASED ANALYSIS:
  Analyzing 5 one-second segments (stereo):
    Segment  1 ( 0- 1s): L=-80.77 dBFS | R=-80.77 dBFS
    Segment  2 ( 1- 2s): L=-80.77 dBFS | R=-80.77 dBFS
    ...
```

## Conclusion

The threshold-based approach provides a more robust and configurable method for audio testing. It can be easily adjusted for different environments and requirements while providing consistent, predictable results for automated testing scenarios. The addition of detailed dB level display enhances the diagnostic capabilities of the system.
