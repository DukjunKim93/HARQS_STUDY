*** Settings ***
Documentation    Test to demonstrate dB level display in audio testing...              This test shows detailed dB level information during audio analysis

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

Analyze Audio With DB Levels
    [Documentation]    Record audio and display detailed dB level information
    [Arguments]    ${duration}=3s    ${threshold}=-60.0

    ${timestamp} =    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${record_file} =    Set Variable    /tmp/db_test_${timestamp}.wav

    # Record audio
    Log    Starting ${duration} audio recording...
    SoundSensor.Sound Record    ${duration}    ${record_file}

    # Check that file was created
    File Should Exist    ${record_file}
    ${file_size} =    Get File Size    ${record_file}
    Should Be True    ${file_size} > 0

    # Get dBFS level
    ${dbfs_level} =    SoundSensor.Sound Get DBFS    ${record_file}
    ${has_sound} =    SoundSensor.Sound Is Above Threshold    ${record_file}    ${threshold}

    # Log detailed information
    Log    Audio Analysis Results:
    Log    | File: ${record_file}
    Log    | File Size: ${file_size} bytes
    Log    | dBFS Level: ${dbfs_level}
    Log    | Threshold: ${threshold} dBFS
    Log    | Audio Detected: ${has_sound}

    # Show the dBFS level in the console for visibility
    IF    ${has_sound}
        Log    RESULT: PASS - Audio detected above threshold
    ELSE
        Log    RESULT: FAIL - No significant audio detected
    END

    RETURN    ${dbfs_level}    ${has_sound}

*** Test Cases ***
Display Audio dB Levels
    [Documentation]    Record audio and display dB level information
    [Setup]    Set Sound Device

    Log    Audio dB Level Display Test
    Log    ========================

    # Test with different durations
    @{test_durations} =    Create List    2s    3s    5s

    FOR    ${duration}    IN    @{test_durations}
        Log    \n--- Testing ${duration} recording ---
        ${dbfs_level}    ${has_sound} =    Analyze Audio With DB Levels    ${duration}
        Log    Duration: ${duration} | dBFS: ${dbfs_level} | Result: ${has_sound}
    END

    Log    \nTest completed - dB level information displayed for all recordings

Compare Different Thresholds
    [Documentation]    Test audio detection with different threshold values
    [Setup]    Set Sound Device

    Log    Threshold Comparison Test
    Log    ======================

    ${timestamp} =    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${record_file} =    Set Variable    /tmp/threshold_comp_${timestamp}.wav

    # Record audio once
    SoundSensor.Sound Record    3s    ${record_file}

    # Get dBFS level
    ${dbfs_level} =    SoundSensor.Sound Get DBFS    ${record_file}
    Log    Audio file dBFS level: ${dbfs_level}

    # Test with different thresholds
    @{thresholds} =    Create List    -70.0    -60.0    -50.0    -40.0    -30.0

    Log    \nThreshold Comparison Results:
    Log    dBFS Level: ${dbfs_level}
    Log    ------------------------

    FOR    ${threshold}    IN    @{thresholds}
        ${above_threshold} =    SoundSensor.Sound Is Above Threshold    ${record_file}    ${threshold}
        ${result} =    Set Variable If    ${above_threshold}    PASS    FAIL
        Log    Threshold ${threshold}: ${result} (Audio ${above_threshold})
    END
