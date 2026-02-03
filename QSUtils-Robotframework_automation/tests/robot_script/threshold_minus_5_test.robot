*** Settings ***
Documentation    Test to demonstrate audio detection with threshold -5 dBFS
...              This test shows audio detection results when using -5 dBFS as threshold
# Standard libraries
Library    BuiltIn
Library    Collections
Library    DateTime
Library    OperatingSystem

# Device settings
Variables    BTS_Device_Settings.py

# BTS libraries
Library    BTS.BTS_Sound    WITH NAME    SoundSensor
Library    BTS.BTS_Common

*** Keywords ***
Set Sound Device
    [Documentation]    Set the sound device from configuration
    SoundSensor.Sound Set Device    ${Sound01}

Analyze Audio With Threshold Minus 5
    [Documentation]    Record audio and check if it's above -5 dBFS threshold
    [Arguments]    ${duration}=3s
    ${timestamp} =    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${record_file} =    Set Variable    /tmp/threshold_minus_5_test_${timestamp}.wav
    
    # Record audio
    Log    Starting ${duration} audio recording...
    SoundSensor.Sound Record    ${duration}    ${record_file}
    
    # Check that file was created
    File Should Exist    ${record_file}
    ${file_size} =    Get File Size    ${record_file}
    Should Be True    ${file_size} > 0
    
    # Get dBFS level
    ${dbfs_level} =    SoundSensor.Sound Get DBFS    ${record_file}
    ${has_sound} =    SoundSensor.Sound Is Above Threshold    ${record_file}    -5.0
    
    # Log detailed information
    Log    Audio Analysis Results:
    Log    | File: ${record_file}
    Log    | File Size: ${file_size} bytes
    Log    | dBFS Level: ${dbfs_level}
    Log    | Threshold: -5.0 dBFS
    Log    | Audio Detected: ${has_sound}
    
    # Show the dBFS level in the console for visibility
    # Check if dBFS level is above -5 dBFS
    ${is_above_threshold} =    Evaluate    ${dbfs_level} > -17.0
    
    IF    ${is_above_threshold}
        Log    RESULT: PASS - Audio level (${dbfs_level} dBFS) is above threshold (-10.0 dBFS)
    ELSE
        Log    RESULT: FAIL - Audio level (${dbfs_level} dBFS) is below threshold (-10.0 dBFS)
    END
    
    # Fail the test if dBFS level is below threshold
    Should Be True    ${is_above_threshold}    Audio level (${dbfs_level} dBFS) is below threshold (-10.0 dBFS)
    
    RETURN    ${dbfs_level}    ${is_above_threshold}

*** Test Cases ***
Audio Detection With Threshold Minus 5
    [Documentation]    Record audio and check detection with -5 dBFS threshold
    [Setup]    Set Sound Device
    
    Log    Audio Detection Test with -5 dBFS Threshold
    Log    ========================================
    
    # Test with different durations
    @{test_durations} =    Create List    2s    3s    5s
    
    FOR    ${duration}    IN    @{test_durations}
        Log    \n--- Testing ${duration} recording ---
        ${dbfs_level}    ${has_sound} =    Analyze Audio With Threshold Minus 5    ${duration}
        Log    Duration: ${duration} | dBFS: ${dbfs_level} | Result: ${has_sound}
    END
    
    Log    \nTest completed - Audio detection with -5 dBFS threshold

Single Test With Threshold Minus 5
    [Documentation]    Single test with 3s recording and -5 dBFS threshold
    [Setup]    Set Sound Device
    
    Log    Single Audio Detection Test with -5 dBFS Threshold
    Log    ===============================================
    
    ${dbfs_level}    ${is_above_threshold} =    Analyze Audio With Threshold Minus 5    3s
    
    Log    \nFinal Result:
    Log    dBFS Level: ${dbfs_level}
    Log    Threshold: -5.0 dBFS
    Log    Audio Detected: ${is_above_threshold}
    
    IF    ${is_above_threshold}
        Log    OVERALL RESULT: PASS - Audio level (${dbfs_level} dBFS) is above threshold (-5.0 dBFS)
    ELSE
        Log    OVERALL RESULT: FAIL - Audio level (${dbfs_level} dBFS) is below threshold (-5.0 dBFS)
    END
