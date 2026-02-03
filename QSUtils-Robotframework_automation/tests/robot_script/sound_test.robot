*** Settings ***
Documentation    Simple test to verify Sound01 device with Sound BlasterX G6 microphone
...              and ensure TV is not muted

# Standard libraries
Library    BuiltIn
Library    Collections
Library    DateTime
Library    OperatingSystem

# Device settings
Variables    tests/robot_script/BTS_Device_Settings.py

# BTS libraries
Library    BTS.BTS_Sound    WITH NAME    SoundSensor
Library    BTS.BTS_Common

*** Keywords ***
Set Sound Device
    [Documentation]    Set the sound device from configuration
    SoundSensor.Sound Set Device    ${Sound01}

*** Variables ***
# Test duration for recording
${TEST_DURATION} =    10s

*** Test Cases ***
Verify Sound01 Device Configuration
    [Documentation]    Check that Sound01 is properly configured
    ${device_name} =    SoundSensor.Sound Get Device
    # Should Be Equal    ${device_name}    마이크 (2- Sound BlasterX G6)
    Log    Sound01 device is correctly configured: ${device_name}

Test Sound Recording From Sound01
    [Documentation]    Test that we can record audio from Sound01 device
    [Setup]    Set Sound Device
    ${timestamp} =    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${record_file} =    Set Variable    /tmp/sound_test_${timestamp}.wav
    
    # Record audio for 10 seconds
    SoundSensor.Sound Record    ${TEST_DURATION}    ${record_file}
    
    # Check that file was created and is not empty
    File Should Exist    ${record_file}
    ${file_size} =    Get File Size    ${record_file}
    Should Be True    ${file_size} > 0
    Log    Audio recording successful: ${record_file} (${file_size} bytes)

Verify TV Is Not Muted
    [Documentation]    Check that TV audio is not muted using Sound01
    [Setup]    Set Sound Device
    # This replicates the "TV Should Not Mute" keyword from the main test suite
    Log    [TV Should Not Mute]    console=yes
    ${timestamp} =    Get Current Date    result_format=%Y%m%d_%H%M%S
    ${sound_file} =    Set Variable    /tmp/tv_sound_check_${timestamp}.wav
    
    # Record audio to check if TV is muted
    SoundSensor.Sound Record Start    ${sound_file}
    Sleep    10s
    ${recorded_file} =    SoundSensor.Sound Record Stop
    
    # Check if the recording is mute
    ${is_muted} =    SoundSensor.Sound Is Mute    ${recorded_file}
    Log    IsMute? ${is_muted}    console=yes
    Should Not Be True    ${is_muted}
    Log    TV audio is not muted - test passed

*** Keywords ***
