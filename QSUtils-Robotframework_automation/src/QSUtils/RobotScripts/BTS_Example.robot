*** Settings ***
Metadata        Version        2022.10.06

Documentation    BTS CheatSheet, script snippets

# Standard libraries of Robot Framework
Library    BuiltIn
Library    Collections
Library    DateTime
# Library    Dialogs
Library    OperatingSystem
Library    Process
# Library    Screenshot
# Library    String
# Library    Telnet
# Library    XML
# Reference variable lists managed by ReferenceEditor
# If you want to test with the ReferenceEditor then you should remove comment
# Variables    BTS_ReferenceList_IMG.py
# Variables    BTS_ReferenceList_OCR.py

# Device settings managed by SetupManager
Variables    ${EXECDIR}${/}BTS_Variable.py    BTS_Device_Settings.ini
Variables    ${EXECDIR}${/}BTS_Device_Settings.py     # Created by "Variables    BTS_Variable.py    BTS_Device_Settings.ini"

# BTS libraries
Library    BTS.BTS_ATHub   ${ATHub01}
Library    BTS.BTS_DebugShell   ${DebugShell01}
Library    BTS.BTS_Image
Library    BTS.BTS_OCR
Library    BTS.BTS_PatternGenerator   ${PatternGenerator01}
Library    BTS.BTS_Sdb   ${SDB01}
Library    BTS.BTS_Sound   ${Sound01}   WITH NAME   TVSPEAKER
Library    BTS.BTS_Sound   ${Sound02}   WITH NAME   SOUNDBAR
Library    BTS.BTS_Video
Library    BTS.BTS_WebCam   ${WebCam01}
Library    BTS.BTS_KeySender   ${ATHub01}   ${DebugShell01}
Library    BTS.BTS_Common

# BTS common userkeyword
Resource    ${EXECDIR}${/}CommonKeyword.robot

# Setup and Teardown
Suite Setup     Log    [[Executed before any test cases or sub test suites in that test suite.]]    console=yes
Suite Teardown    Log    [[Executed after any test cases or sub test suites in that test suite.]]    console=yes

Test Setup      Log    [A test setup is something that is executed before a test case.]    console=yes
Test Teardown   Log    [A test teardown is executed after a test case.]    console=yes


*** Variables ***
${STRING}=        cat
${NUMBER}=        ${1}
@{LIST}=          one    two    three
&{DICTIONARY}=    string=${STRING}    number=${NUMBER}    list=@{LIST}
${ENVIRONMENT_VARIABLE}=    %{PATH}


*** Test Cases ***    # BTS script snippets
Example_AccessBTSVariables
    [Documentation]    Sample TC to use usercommands to access BTS variables.
    [Tags]    Example
    Log    Access Device Settings. At-hub, Serial, Sdb have to be connected    console=yes
    Access Device Settings

    Log    Access Reference Information. you have to have OCR reference which name(ID) is OCR_SDB01_image    console=yes
    Access Reference Information    ${OCR_SDB01_image}

Example_BTS_KeySender
    [Tags]    Example
    [Teardown]    Keysender Disconnect
    Keysender Set Delay     5s      #After key send, wait 5S
    Keysender Connect
    Keysender Sendkey    KEY_MENU
    Keysender Sendkey    KEY_DOWN    

Example_BTS_ATHub
    [Tags]    Example
    [Setup]    Athub Connect
    [Teardown]    Athub Disconnect
    Athub SendIR    KEY_EXIT
    Athub SendIR    KEY_MENU    delay=5
    Athub SendIR    KEY_DOWN    repeat=4
    Athub SendIR    KEY_UP      repeat=3    delay=1
    Athub SendIR    KEY_UP      3           1
    Athub Setmasterpower    OFF
    Athub Setmasterpower    ON
    Athub SelectUSB    PC
    Athub SelectUSB    TV

Example_BTS_DebugShell
    [Tags]    Example
    [Setup]    Debugshell Connect
    [Teardown]    Debugshell Disconnect
    Debugshell Sendcommand      20102011
    Debugshell Sendcommand      stop
    Debugshell Sendcommand      exit
    Debugshell Sendcommand      exit
    Debugshell Sendcommand      99
    Debugshell Sendcommand      20089999
    Debugshell Sendcommand      98
    ${ret}=    Debugshell Waitkeyword      run Shell mode      3
    Log   Return is ${ret}    console=yes

Example_BTS_Image
    [Tags]    Example
    [Setup]    Sdb Connect
    [Teardown]  Sdb Disconnect
    
    ${captured_image}=    SDB GET CURRENT SCREEN  dump_screen_source.png
    # You have to prepare image reference which name(ID) is IMG_SDB01_image
    ${res}=    Image Compare  ${IMG_SDB01_image}    ${captured_image}
    Should Be True  ${res}

Example_BTS_OCR
    [Tags]    Example
    [Setup]    Sdb Connect
    [Teardown]  Sdb Disconnect

    Ocr Set Language    English
    ${captured_image}=    SDB GET CURRENT SCREEN  dump_screen_source.png
    # You have to prepare OCR reference which name(ID) is OCR_SDB01_image
    # ${read_text}=    Ocr Read Text From Imagefile By Region   dump_screen_source.png  ${OCR_SDB01_image}[region]
    ${read_text}=    Get Text By OCR    ${OCR_SDB01_image}    ${captured_image}
    Log    ${read_text}
    Should Match    ${read_text}    ${OCR_SDB01_image}[text]

Example_BTS_Sdb
    [Tags]    Example
    [Setup]    Sdb Connect
    [Teardown]  Sdb Disconnect

    # Enable hyperuart and save it's log to ${OUTPUT DIR}/sdb_log.txt.
    # Log file will be divided by 10000 lines
    Remove File    ${OUTPUT DIR}/sdb_log.txt
    Sdb Enable Hyperuart    ${OUTPUT DIR}/sdb_log.txt    10000

    # Dump current OSD screen and save in ${OUTPUT DIR}.
    Remove File    ${OUTPUT DIR}/dump_screen.png
    ${capturefile}=    Sdb Get Current Screen     ${OUTPUT DIR}
    Log    ${capturefile}        console=yes
    File Should Exist     ${capturefile}

    Sdb Disable Hyperuart

Example_BTS_Sdb_capture_TV_screen
    [Tags]    Example
    [Setup]    Sdb Connect
    [Teardown]  Sdb Disconnect

    # Capture screen by BTS_SDB keyword
    ${capturefile}=   Sdb Get Current Screen    caputured_screen.png
    Log    ${capturefile}    console=yes
    File Should Exist    ${capturefile}

    # Capture screen by Common keyword (CommonKeyword.robot)
    ${defaultpath}=    Sdb Get Current Screen
    Log    ${defaultpath}    console=yes
    File Should Exist    ${defaultpath}

Example_BTS_Sound
    [Tags]    Example

    ${file}=   TVSPEAKER.Sound Record  10    ${OUTPUT DIR}/sound_muteon.wav
    ${ret}=    TVSPEAKER.Sound Has Mute   recorded_file_path=${OUTPUT DIR}/sound_muteon.wav    # It should be mute

    Should Be True  ${ret}

Example_BTS_Video
    [Tags]    Example
    [Documentation]    Check the Video recorded files were muted

    Webcam Videorecordstart   webcam_record.avi    # It will be created Project folder${/}report${/}2020xxxx${/}video
    Sleep    2m
    ${video_path} =    Webcam Videorecordstop
    Log To Console    Recorded Path : ${video_path}

    ${video_isMute}     Video Ismute    ${video_path}
    ${video_hasMute}    Video Hasmute    ${video_path}    criteriaforfinding=1s
    Log    ${video_hasMute}        console=yes

    Should Not Be True     ${video_isMute}
    Should Not Be True     ${video_hasMute}

Example_BTS_WebCam
    [Tags]    Example

    Webcam Showwebcam    str=ON

    # snapshot : snapshot fils is saved in Project folder${/}report${/}2020xxxx${/}image
    ${captured}=    Webcam Captureimage     channel.jpg
    Log To Console    ${captured}

    # Wait image : Wait 10 seconds until the same screen as the reference file(${IMG_WebCam01_image}) appears webcam.
    # Prepare image reference which name(ID) is IMG_WebCam01_image
    # WebCam WaitImage    ${IMG_WebCam01_image}    10

    # Full screen mode is enable/disable
    Webcam Fullscreen    on
    Sleep    2s
    Webcam Fullscreen    off

    # Recording with test.avi file
    Webcam Videorecordstart    test.avi
    Sleep    1s    

    Webcam Videorecordpause
    Sleep    1s

    Webcam Videorecordresume
    Sleep    1s

    ${recorded}=   Webcam Videorecordstop
    Log To Console    ${recorded}

Example_BTS_PatternGenerator
    [Tags]    Example
    [Setup]    Patterngenerator Connect
    [Teardown]  Patterngenerator Disconnect
    # You need "Cross Serial cable" and check Pattern Generator Baud rate 115200
    Sleep    10
    Log To Console    pattern1
    Patterngenerator Set Pattern    25
    Patterngenerator Set Resolution    435

    Log To Console    pattern2
    Patterngenerator Set Pattern    35
    Patterngenerator Set Resolution    356

Example_BTS_HighlightFailMessageOnRunner
    [Documentation]  During test, various Fails would be occurred.
    ...  Script developer can highlight important fail message at Runner's 'TestInProgressing' > Message by using 'Run Keyword And Highlight Fail Message' keyword.
    ...  (Ex: Distinguish between judgement fail and environment fail(connection fail, navigation fail, etc...)
    ...  http://wiki.vd.sec.samsung.net/display/BTS/Leave+a+message+on+the+TestInProgressing
    Run Keyword And Highlight Fail Message    Should Be Same    11    99    message=HighlightFailMessage

Example_BTS_RunnerVariables
    [Documentation]    
    ...    http://wiki.vd.sec.samsung.net/pages/viewpage.action?pageId=116481361
    ...    When BTS runner execute robot test, appends some variables related to TC repeat information.
    ...    BTS test automation script developer can use this in script.
    # ${RunnerTCRepeatType} : Repeat type of the TC (Time Increase | Time Decrease | Time Randomize)
    # ${RunnerTCRepeatValue} : Configured repeat value of the TC
    # ${RunnerTCRepeatIndex} : Current repeat index of the TC
    # 
    # ${RunnerTCListRepeatIndex} : Current repeat index of the TestCaseList

    Log To Console    ${RunnerTCListRepeatIndex} : ${RunnerTCRepeatValue} : ${RunnerTCRepeatIndex}



# #########################################################
# Robot Framework script snippets
# #########################################################
Call keywords with a varying number of arguments
    A Keyword Without Arguments
    A Keyword With A Required Argument    Argument
    A Keyword With A Required Argument    argument=Argument
    A Keyword With An Optional Argument
    A Keyword With An Optional Argument    Argument
    A Keyword With An Optional Argument    argument=Argument
    A Keyword With Any Number Of Arguments
    A Keyword With Any Number Of Arguments    arg1    arg2    arg3    arg4    arg5
    A Keyword With One Or More Arguments    arg1
    A Keyword With One Or More Arguments    arg1    arg2    arg3

# Conditional IF ELSE
#     [Documentation]    Robot Framework 3.x has 'Run Keyword If', 'ELSE IF', 'ELSE' keyword.
#     ...    (From Robot Framework 4.x, support for 'Native IF/ELSE syntax' and 'nested control structures'.)
#     ...    (https://github.com/robotframework/robotframework/blob/master/doc/releasenotes/rf-4.0.rst)
#     ${value}=    Set Variable    3
#     RUN KEYWORD IF    ${value}== 1    Log    111
#     ...    ELSE IF    ${value}== 2    Log    222
#     ...    ELSE IF    ${value}== 3
#     ...        Run keywords    Log    333    console=yes
#     ...                 AND    Log    321    console=yes
#     ...                 AND    Log    300    console=yes
#     ...    ELSE    Log    no match    console=yes
#     ${value}=    Set Variable If    ${value}== 3    5
#     Log    ${value}    console=yes

Do conditional IF - ELSE IF - ELSE execution
    [Documentation]    
    ...    Robot Framework 4 introduces native IF, ELSE IF, ELSE constructs to achieve conditional execution in your robot,
    ...    giving you new possibilities for implementing logic branching
    
    IF    ${NUMBER} > 1
        Log    Greater than one.      console=yes
    ELSE IF    "${STRING}" == "dog"
        Log    It's a dog!      console=yes
    ELSE
        Log    Probably a cat.      console=yes
    END

Call a keyword that returns a value
    ${value}=    A keyword that returns a value
    Log    ${value}    console=yes    # Return value

Loop a list
    Log    ${LIST}    # ['one', 'two', 'three']
    FOR    ${item}    IN    @{LIST}
        Log    ${item}    console=yes    # one, two, three
    END
    FOR    ${item}    IN    one    two    three
        Log    ${item}    console=yes    # one, two, three
    END

Loop a dictionary
    Log    ${DICTIONARY}
    # {'string': 'cat', 'number': 1, 'list': ['one', 'two', 'three']}
    FOR    ${key_value_tuple}    IN    &{DICTIONARY}
        Log    ${key_value_tuple}    console=yes
        # ('string', 'cat'), ('number', 1), ('list', ['one', 'two', 'three'])
    END
    FOR    ${key}    IN    @{DICTIONARY}
        Log    ${key}=${DICTIONARY}[${key}]    console=yes
        # string=cat, number=1, list=['one', 'two', 'three']
    END

Loop a range from 0 to end index
    FOR    ${index}    IN RANGE    10
        Log    ${index}    console=yes    # 0-9
    END

Loop a range from start to end index
    FOR    ${index}    IN RANGE    1    10
        Log    ${index}    console=yes    # 1-9
    END

Loop a range from start to end index with steps
    FOR    ${index}    IN RANGE    0    10    2
        Log    ${index}    console=yes    # 0, 2, 4, 6, 8
    END

Nest loops
    [Documentation]    
    ...    Robot Framework 3 did not natively support nested control structures (such as a FOR loop inside a FOR loop). 
    ...    Robot Framework 4 natively supports nested control structures, such as FOR loops and IF constructs

    @{alphabets}=    Create List    a    b    c
    Log to console     ${alphabets}    # ['a', 'b', 'c']
    @{numbers}=    Create List    ${1}    ${2}    ${3}
    Log to console     ${numbers}    # [1, 2, 3]
    FOR    ${alphabet}    IN    @{alphabets}
        FOR    ${number}    IN    @{numbers}
            Log to console     ${alphabet}${number}
            # a1, a2, a3, b1, b2, b3, c1, c2, c3
        END
    END

Exit a loop on condition
    FOR    ${i}    IN RANGE    5
        Exit For Loop If    ${i}== 2
        Log    ${i}    console=yes    # 0, 1
    END

Continue a loop from the next iteration on condition
    FOR    ${i}    IN RANGE    3
        Continue For Loop If    ${i}== 1
        Log    ${i}    console=yes    # 0, 2
    END

Create a scalar variable
    ${animal}=    Set Variable    dog
    Log    ${animal}    console=yes    # dog
    Log    ${animal}[0]    console=yes    # d
    Log    ${animal}[-1]    console=yes    # g

Create a number variable
    ${π}=    Set Variable    ${3.14}
    Log    ${π}    console=yes    # 3.14

Create a list variable
    @{animals}=    Create List    dog    cat    bear
    Log    ${animals}    console=yes    # ['dog', 'cat', 'bear']
    Log    ${animals}[0]    console=yes    # dog
    Log    ${animals}[-1]    console=yes    # bear

Create a dictionary variable
    &{dictionary}=    Create Dictionary    key1=value1    key2=value2
    Log    ${dictionary}    console=yes    # {'key1': 'value1', 'key2': 'value2'}
    Log    ${dictionary}[key1]    console=yes    # value1
    Log    ${dictionary.key2}    console=yes    # value2

Access the items in a sequence (list, string)
    ${string}=    Set Variable    Hello world!
    Log    ${string}[0]    console=yes    # H
    Log    ${string}[:5]    console=yes    # Hello
    Log    ${string}[6:]    console=yes    # world!
    Log    ${string}[-1]    console=yes    # !
    @{list}=    Create List    one    two    three    four    five
    Log    ${list}    console=yes    # ['one', 'two', 'three', 'four', 'five']
    Log    ${list}[0:6:2]    console=yes    # ['one', 'three', 'five']

Split arguments to multiple lines
    A keyword with any number of arguments
    ...    arg1
    ...    arg2
    ...    arg3

Log available variables
    Log Variables
    # ${/}= /
    # &{DICTIONARY}= { string=cat | number=1 | list=['one', 'two', 'three'] }
    # ${OUTPUT_DIR}= /Users/<username>/...
    # ...

Evaluate Python expressions
    ${path}=    Evaluate    os.environ.get("PATH")
    ${path}=    Set Variable    ${{os.environ.get("PATH")}}

    ${ret}=    Evaluate    random.randint(0, 123456)    modules=random
    Log    ${ret}    console=yes

Use special variables
    Log    ${EMPTY}    # Like the ${SPACE}, but without the space.
    Log    ${False}    # Boolean False.
    Log    ${None}    # Python None
    Log    ${null}    # Java null.
    Log    ${SPACE}    # ASCII space (\x20).
    Log    ${SPACE * 4}    # Four spaces.
    Log    "${SPACE}"    # Quoted space (" ").
    Log    ${True}    # Boolean True.

Timestamp_Format
    ${ts}    Get Current Date    result_format=%m%d_%H%M%S
    Log    ${ts}    console=yes    # 1006_114550

*** Keywords ***
A Keyword Without Arguments
    Log    No arguments.    console=yes

A Keyword With A Required Argument
    [Arguments]    ${argument}
    Log    Required argument: ${argument}    console=yes

A Keyword With An Optional Argument
    [Arguments]    ${argument}=Default value
    Log    Optional argument: ${argument}    console=yes

A Keyword With Any Number Of Arguments
    [Arguments]    @{varargs}
    Log    Any number of arguments: @{varargs}    console=yes

A Keyword With One Or More Arguments
    [Arguments]    ${argument}    @{varargs}
    Log    One or more arguments: ${argument} @{varargs}    console=yes

A Keyword That Returns A Value
    RETURN    Return value

A keyword With Documentation
    [Documentation]    This is keyword documentation.
    No Operation

Access Device Settings
    Log To Console    ""
    Log To Console    ${ATHub01}[port]
    Log To Console    ${DebugShell01}[port]
    #    Log To Console    ${PatternGenerator01}[port]
    Log To Console    ${SDB01}[ip]
    #    Log To Console    ${Sound01}[name]
    #    Log To Console    ${Sound01}[sound_dev_id]
    #    Log To Console    ${WebCam01}[name]
    #    Log To Console    ${WebCam01}[imaging_dev_id]
    #    Log To Console    ${WebCam01}[rect]

Access Reference Information
    [Arguments]    ${reference}
    Log To Console    ""
    Log To Console    ${reference}
    Log To Console    ${reference['path']}
    Log To Console    ${reference}[path]
    Log To Console    ${reference}[region]
    Log To Console    ${reference['region']}
    Log To Console    ${reference}[region][3]
    Log To Console    ${reference}[text]
    Log To Console    ${reference}[language]
