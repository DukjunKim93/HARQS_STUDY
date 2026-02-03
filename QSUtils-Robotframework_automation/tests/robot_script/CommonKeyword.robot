#*** Settings ***
# Metadata        Version        2021.03.05
#
#Library           BTS.BTS_Image
#Library           BTS.BTS_Video
#Library           BTS.BTS_Serial
#Library           BTS.BTS_WebCam
#Library           BTS.BTS_PatternGenerator
#Library           BTS.BTS_ATHub
#Library           BTS.BTS_Sdb
#Library           BTS.BTS_OCR

#Library           BuiltIn
#Library           Collections
#Library           DateTime

*** Keywords ***
### Image / Video   ###
Wait Image by SDB
    [Documentation]  This keyword is used to compare user provided reference image file with SDB captured image.\n
    ...    Library   *BTS.BTS_Sdb* and *BTS.BTS_Image* are required.\n
    ...    |  Wait Image by SDB  |  ${ReferenceFile}  |     |
    ...    |  Wait Image by SDB  |  ${ReferenceFile}  |  3  |
    ...    ${repeat} argument takes integer value for iteration of image capturing from SDB and comparing it with reference image file. \n
    ...    Default repeat argument value is 1.\n
    ...    This keyword will get passed if both the images are same else it will be failed.
    
    [Arguments]      ${ReferenceFile}       ${repeat}=1
    FOR    ${i}    IN RANGE    ${repeat}
      Sdb Get Current Screen    ${EXECDIR}
      ${ret} =    Image Compare    ${ReferenceFile}     ${EXECDIR}${/}dump_screen.png
      Log To Console    ** result ** ${ret}
      Exit For Loop If    ${ret} == True
    END
    Should Be True    ${ret}

Video Record
    [Documentation]  This keyword is used to record video from webcam and return filename with robot variable ${RecordFile} which can be used globally within test suite.
    ...    |  ${recordedfilepath} =  |  Video Record  |  ${time}  |  ${videofilename}  |  ${show_timestamp}  |  \# Returns full path.  |
    ...    |  ${recordedfilepath} =  |  Video Record  |  10s  |  TestVideo.mp4  |  ${True}  |
    [Arguments]      ${time}=10       ${videofilename}=${EMPTY}    ${show_timestamp}=On    
    ${expected_text} =      Run Keyword If  "${videofilename}"=="${EMPTY}"      Webcam Videorecordstart    show_timestamp=${show_timestamp}
    ...        ELSE        Webcam Videorecordstart    ${videofilename}       show_timestamp=${show_timestamp}
    sleep     ${time}
    ${filename}=    Webcam Videorecordstop
    ${RecordFile}=       Set Variable  ${filename}
    Set Global Variable        ${RecordFile}
    File Should Exist          ${RecordFile}
    Log To Console       Success Recording : ${RecordFile}
    Return From Keyword        ${RecordFile}

### OCR  ###
Get Text By OCR
    [Documentation]  This keyword is used to get text from target image path provided in argument and return text based on reference OCR image data like region, inverse, psm etc.
    ...    Library *BTS.BTS_Ocr* and *Collections* are required.
    ...  |  ${text} =  |  Get Text By OCR  |  ${ref_ocr_data}  |  ${target_image_path}  |  /# Returns OCR text  |  
    [Arguments]     ${ref_ocr_data}     ${target_image_path}
    #${image_path} =      GET FROM DICTIONARY    ${ref_ocr_data}      captured_path    
    ${region} =          Get From Dictionary    ${ref_ocr_data}      region
    ${lang} =            Get From Dictionary    ${ref_ocr_data}      language
    ${inverse} =         Get From Dictionary    ${ref_ocr_data}      invert_image
    ${psm} =             Get From Dictionary    ${ref_ocr_data}      page_seg_mode
    ${expected_text} =      Get From Dictionary    ${ref_ocr_data}      text

    Ocr Set Language    ${lang}            
    ${ret} =        Ocr Read Text From Imagefile By Region       ${target_image_path}    ${region}    ${inverse}    ${psm}
    Return From Keyword          ${ret}

OCR Check
    [Documentation]  This keyword is used to compare text from target image provided in argument with reference OCR image based on expected text passed in argument.
    ...    This keyword will be passed if text matches in target image path based on reference OCR data.
    ...    Library *BTS.BTS_Ocr* is required.
    ...  |  OCR Check  |  ${ref_ocr_data}  |  ${target_image_path}  |
    ...  |  OCR Check  |  ${ref_ocr_data}  |  ${target_image_path}  |  Expected text  |

    [Arguments]     ${ref_ocr_data}      ${target_image_path}     ${expected_text}=${EMPTY}
    ${recognized_text} =    Get Text By OCR       ${ref_ocr_data}      ${target_image_path}
    ${expected_text} =      Run Keyword If  "${expected_text}"=="${EMPTY}"      Get From Dictionary    ${ref_ocr_data}    text
    ...        ELSE        Set Variable    ${expected_text}
    Log To Console      ** Expected : [${expected_text}]. Result : [${recognized_text}]
    ${ret} =       Evaluate    "${recognized_text}"=="${expected_text}"
    Log       [OCR Check] Result is <${ret}>       console=yes
    Should Be True             ${ret}

Wait OCR by SDB
    [Documentation]  This keyword is used compare text from sdb captured image based on OCR image provided in argument.
    ...    This keyword will be passed if text matches in sdb captured image based on OCR image text
    ...    Library *BTS.BTS_Sdb* and *Collections* are required.
    ...    |  Wait OCR by SDB  |  ${ref_ocr_data}  |
    ...    |  Wait OCR by SDB  |  ${ref_ocr_data}  |  3  |
    ...    |  Wait OCR by SDB  |  ${ref_ocr_data}  |  2  |  ${expected_text}  |
    [Arguments]     ${ref_ocr_data}        ${repeat}=1        ${expected_text}=${EMPTY}
    FOR    ${i}    IN RANGE    ${repeat}
        ${connectStatus}=   Sdb Isconnected
        Sleep    1s
        Run Keyword If  ${connectStatus} == True     Sdb Get Current Screen      ${EXECDIR}
        ${recognized_text} =    Get Text By OCR       ${ref_ocr_data}      ${EXECDIR}${/}dump_screen.png
        ${expected_text} =      Run Keyword If  "${expected_text}"=="${EMPTY}"      Get From Dictionary    ${ref_ocr_data}    text
        ...        ELSE        Set Variable    ${expected_text}
        Log       ** Expected : [${expected_text}]. Result : [${recognized_text}]        console=yes
        ${ret} =       Evaluate    "${recognized_text.replace("\r\n"," ")}"=="${expected_text}"
        Log       [Wait OCR] Result is <${ret}>       console=yes
        Exit For Loop If    ${ret} == True
    END
    Should Be True     ${ret}

Wait OCR by CAM
    [Documentation]  This keyword is used compare text from webcam captured image based on OCR image provided in argument.\n
    ...    This keyword will be passed if text matches in webcam captured image based on OCR image text.\n
    ...    Library *BTS.BTS_Webcam* is required.
    ...    |  Wait OCR by CAM  |  ${ref_ocr_data}  |
    ...    |  Wait OCR by CAM  |  ${ref_ocr_data}  |  3  |
    ...    |  Wait OCR by CAM  |  ${ref_ocr_data}  |  3  |  ${expected_text}  |
    [Arguments]     ${ref_ocr_data}        ${repeat}=1        ${expected_text}=${EMPTY}
    FOR    ${i}    IN RANGE    ${repeat}
        ${CaptureFile}=     Webcam Captureimage
        Sleep    1s
        ${recognized_text} =    Get Text By OCR       ${ref_ocr_data}      ${CaptureFile}
        ${expected_text} =      Run Keyword If  "${expected_text}"=="${EMPTY}"      Get From Dictionary    ${ref_ocr_data}    text
        ...        ELSE        set variable    ${expected_text}
        Log       ** Expected : [${expected_text}]. Result : [${recognized_text}]        console=yes
        ${ret} =       Evaluate    """${recognized_text.replace("\n"," ")}"""=="${expected_text}"
        Log       [Wait OCR] Result is <${ret}>       console=yes
        Exit For Loop If    ${ret} == True
    END
    Should Be True     ${ret}

Wait Until Assigned Datetime
    [Documentation]  This keyword is used to wait until datetime.\n
    ...    Library *DateTime* is required.
    ...    |  Wait Until Assigned Datetime  |  ${until datetime}  |  
    ...    |  Wait Until Assigned Datetime  |  ${until datetime}  |  10s  |
    [Arguments]  ${until datetime}      ${log interval}=1m
    ${current datetime}     Get Current Date
    Log    Start Waiting (current datetime: ${current datetime}/ until: ${until datetime})     console=yes
    FOR    ${i}    IN RANGE    999999
        ${current datetime}     Get Current Date
        ${next log datetime}    Add Time To Date        ${current datetime}     ${log interval}
        Exit For Loop If    '${next log datetime}' > '${until datetime}'
        Log     Waiting Until Assigned Datetime (current datetime: ${current datetime}/ until: ${until datetime})       console=yes
        Sleep   ${log interval}
    END
    Wait Until Keyword Succeeds     ${log interval}     1s      Should Be Past      ${until datetime}
    ${current datetime}     Get Current Date
    Log    End Waiting (current datetime: ${current datetime}/ until: ${until datetime})        console=yes

Should Be Past
    [Documentation]  Fails if the given datetime is not past.\n
    ...    Library *DateTime* is required.
    ...    |  Should Be Past  |  ${datetime}  |
    [Arguments]  ${datetime}
    ${current datetime}     Get Current Date
    Should Be True      "${datetime}" < "${current datetime}"
	
SleepRandomSeconds
	[Documentation]    Sleep for random seconds
	...    Sleep a randomly selected seconds from range(MinSeconds, MaxSeconds, step).
	...    | SleepRandomSeconds  |   11  |  19  | 
	...    | SleepRandomSeconds  |   3   |  100  |   3  | 
	...    | Repeat Keyword      |   10  |  SleepRandomSeconds  |  3  |  100  |  3  |

	[Arguments]    ${MinSeconds}    ${MaxSeconds}    ${Step}=1

	${time} =    Set Variable    ${{random.randrange(${MinSeconds}, ${MaxSeconds}, ${Step})}}
	log    Sleep ${time}    console=yes
	Sleep    ${time}
	
SleepRandomMilliSeconds
    [Documentation]    Sleep for random milliseconds.\n
    ...    Sleep a randomly selected seconds from range(MinMilliSeconds, MaxMilliSeconds, step).
    ...    | SleepRandomMilliSeconds  |   500  |  1500  |    |
    ...    | SleepRandomMilliSeconds  |   300   |  900  |   30  | 
    ...    | Repeat Keyword      |   10  |  SleepRandomMilliSeconds  |   300   |  900  | 

    [Arguments]    ${MinMilliSeconds}    ${MaxMilliSeconds}    ${Step}=1
    
    ${time} =    Set Variable    ${{random.randrange(${MinMilliSeconds}, ${MaxMilliSeconds}, ${Step})}}
    log    Sleep ${time}ms    console=yes
    Sleep    ${time}ms
    
Sleep Timing
    [Documentation]
    ...    [Documentation]    Sleep variable time belong to Runner's repeat type. Using Robot Framework's time value.
    ...    
    ...    *Library  DateTime* is required.
    ...    
    ...    |  Sleep Timing  |  900ms  |  50  |   1 hour 10 minutes    | 
   
    [Arguments]    ${MinValue}    ${DefaultValue}    ${MaxValue}
    
    ${min} =    Convert Time    ${MinValue}
    ${default} =    Convert Time    ${DefaultValue}
    ${max} =    Convert Time    ${MaxValue}
    
    ${val} =    Get Value In Range    ${{1000*${min}}}    ${{1000*${default}}}    ${{1000*${max}}}
    Log    Sleep ${val} ms   console=yes
    Sleep    ${val}ms

Sleep Timing Seconds   
    [Documentation]    Sleep variable seconds belong to Runner's repeat types.   
    ...        |  Sleep Timing Seconds  |  3  |  15  |   30    | 
    [Arguments]    ${MinValue}    ${DefaultValue}    ${MaxValue}
    ${val} =    Get Value In Range    ${MinValue}    ${DefaultValue}    ${MaxValue}
    Log    Sleep ${val} seconds    console=yes
    Sleep    ${val}

Sleep Timing MilliSeconds
    [Documentation]    Sleep variable milliseconds belong to Runner's repeat types.
    ...        |  Sleep Timing Milliseconds    |  900  |  5000  |   20000    |     
    [Arguments]    ${MinValue}    ${DefaultValue}    ${MaxValue}
    ${val} =    Get Value In Range    ${MinValue}    ${DefaultValue}    ${MaxValue}
    Log    Sleep ${val} ms    console=yes
    Sleep    ${val}ms
    
Get Value In Range
    [Documentation]    Return integer number between MinValue to MaxValue. Number changes belong to Runner's repeat type.
    ...   |  ${val} =   |   Get Value In Range   |   3   |   10   |   200   |
    ...   |  Sleep      |   ${val}  | 
    ...    
    ...    This keyword is related to BTS Runner's repeat option
    ...    When Runner send related variables (RunnerTCRepeatType, RunnerTCRepeatValue, isRunnerTCRepeatIndex),
    ...    calcuated value is returned.
    ...    
    ...    |           | Min   | Default |  Max  |
    ...    | Default   |       |    o    |       |
    ...    | Increase  |       |    o    | ----o |
    ...    | Decrease  | o---- |    o    |       |
    ...    | Randomize | ooo   |    O    |  ooo  |
    ...    
    ...    Each step value is automatically divided.\n
    ...    * 'Time Randomize' is not strict random. First execution(RepeatIndex==1) uses 'Default' value.

    [Arguments]    ${MinValue}    ${DefaultValue}    ${MaxValue}
        
    ${isRunnerTCRepeatType} =    Run Keyword And Return Status    Variable Should Exist    ${RunnerTCRepeatType}
    ${isRunnerTCRepeatValue} =    Run Keyword And Return Status    Variable Should Exist    ${RunnerTCRepeatValue}
    ${isRunnerTCRepeatIndex} =    Run Keyword And Return Status    Variable Should Exist    ${RunnerTCRepeatIndex}
    # Log to console    [RunnerTCRepeatType:${isRunnerTCRepeatType}, RunnerTCRepeatValue:${isRunnerTCRepeatValue}, RunnerTCRepeatIndex:${isRunnerTCRepeatIndex}]
    
    Run Keyword If    ${MinValue}>${DefaultValue}    Fail    {MinValue} > {DefaultValue}
    Run Keyword If    ${DefaultValue}>${MaxValue}    Fail    {DefaultValue} > {MaxValue}
    
    Return From Keyword If    ${MinValue}==${MaxValue}    ${DefaultValue}    
    
    Return From Keyword If      ${isRunnerTCRepeatType}==${False}    ${DefaultValue}
    Return From Keyword If      ${isRunnerTCRepeatValue}==${False}    ${DefaultValue}
    Return From Keyword If      ${isRunnerTCRepeatIndex}==${False}    ${DefaultValue} 
    Return From Keyword If      '${RunnerTCRepeatType}'=='Default'    ${DefaultValue}
    Return From Keyword If    ${RunnerTCRepeatValue}<=1    ${DefaultValue}    
    
    Run Keyword If    '${RunnerTCRepeatType}'=='Randomize' and ${RunnerTCRepeatIndex}==1    Return From Keyword    ${DefaultValue}
    ${randval} =    Run Keyword If    '${RunnerTCRepeatType}'=='Randomize'    GetRandomRangeValue    ${MinValue}    ${MaxValue}    
    # Log     randval : ${randval}
    Run Keyword If    None!=${randval}    Return From Keyword    ${randval}
    
    ${incval} =    Run Keyword If    '${RunnerTCRepeatType}'=='Increase'    GetIncreaseRangeValue    ${DefaultValue}    ${MaxValue}
    # Log     incval : ${incval}    
    Run Keyword If    None!=${incval}    Return From Keyword    ${incval}

    ${decval} =    Run Keyword If    '${RunnerTCRepeatType}'=='Decrease'    GetDecreaseRangeValue    ${MinValue}    ${DefaultValue}
    # Log     decval : ${decval}    
    Run Keyword If    None!=${decval}    Return From Keyword    ${decval}
        
    RETURN    ${DefaultValue}
    
GetRandomRangeValue
    [Arguments]    ${MinValue}    ${MaxValue}
    ${randtime} =    Set Variable    ${{random.randrange(${MinValue}, ${MaxValue})}}
    Log to console    randtime : ${randtime}    console=yes
    RETURN    ${randtime}
    
GetIncreaseRangeValue
    [Arguments]    ${Defalt}    ${MaxValue}
    ${step} =    Set Variable    ${{(${MaxValue}-${Defalt})/(${RunnerTCRepeatValue}-1)}}
    ${value} =    Set Variable    ${{${Defalt}+(${RunnerTCRepeatIndex}-1)*${step}}}
    
    ${value} =    Convert To Integer    ${value}    
    Log to console   increasevalue : ${value}
    RETURN    ${value}

GetDecreaseRangeValue
    [Arguments]    ${MinValue}    ${Defalt}
    ${step} =    Set Variable    ${{(${Defalt}-${MinValue})/(${RunnerTCRepeatValue}-1)}}
    ${value} =    Set Variable    ${{${Defalt}-(${RunnerTCRepeatIndex}-1)*${step}}}

    ${value} =    Convert To Integer    ${value}    
    RETURN    ${value}

Is BT Speaker
    [Arguments]    ${speaker_type}

    ${ret} =    Run Keyword If    ${speaker_type} in [3, 5, 6]    Set Variable     ${True}
    ...         ELSE                                                    Set Variable     ${False}
    return from keyword     ${ret}


Get TV Volume Via SDB
    ${speaker_selection_cmd}    Set Variable    vconftool get file/private/sound/feature/SpeakerSelection
    ${tv_get_volume_cmd}    Set Variable    vconftool get file/private/sound/volume/Master
    ${bt_get_volume_cmd}    Set Variable    vconftool get db/btapp/cur_spk_vol_level

    ${speaker_type} =    sdb sendshellcmd    ${speaker_selection_cmd}

    ${speaker_type}    get regexp matches    ${speaker_type}    value (.*?) ([0-9]+)    2
    ${is_bt} =    Is BT Speaker    ${speaker_type}[0]

    ${ret}    Run Keyword If    ${is_bt}    sdb sendshellcmd    ${bt_get_volume_cmd}
    ...       ELSE                          sdb sendshellcmd    ${tv_get_volume_cmd}

    ${ret}    get regexp matches    ${ret}    value (.*?) ([0-9]+)    2
    return from keyword    ${ret}[0]

Get TV Volume Via DebugShell
    ${debugshell_connection}    debugshell isconnected
    ${speaker_selection_cmd}    Set Variable    vconftool get file/private/sound/feature/SpeakerSelection
    ${tv_get_volume_cmd}    Set Variable    vconftool get file/private/sound/volume/Master
    ${bt_get_volume_cmd}    Set Variable    vconftool get db/btapp/cur_spk_vol_level
    Run Keyword If    ${debugshell_connection}    debugshell enter shellmode

    ${speaker_type} =    debugshell sendcommandandwaitkeyword    ${speaker_selection_cmd}    value =    5

    ${speaker_type}    get regexp matches    ${speaker_type}    value (.*?) ([0-9]+)    2
    log    ${speaker_type}    console=yes
    ${is_bt} =    Is BT Speaker    ${speaker_type}[0]


    ${ret}    Run Keyword If    ${is_bt}    debugshell sendcommandandwaitkeyword    ${bt_get_volume_cmd}    value =    5
    ...       ELSE                          debugshell sendcommandandwaitkeyword    ${tv_get_volume_cmd}    value =    5

    ${ret}    get regexp matches    ${ret}    value (.*?) ([0-9]+)    2
    return from keyword    ${ret}[0]

Set TV Volume Via SDB
    [Arguments]    ${volume}    ${retry}=1
    ${speaker_selection_cmd}    Set Variable    vconftool get file/private/sound/feature/SpeakerSelection
    ${cur_vol}    Get TV Volume Via SDB
    ${target_vol}    evaluate    ${volume} - ${cur_vol}
    log    target_vol: ${target_vol}    console=yes
    ${is_positive}      evaluate    ${target_vol} >= 0
    ${vol_count}    Set variable    ${target_vol.__abs__()}
    log     current volume : ${cur_vol}    console=yes
    Run Keyword If    ${is_positive}    keysender sendkey    KEY_VOLUP      repeat=${vol_count}
    ...      ELSE                       keysender sendkey    KEY_VOLDOWN    repeat=${vol_count}

    ${cur_vol}    Get TV Volume Via SDB
    log     current volume : ${cur_vol}    console=yes

    ${next} =    Evaluate    ${retry} - 1
    ${done} =    Evaluate    ${volume} == ${cur_vol}
    Run Keyword If    ${retry} > 0    Run Keyword If    ${done} == ${False}    Set TV Volume Via SDB    ${volume}    ${next}

Set TV Volume Via DebugShell
    [Arguments]    ${volume}    ${retry}=1
    ${speaker_selection_cmd}    Set Variable    vconftool get file/private/sound/feature/SpeakerSelection
    ${cur_vol}    Get TV Volume Via DebugShell
    ${target_vol}    evaluate    ${volume} - ${cur_vol}
    log    target_vol: ${target_vol}    console=yes
    ${is_positive}      evaluate    ${target_vol} >= 0
    ${vol_count}    Set variable    ${target_vol.__abs__()}
    log     current volume : ${cur_vol}    console=yes
    Run Keyword If    ${is_positive}    keysender sendkey    KEY_VOLUP      repeat=${vol_count}
    ...      ELSE                       keysender sendkey    KEY_VOLDOWN    repeat=${vol_count}

    ${cur_vol}    Get TV Volume Via DebugShell
    log     current volume : ${cur_vol}    console=yes

    ${next} =    Evaluate    ${retry} - 1
    ${done} =    Evaluate    ${volume} == ${cur_vol}
    Run Keyword If    ${retry} > 0    Run Keyword If    ${done} == ${False}    Set TV Volume Via DebugShell    ${volume}    ${next}

Get TV Mute Status Via DebugShell
    ${debugshell_connection}    debugshell isconnected
    ${tv_get_mute_cmd}    Set Variable    vconftool get memory/org.tizen.tv-viewer/mute_status
    Run Keyword If    ${debugshell_connection}    debugshell enter shellmode
    ${mute_value} =    debugshell sendcommandandwaitkeyword    ${tv_get_mute_cmd}    value =    5
    ${mute_value}    get regexp matches    ${mute_value}    value = (.*?) \\(    1
    log    ${mute_value}[0]    console=yes
    return from keyword    ${mute_value}[0]

Get BT Mute Status Via DebugShell
    ${debugshell_connection}    debugshell isconnected
    ${tv_get_mute_cmd}    Set Variable    vconftool get memory/menu/network/screenmirroring/get_volume_mute_bt
    Run Keyword If    ${debugshell_connection}    debugshell enter shellmode
    ${mute_value} =    debugshell sendcommandandwaitkeyword    ${tv_get_mute_cmd}    value =    5
    ${mute_value}    get regexp matches    ${mute_value}    value (.*?) ([0-9]+)    2

    IF    ${mute_value} == 1
        ${mute_vale_ret}    Set Variable    True
    ELSE
        ${mute_vale_ret}    Set Variable    False
    END

    log    ${mute_vale_ret}    console=yes
    return from keyword    ${mute_vale_ret}    

Get TV Mute Status Via Sdb
    ${tv_get_mute_cmd}    Set Variable    vconftool get memory/org.tizen.tv-viewer/mute_status
    ${mute_value} =    sdb sendshellcmd    ${tv_get_mute_cmd}
    ${mute_value}    get regexp matches    ${mute_value}    value = (.*?) \\(    1
    log    ${mute_value}[0]    console=yes
    return from keyword    ${mute_value}[0]

Get BT Mute Status Via Sdb
    ${tv_get_mute_cmd}    Set Variable    vconftool get memory/menu/network/screenmirroring/get_volume_mute_bt
    ${mute_value} =    sdb sendshellcmd    ${tv_get_mute_cmd}
    ${mute_value}    get regexp matches    ${mute_value}    value (.*?) ([0-9]+)    2

    IF    ${mute_value} == 1
        ${mute_vale_ret}    Set Variable    True
    ELSE
        ${mute_vale_ret}    Set Variable    False
    END

    log    ${mute_vale_ret}    console=yes
    return from keyword    ${mute_vale_ret}    

# Set Memo Variable
    # [Documentation]     Set non-volatile variable\n
    # ...    |  Set Memo Variable  |  Memoname  |  0  |
    # ...    |  Set Memo Variable  |  Memoname  |  ${countval+1}  |
    # [Arguments]    ${memo_name}    ${memo_value}
    
    # ${memo_value} =    Convert To String    ${memo_value}
    # Create File    ${memo_name}.mem    ${memo_value}
    
# Get Memo Value As Integer
    # [Documentation]     Get non-volatile variable as integer\n
    # ...    | ${countval} =  |  Get Memo Value As Integer  |  CountMemo  |
    # [Arguments]    ${memo_name}
    
    # ${memo_value} =    Get File    ${memo_name}.mem
    # ${memo_value} =    Convert To Integer    ${memo_value}
    # RETURN    ${memo_value}

   
# Get Memo Value
    # [Documentation]     Get non-volatile variable\n
    # ...    : memo_name : Memo file name that contains value.\n
    # ...    : convertkeyword : Convert keyword to get prefer variable type. \n
    # ...    
    # ...    | ${strval} =  |  Get Memo Value  |  StringMemo  |    |
    # ...    | ${intval} =  |  Get Memo Value  |  IntMemo  |    Convert To Integer  |
    # ...    | ${binaryval} =  |  Get Memo Value  |  BinaryMemo  |    Convert To Binary  |
    # ...    | ${booleanval} =  |  Get Memo Value  |  BooleanMemo  |    Convert To Boolean  |
    # ...    | ${floatval} =  |  Get Memo Value  |  FloatMemo  |    Convert To Number  |    
    # ...    | ${octalval} =  |  Get Memo Value  |  OctalMemo  |    Convert To Octal  |
    # [Arguments]    ${memo_name}    ${convertkeyword}=Convert To String
    
    # ${memo_value} =    Get File    ${memo_name}.mem
    # ${memo_value} =    Run Keyword    ${convertkeyword}    ${memo_value}
    # RETURN    ${memo_value}
    
SDB Reconnect When SDB Connect Fail
    [Documentation]    
    ...    This keyword attempts to reconnect up to 2 times if 'sdb connect' fails and requires 'DebugShell' or 'ATHub' to be pre-connected for reconnection.
    ...    Be sure to call 'DebugShell Connect' or 'ATHub Connect' before calling this keyword
    ${athub_device}    get variable value    ${ATHub01}    ${None}
    ${debugshell_device}    get variable value    ${DebugShell01}    ${None}
    ${ip2ir_device}    get variable value    ${IP2IR01}    ${None}
    ${apc_device}    get variable value    ${APC01}    ${None}

    ${status}    ${value} =    Run Keyword And Ignore Error    wait until keyword succeeds     2 times     5s     Check SDB Connection Status
    IF    '${status}'=='FAIL'
        Log    sdb connect is failed total 2 times, try to reboot master power     Error
        IF    ${athub_device} is not ${None}
            Sleep   120s
            ATHub Master Power Reboot for SDB
            Check SDB Connection Status
        ELSE IF    ${ip2ir_device} is not ${None} and ${apc_device} is not ${None}
            Sleep   120s
            APC and IP2IR Master Power Reboot for SDB
            Check SDB Connection Status    
        END
    END

Check SDB Connection Status
    ${passed} =     Run Keyword And Return Status    Sdb Connect
    IF    '${passed}'=='False'
        Log    sdb connect is fail, try to Master Power reboot TV     Error

        ${athub_device}    get variable value    ${ATHub01}    ${None}
        ${debugshell_device}    get variable value    ${DebugShell01}    ${None}
        ${ip2ir_device}    get variable value    ${IP2IR01}    ${None}
        ${apc_device}    get variable value    ${APC01}    ${None}        
        IF    ${athub_device} is not ${None}
            Athub Connect
            New Soft Power Reboot for SDB
            Sdb Disconnect
            Sdb Connect      
        ELSE IF    ${ip2ir_device} is not ${None}  
            New Soft Power Reboot for IP2IR
            Sdb Disconnect
            Sdb Connect                 
        ELSE IF    ${debugshell_device} is not ${None}
            DebugShell Master Power Reboot for SDB
            Sdb Disconnect
            Sdb Connect
        ELSE
            Log    There is no device to reboot.
        END        
    END
    Sleep    5s

APC and IP2IR Check SDB Connection Statuss
    ${passed} =     Run Keyword And Return Status    Sdb Connect
    IF    '${passed}'=='False'
        Log    sdb connect is fail, try to Master Power reboot TV     Error

        ${athub_device}    get variable value    ${ATHub01}    ${None}
        ${debugshell_device}    get variable value    ${DebugShell01}    ${None}
        IF    ${athub_device} is not ${None}
            Athub Connect
            New Soft Power Reboot for SDB
            Sdb Disconnect
            Sdb Connect        
        ELSE IF    ${debugshell_device} is not ${None}
            DebugShell Master Power Reboot for SDB
            Sdb Disconnect
            Sdb Connect
        ELSE
            Log    There is no device to reboot.
        END        
    END
    Sleep    5s
 
ATHub Master Power Reboot for SDB
    Log To Console    [ ATHub Master Power Reboot for SDB ]   
    sleep      10s
    athub setmasterpower    off
    sleep      10s
    athub setmasterpower    on
    sleep      10s
    athub sendIR    DISCRET_POWER_ON    repeat=5    delay=3
    sleep      180s   

DebugShell Master Power Reboot for SDB
    Log To Console    [ DebugShell Master Power Reboot for SDB ]   
    sleep      10s
    Debugshell Connect
    Enter Debugshell TTY PRINTK
    Debugshell Enter Shellmode
    Debugshell Sendcommand    export PATH=$PATH:/prd/usr/bin;micom-tool reboot
    sleep      180s   

APC and IP2IR Master Power Reboot for SDB
    Log To Console    [ APC and IP2IR Master Power Reboot for SDB ]   
    sleep      10s
    Apc Setmasterpower    OFF    ${APC01}[switch_id]
    sleep      10s
    Apc Setmasterpower    ON    ${APC01}[switch_id]
    sleep      10s
    IP2IR SendIR    DISCRET_POWER_ON    repeat=5    delay=3
    sleep      180s   

Enter Debugshell TTY PRINTK
    ${expected_log}    set variable    Disable ALL PRINT
    FOR    ${index}    IN RANGE    5
        ${expected_logs}    create list    ${expected_log}
        debugshell register keyword monitor    ${expected_logs}
        debugshell tty mode
        ${log}    debugshell get keyword monitor result    1
        Run Keyword If    """${expected_log}""" in """${log}"""    Exit For Loop
        debugshell tty mode    repeat=1
    END    

New Soft Power Reboot for SDB
    Log To Console    <New Soft Power Reboot for SDB : Soft Power Reboot>
    Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR    DISCRET_POWER_OFF    repeat=3
 
    Sleep    120s
 
    # TV Power On
    Log    DISCRET_POWER_ON    console=yes
    athub sendIR    DISCRET_POWER_ON    repeat=5    delay=3
 
    Log    Sleep 120    console=yes
    Sleep    120s
    Log to console    </Soft Power Reboot>

New Soft Power Reboot for IP2IR
    Log To Console    <New Soft Power Reboot for IP2IR : Soft Power Reboot>
    Log    DISCRET_POWER_OFF    console=yes
    IP2IR SendIR    DISCRET_POWER_OFF    repeat=3
 
    Sleep    120s
 
    # TV Power On
    Log    DISCRET_POWER_ON    console=yes
    IP2IR SendIR    DISCRET_POWER_ON    repeat=5    delay=3
 
    Log    Sleep 120    console=yes
    Sleep    120s
    Log to console    </Soft Power Reboot>
