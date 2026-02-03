*** Settings ***
Metadata        Version        2022.5.16
Metadata    Author    jjkk.kim, khc11, dreamj85

Documentation    TV - Soundbar connection test automation script.

# Standard libraries of Robot Framework
Library    BuiltIn
Library    Collections
Library    DateTime
Library    Dialogs
Library    OperatingSystem
Library    Process
#Library    Screenshot
#Library    String
#Library    Telnet
#Library    XML

# Reference variable lists managed by ReferenceEditor
# If you want to test with the ReferenceEditor then you should remove comment
Variables    BTS_ReferenceList_IMG.py
#Variables    BTS_ReferenceList_OCR.py

# Device settings managed by SetupManager
Variables    BTS_Variable.py    BTS_Device_Settings.ini
Variables    BTS_Device_Settings.py     # Created by "Variables    BTS_Variable.py    BTS_Device_Settings.ini"

# BTS libraries
Library    BTS.BTS_ATHub   ${ATHub01}
Library    BTS.BTS_DebugShell   ${DebugShell01}
# Library    BTS.BTS_Image
# Library    BTS.BTS_OCR
# Library    BTS.BTS_PatternGenerator   ${PatternGenerator01}
Library    BTS.BTS_Sdb   ${SDB01}    WITH NAME    SDB_TV
# Library    BTS.BTS_Sdb   ${SDB01}    WITH NAME    SDB_SOUNDBAR
# Library    BTS.BTS_Sdb   ${SDB02}    WITH NAME    SDB_TV

Library    BTS.BTS_Sound   ${Sound01}   #WITH NAME   SoundSensor
Library    BTS.BTS_Video
Library    BTS.BTS_WebCam   ${WebCam01}
# Library    BTS.BTS_HIDKeyboard   ${HIDKeyboard01}
# Library    BTS.BTS_KeySender   ${ATHub01}   ${DebugShell01}
Library    BTS.BTS_KeySender   ${ATHub01}   ${SDB01}         #ATHUB 사용시
# Library    BTS.BTS_KeySender   ${AxiDraw01}   ${SDB01}      #AxiDraw 사용시 
Library    BTS.BTS_Navigation  ${SDB01}    ${SDB01}   ${SDB01}
Library    BTS.BTS_RedRat
Library    BTS.BTS_Common
# Library    BTS.BTS_AxiDraw
# Library    BTS.BTS_AxiDraw      ${AxiDraw01}
Library    AppiumLibrary


## BTS common userkeyword
Resource    CommonKeyword.robot

# Setup and Teardown
Suite Setup     SuiteSetupKW
Suite Teardown    SuiteTeardownKW

# Test Setup      TestSetupKW
# Test Teardown   TestTeardownKW


*** Variables ***
# @{NAME_LIST} =       Matti       Teppo
# &{USER_DICTIONARY} =      name=Megan    address=fromis         phone=999

# Should be measured before test. (DeviceController.CheckDBThreshold)
${DB_Threshold} =  -77.053321564799646
# ${SoundBarName} =      TV + Souunbar Q990B(Optical)
${SoundOutput} =   TV + Soundbar Q930B(HDMI-eARC)
# Soundbar Q-Series(HDMI-eARC)

# Max number of soundoutput in list
${SoundOutputLimit} =    9

${LOG_DIR} =    logdir
${SoundOutputMemoFile} =    BTS_TestSoundOutput.som

@{NAVIGATION}=    KEY_CHUP    KEY_CHDOWN
@{KEY_DELAY}=   1    5    10    30    60
@{REPEAT_COUNT}=    3    5    7    9
@{RANDOM_SLEEP}=    1s    5s    10s

*** Test Cases ***
test capture
    TV Should Not Mute
TestTest
    Log To Console    <${SoundOutput}>
    ${status}    ${value} =    Run Keyword And Ignore Error    Navigation Efl Focused Texts Should Contain    ${SoundOutput}

CreatMenuTree
    [Documentation]    EFL Menu Tree 생성  (기본 3step)
    Navigation Create Menutree


BT Remote Test(SoftPower)
    Axidraw Connect
    Debugshell Connect
   
    Log    [BT Remote MBR Test]    console=yes
        ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S

    Log    [Video Record Start]    console=yes    
        Webcam Videorecordstart     VIDEO_${timestring}.mp4    show_timestamp=ON 

    Log    Sleep 10s    console=yes
        Sleep    10s

    Log    [MBR Ch Change]    console=yes
        # Debugshell Waitkeyword       suspend        10m
        keysender sendkey    KEY_CHUP             delay=3        
        keysender sendkey    KEY_CHDOWN           delay=3    
    
    Log    Sleep 10s    console=yes
        Sleep    10s

    Log    POWER_OFF    console=yes
        keysender sendkey    KEY_POWER        delay=2     

    # Power off 확인
    ${wait_keywords}    create list    suspend of devices complete after
    Log    POWER_off complete    console=yes
        Debugshell Register Keyword Monitor    ${wait_keywords}
        Debugshell Get Keyword Monitor Result    240
    
    Log    Sleep 5s ~ 300s    console=yes
        Sleep Timing    5s    150s   300s       
    
    # Log 문자를 확인하여 Power on 여부 Check
    ${wait_keywords}    create list    boot_reason(68)
    # Power on Check 부분의 키워드는 상황에 따라서 다르게 사용 resume of devices complete after
    # IOT 설정 상태에서는 서버 연결 동작으로 boot_reason(68) 사용

    FOR      ${i}     IN RANGE      10
        Log    POWER_ON ${i}회    console=yes
        Debugshell Register Keyword Monitor    ${wait_keywords}
        Sleep    1s
            keysender sendkey    KEY_POWER       safekey=False    #longpress_time=1s
        ${ret} =    Debugshell Get Keyword Monitor Result    10
        Exit for loop if    """${ret}"""!="${Empty}"
    END
        
    Log    Sleep 30s    console=yes   
    Sleep    30s

    # Power on 상태 check 및 화면 check
    IF    """${ret}"""=="${Empty}"
        ${wait_keywords}    create list    E/
        Debugshell Register Keyword Monitor    ${wait_keywords}
        ${ret1} =    Debugshell Get Keyword Monitor Result    10
        IF    """${ret1}"""=="${Empty}"
            Athub SendIR    DISCRET_POWER_ON    repeat=5    delay=1      
            Log    Discret_Sleep 30s    console=yes
            Sleep      30s
        ELSE
            FOR    ${i}    IN RANGE    5
                ${isStatic}         VideoCheck_IsStatic
                IF  '${isStatic}'=='True'    
                    Athub SendIR    DISCRET_POWER_ON    repeat=5    delay=1
                END
                Log    Video_Sleep 20s    console=yes    
                Sleep      20s
                Log    Power on ${i}회   console=yes
                Exit for loop if    '${isStatic}'!='True'          
            END
            Log    [Video Record Start]    console=yes    
            Webcam Videorecordstart     VIDEO_${timestring}_1.mp4   show_timestamp=ON
            Sleep    10s
        END
    END

    Log    Sleep 90s    console=yes   
    Sleep    90s

    Log    [MBR Ch Change]    console=yes
        ${status}    ${value}   Run Keyword And Ignore Error    keysender sendkey    KEY_CHUP         repeat=10         delay=3   
        run keyword if  '${status}'=='FAIL'    
        ...                     Run Keywords      pause execution   error occur
        ...                     FAIL    No response   

        ${status}    ${value}   Run Keyword And Ignore Error    keysender sendkey    KEY_CHDOWN         repeat=10         delay=3   
        run keyword if  '${status}'=='FAIL'    
        ...                     Run Keywords      pause execution   error occur
        ...                     FAIL    No response   

          
     ${videofile} =    Webcam Videorecordstop

    Athub SendIR    KEY_2    delay=2
    Athub SendIR    KEY_4    delay=2
    Athub SendIR    KEY_OK    delay=2


    Debugshell Disconnect
    Axidraw Disconnect


BT Remote Test_Random(SoftPower)
    Axidraw Connect
    Debugshell Connect
   
    Log    [BT Remote MBR Test]    console=yes
        ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S

    Log    [Video Record Start]    console=yes    
        Webcam Videorecordstart     VIDEO_${timestring}.mp4    show_timestamp=ON 

    Log    Sleep 10s    console=yes
        Sleep    10s

    Log    [MBR Ch Change]    console=yes
        # Debugshell Waitkeyword       suspend        10m
        keysender sendkey    KEY_CHUP             delay=3        
        keysender sendkey    KEY_CHDOWN           delay=3    
    
    Log    Sleep 10s    console=yes
        Sleep    10s

    Log    POWER_OFF    console=yes
        keysender sendkey    KEY_POWER        delay=2     

    # Power off 확인
    ${wait_keywords}    create list    suspend of devices complete after
    Log    POWER_off complete    console=yes
        Debugshell Register Keyword Monitor    ${wait_keywords}
        Debugshell Get Keyword Monitor Result    240
    
    Log    Sleep 5s ~ 300s    console=yes
        Sleep Timing    5s    150s   300s       
    
    # Log 문자를 확인하여 Power on 여부 Check
    ${wait_keywords}    create list    boot_reason(68)
    # Power on Check 부분의 키워드는 상황에 따라서 다르게 사용 resume of devices complete after
    # IOT 설정 상태에서는 서버 연결 동작으로 boot_reason(68) 사용

    FOR      ${i}     IN RANGE      10
        Log    POWER_ON ${i}회    console=yes
        Debugshell Register Keyword Monitor    ${wait_keywords}
        Sleep    1s
            keysender sendkey    KEY_POWER       safekey=False    #longpress_time=1s
        ${ret} =    Debugshell Get Keyword Monitor Result    10
        Exit for loop if    """${ret}"""!="${Empty}"
    END
        
    Log    Sleep 30s    console=yes   
    Sleep    30s

    # Power on 상태 check 및 화면 check
    IF    """${ret}"""=="${Empty}"
        ${wait_keywords}    create list    E/
        Debugshell Register Keyword Monitor    ${wait_keywords}
        ${ret1} =    Debugshell Get Keyword Monitor Result    10
        IF    """${ret1}"""=="${Empty}"
            Athub SendIR    DISCRET_POWER_ON    repeat=5    delay=1      
            Log    Discret_Sleep 30s    console=yes
            Sleep      30s
        ELSE
            FOR    ${i}    IN RANGE    5
                ${isStatic}         VideoCheck_IsStatic
                IF  '${isStatic}'=='True'    
                    Athub SendIR    DISCRET_POWER_ON    repeat=5    delay=1
                END
                Log    Video_Sleep 20s    console=yes    
                Sleep      20s
                Log    Power on ${i}회   console=yes
                Exit for loop if    '${isStatic}'!='True'          
            END
            Log    [Video Record Start]    console=yes    
            Webcam Videorecordstart     VIDEO_${timestring}_1.avi    show_timestamp=ON
            Sleep    10s
        END
    END

    Log    Sleep 90s    console=yes   
    Sleep    90s

    # Channel, Repeat, Delay Random 테스트
    Random_ALL

    # Repeat, Delay Random 테스트
    Random_Repeat_Delay
          
    ${videofile} =    Webcam Videorecordstop

    Athub SendIR    KEY_2    delay=2
    Athub SendIR    KEY_4    delay=2
    Athub SendIR    KEY_OK    delay=2


    Debugshell Disconnect
    Axidraw Disconnect


captureimage
    SDB_TV.Sdb Connect
    sdb get capture screen using capturetool

    # 1. 화면 캡처 선 진행 후 Home Test 실행
    # 2. Checklist 수행 전 IMG Referance 설정
    # 3. BT 리모컨을 TV IR 수신부로 지향
    
BT Remote_Home Test(SoftPower) 
    
    # Athub Connect
    # Retry sdb connect
    Axidraw Connect
    # Navigation Connect
    # Keysender Connect
    Debugshell Connect
    
    Log    [BT Remote Home Test]    console=yes
        ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S

    Log    [Video Record Start]    console=yes    
        Webcam Videorecordstart     VIDEO_${timestring}.mp4    show_timestamp=ON 

    Log    Sleep 5s    console=yes
        Sleep    5s

    Log    [Home]    console=yes
        # Debugshell Waitkeyword       suspend        10m
        keysender sendkey    KEY_CONTENTS    delay=3   
    
    Log    Sleep 5s    console=yes
        Sleep    5s

    Log    POWER_OFF    console=yes
        keysender sendkey    KEY_POWER        delay=2     

    # Power off 확인
    ${wait_keywords}    create list    suspend of devices complete after
    Log    POWER_off    console=yes
        Debugshell Register Keyword Monitor    ${wait_keywords}
        Debugshell Get Keyword Monitor Result    240
    Log    POWER_off complete    console=yes

    Log    Sleep 5s ~ 180s    console=yes
        Sleep Timing    5s    100s   180s       
    
    # Sleep    5s
    # Log 문자를 확인하여 Power on 여부 Check
    ${wait_keywords}    create list    boot_reason(68)    
        # 상황에 따라서 사용하는 기준 변경: resume of devices complete after(IOT 설정 상태에서는 사용하지 말고 boot_reason(68) 사용)
        # IOT로 인해 Power on 오류 발생

    FOR      ${i}     IN RANGE      10
        Log    POWER_ON ${i}회    console=yes
        Debugshell Register Keyword Monitor    ${wait_keywords}
            keysender sendkey    KEY_POWER       safekey=False    # longpress_time=1s
        ${ret} =    Debugshell Get Keyword Monitor Result    10
        Exit for loop if    """${ret}"""!="${Empty}"
    END
    Log    POWER_on complete    console=yes

    # Log    Sleep 30s    console=yes   
    #     Sleep    30s
    
    # Power on 상태 Check
    IF    """${ret}"""=="${Empty}"
        Log    Sleep 30s    console=yes   
        Sleep    30s
        ${wait_keywords}    create list    E/ 
        Debugshell Register Keyword Monitor    ${wait_keywords}
        ${ret1} =    Debugshell Get Keyword Monitor Result    10
        IF    """${ret1}"""=="${Empty}"
            Athub SendIR    DISCRET_POWER_ON    repeat=5    delay=1s  
            Log    Discret_Sleep 30s    console=yes
            sleep      30s
            # 구멍을 찾아서 한번 더 수정 필요(강제 Power on 안되는 케이스 존재)
        ELSE
            FOR    ${i}    IN RANGE    5
                ${isStatic}         VideoCheck_IsStatic
                IF  '${isStatic}'=='True'    
                    Athub SendIR    DISCRET_POWER_ON    repeat=5    delay=1
                END
                Log    Sleep 20s    console=yes    
                sleep      20s
                Log    Power on ${i}회   console=yes
                Exit for loop if    '${isStatic}'!='True'          
            END
            Log    [Video Record Start]    console=yes    
            Webcam Videorecordstart     VIDEO_${timestring}_1.mp4    show_timestamp=ON
            Sleep    10s
        END
    END

     Log    Sleep 8s    console=yes   
        Sleep    8s

    # Log    [Home]    console=yes
    #     ${status}    ${value}   Run Keyword And Ignore Error    keysender sendkey    KEY_CONTENTS    delay=1
    #             IF    '${status}'=='FAIL'    
    #             pause execution   error occur
    #             FAIL    No response   
    #     END
    #     Sleep    3s

    Log    [Home Move_up]    console=yes
        keysender sendkey    KEY_UP    delay=1    safekey=False   
        Log    1 Move_UP_Complete    console=yes
    
    # Log    [Home Move_up]    console=yes
    #     keysender sendkey    KEY_UP    delay=0.2    safekey=False   
    #     Log    2 Move_UP_Complete    console=yes

    # sdb connect

    Log    [Home Move_Right]    console=yes
        keysender sendkey    KEY_RIGHT    repeat=5    delay=0.15    safekey=False  
        Log    Move_Right_Complete    console=yes
    
    webcam captureimage    
    Sleep    1.5s
    
    ${date} =   Get Current Date    result_format=%Y%m%d_%H%M
    webcam captureimage    
    #  webcam captureimage    ${OUTPUTDIR}/../webcam_${date}.png
    Image SetConfig         ratiorestriction=False   criteria=80
    # ${CapturedImage}    sdb get capture screen using capturetool        ${OUTPUTDIR}/../sdb_${date}.png
    # ${CapturedImage}    Sdb Get Current Screen        ${OUTPUTDIR}/../sdb_${date}.png
    ${CapturedImage}    Sdb Get Current Screen        
    ${result1}   Image Compare      ${Youtube_Image}       ${CapturedImage}
    ${result2}   Image Compare      ${Tving}         ${CapturedImage}
    ${result3}   Image Compare      ${Youtube2}       ${CapturedImage}
    ${result4}   Image Compare      ${Tving2}         ${CapturedImage}
    IF  '${result1}'=='True' or '${result2}'=='True' or '${result3}'=='True' or '${result4}'=='True'
                         set test variable      ${result}     PASS
    ELSE
        set test variable      ${result}     FAIL
    END
    log to console    ${result1} and ${result2} and ${result3} and ${result4}: ${result}
    IF  '${result}'=='FAIL'
        FAIL        Focus check failed
    END
    
    Sleep    2s

    Log    [Voice key]    console=yes
        ${status}    ${value}   Run Keyword And Ignore Error    keysender sendkey    KEY_BT_VOICE 
        IF    '${status}'=='FAIL'    
    #            pause execution   error occur
                FAIL    No response   
        END
        Log    BT_Voice_Complete    console=yes
          
     ${videofile} =    Webcam Videorecordstop


    Debugshell Disconnect
    Axidraw Disconnect
    # sdb disconnect
    # Navigation disConnect
    # Keysender disConnect
    # Athub Disconnect

GotoSoundOutput_Check
    
    Navigation Gotomenu       Sound > Sound Output
    ${status}    ${value} =    Run Keyword And Ignore Error    Navigation Efl Focused Texts Should Contain    ${SoundOutput}
    
    Log    Status Result: ${Status}    console=yes
    Log    Value Data: ${value}    console=yes



C_inputSpec+Procedure_Vol_LongPress_UP/Down_1.0ver
    [Documentation]    
    ...  STB 채널 변경 시나리오
    ...  MBR 사전 설정 완료된 상태
    # [Setup]    TestSetupKW
    # # When failed, set precondition for next TC execution.
    # [Teardown]    TestTeardownKW
    
    Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    AxiDraw Connect
    
    Log   Get Current Sound Output Info    console=yes
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    Log    [${SoundOutput}]    console=yes
    Select Sound Output    ${SoundOutput}
    
    sleep    3s     
    
    
    ${timestring} =    GetTimeString
    Webcam Videorecordstart    ${LOG_DIR}${/}Vol_U/D_Video${timestring}.mp4    show_timestamp=ON
    Sound Record Start    ${LOG_DIR}${/}Vol_U/D_Sound_${timestring}.wav
    
    sleep   3s
    
    # AxiDraw 사용 시 Vol_longpress_UPDown 항목도 수정
    Repeat Keyword       10 times     Vol_longpress_UPDown 
       
    AxiDraw sendkey    KEY_VOLUP    delay=2    longpress_time=3
    # keysender sendkey    KEY_VOLUP    delay=2    longpress_time=3
    

    Check Current Sound Output     ${SoundOutput}
    
    ${videofile} =    Webcam Videorecordstop
    ${soundfile} =    Sound Record Stop

    ${status}    ${mixed_file}    Run Keyword And Ignore Error    Mix Video And Audio    ${videofile}    ${soundfile}
    Log    AV Mixed : ${status}, ${mixed_file}    console=yes
    
    sleep    3s 
   
    # Soundbar 소리 출력 확인
    TV Should Not Mute
           
    # Keysender disconnect
    
    Axidraw Disconnect
    Sdb Disconnect

    
C_inputSpec+Procedure_Source change_HDMI1_1.0Ver
    # [Documentation]   Smart Home > Menu > Connected Devices > HDMI1
    # [Setup]    None
    # [Teardown]    None
    Retry sdb connect
    Navigation Connect
    Keysender Connect

    Webcam Videorecordstart              ${LOG_DIR}${/}SelectHDMI1_${TEST_NAME}.mp4    show_timestamp=ON
    
    Log    ${TEST_NAME}    console=yes
     
   
    keysender sendkey    KEY_SOURCE     delay=1
    keysender sendkey    KEY_LEFT       repeat=5   delay=3   
    
    # Source Name을 TV와 동일하게 설정
    ${ReturnValue}    Navigation NUI sendkey Until Focused Text Is     OllehTV     KEY_RIGHT    
    
    Log to console  ${ReturnValue}    
   
    sleep  3s   
    
    Keysender sendkey     KEY_OK       delay=5
    
    sleep  10s     
    
    Webcam Videorecordstop
    
    sleep  10s
    
    Log    ${TEST_NAME}    console=yes
    # Soundbar 소리 출력 확인
    ${status}   ${value}  Run Keyword And Ignore Error     TV Should Not Mute
    run keyword if  '${status}'=='FAIL'    
    ...                   Run Keywords      log to console    This Test is failed(Mute)
    ...    AND    Webcam Videorecordstart     ${LOG_DIR}${/}Current Sound Output_${TEST_NAME}.mp4    show_timestamp=ON
    ...    AND    Get Current Sound Output
    ...    AND    Webcam Videorecordstop
    
    Sleep     120s
    

    Keysender disconnect
    Navigation disconnect
    Sdb Disconnect

    
C_inputSpec+Procedure_Source change_HDMI2_1.0Ver
    [Documentation]   Smart Home > Menu > Connected Devices > HDMI2
    [Setup]    None
    [Teardown]    None
    Retry sdb connect
    Navigation Connect
    Keysender Connect

    Webcam Videorecordstart              ${LOG_DIR}${/}SelectHDMI2_${TEST_NAME}.avi    show_timestamp=ON

    Log    ${TEST_NAME}    console=yes
     
   
    keysender sendkey    KEY_SOURCE     delay=1
    keysender sendkey    KEY_LEFT       repeat=5   delay=3   
    
    # Source Name을 TV와 동일하게 설정
    ${ReturnValue}    Navigation NUI sendkey Until Focused Text Is   SK Broadband    KEY_RIGHT    
    Log to console  ${ReturnValue}    
    
     
    sleep  3s   
    
    Keysender sendkey     KEY_OK       delay=5
   
    sleep  10s     
    
    Webcam Videorecordstop
    
    sleep  10s
     
         
    Log    ${TEST_NAME}    console=yes
    # Soundbar 소리 출력 확인
    ${status}   ${value}  Run Keyword And Ignore Error     TV Should Not Mute
    run keyword if  '${status}'=='FAIL'    
    ...                   Run Keywords      log to console    This Test is failed(Mute)
    ...    AND    Webcam Videorecordstart     ${LOG_DIR}${/}Current Sound Output_${TEST_NAME}.avi    show_timestamp=ON
    ...    AND    Get Current Sound Output
    ...    AND    Webcam Videorecordstop
    
    Sleep     120s
    


    
    Keysender disconnect
    Navigation disconnect

C_inputSpec+Procedure_Source change_HDMI4_1.0Ver
    [Documentation]   Smart Home > Menu > Connected Devices > HDMI4
    [Setup]    None
    [Teardown]    None
    Retry sdb connect
    Navigation Connect
    Keysender Connect

    Webcam Videorecordstart              ${LOG_DIR}${/}SelectHDMI4_${TEST_NAME}.avi    show_timestamp=ON     

    Log    ${TEST_NAME}    console=yes
     
   
    keysender sendkey    KEY_SOURCE     delay=1
    keysender sendkey    KEY_LEFT       repeat=5   delay=3   
    
    # Source Name을 TV와 동일하게 설정
    ${ReturnValue}    Navigation NUI sendkey Until Focused Text Is   LG U+    KEY_RIGHT    
    Log to console  ${ReturnValue}    
    
     sleep  3s   
    
    Keysender sendkey     KEY_OK       delay=5

    sleep  10s     
    
    Webcam Videorecordstop
    
    sleep  10s
           
    Log    ${TEST_NAME}    console=yes
    # Soundbar 소리 출력 확인
    ${status}   ${value}  Run Keyword And Ignore Error     TV Should Not Mute
    run keyword if  '${status}'=='FAIL'    
    ...                   Run Keywords      log to console    This Test is failed(Mute)
    ...    AND    Webcam Videorecordstart     ${LOG_DIR}${/}Current Sound Output_${TEST_NAME}.avi    show_timestamp=ON
    ...    AND    Get Current Sound Output
    ...    AND    Webcam Videorecordstop
    
    Sleep     120s
    

  
    Keysender disconnect
    Navigation disconnect



C_inputSpec+Procedure_PowerOff/On_30s~300s_Random_1.0ver
    [Documentation]   TV 리모컨으로 TV Power Off-on 후 mute check
    [Setup]    None
    [Teardown]    None
   
    Retry sdb connect
    Navigation Connect
    Keysender Connect
    
    Log    ${TEST_NAME}    console=yes
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    Log    [${SoundOutput}]    console=yes
    
    Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    # OFF_TV_STB
    
    Sleep Timing    30s    150s   300s
    # Sleep    30s
    Soft Power Reboot

    
    # OSD 확인
    Check Current Sound Output     ${SoundOutput}
    
    # Soundbar 소리 출력 확인
    TV Should Not Mute
    
    Keysender disconnect
    
   


ARK_Test only_inputSpec+Procedure_PowerOff/On_30s~300s_Random_1.0ver
    [Documentation]   TV 리모컨으로 TV Power Off-on 후 mute check
    [Setup]    None
    [Teardown]    None
   
     Retry sdb connect
     Navigation Connect
     Keysender Connect
    
    Log    ${TEST_NAME}    console=yes
   
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    Log    [${SoundOutputMemo}]    console=yes
    Select Sound Output    ${SoundOutputMemo}
    Log    [${SoundOutput}]    console=yes
    
    Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    # OFF_TV_STB
    
    Sleep    10s
    # Sleep    30s
   
    Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    # Athub SendIR       DISCRET_POWER_ON    
    # Athub SendIR       DISCRET_POWER_ON    
    # Athub SendIR       DISCRET_POWER_ON    
    # Athub SendIR       DISCRET_POWER_ON    
    # Athub SendIR       DISCRET_POWER_ON  
    
     
    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # keysender sendkey    KEY_MENU    delay=2    
    # keysender sendkey    KEY_DOWN    delay=2    
    # keysender sendkey    KEY_PANEL_EXIT    delay=2    
    # keysender sendkey    KEY_OK    delay=2       
    Log    Sleep 10s

    # Soundbar 소리 출력 확인
    TV Should Not Mute
    
    Keysender disconnect

NEWFEATURE_SOURCE_CHANGE_PowerOff/On_COLDBOOT
    [Documentation]   TV 리모컨으로 TV Power Off-on 후 mute check
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S

    
    ${variable}=    Log    ${TEST_NAME}    console=yes
    Log    [Video Record Start]    console=yes    
        Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # OFF_TV_STB
    Sleep    180s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    
        ${videofile} =    Webcam Videorecordstop 
    Log    [Video Record stop]    console=yes
    # Log    Sleep 20s
    Sleep    5s

    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    # Soundbar 소리 출력 확인
    TV Should Not Mute
 
    # Keysender disconnect
    

NEWFEATURE_TVPLUS 
    [Documentation]   TV 리모컨으로 TVPLUS 전환 후 Power Off/On
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S

    
    ${variable}=    Log    ${TEST_NAME}    console=yes
    Log    [Video Record Start]    console=yes    
        Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # OFF_TV_STB
    # Sleep    30s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    
    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    Sleep    10s

    Athub SendIR       KEY_CH_LIST    delay=2    
    
    Sleep    10s
 
      ${videofile} =    Webcam Videorecordstop 
    Log    [Video Record stop]    console=yes
    # Log    Sleep 20s


    # Soundbar 소리 출력 확인
    TV Should Not Mute

    # Source 변경 TVPLUS에서 STB로 변경
    Athub SendIR       KEY_PANEL_EXIT    delay=2 
    Athub SendIR       KEY_PANEL_EXIT    delay=2 
    Athub SendIR       KEY_OK    delay=2 
  
    # Keysender disconnect
NEWFEATURE_24 AUTOMATION TEST 
    [Documentation]  STB TVPLUS 소스 전환 및 POWER OFF/ON
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # OFF_TV_STB
    Sleep  20s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    10s

    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    # Soundbar 소리 출력 확인
    TV Should Not Mute
 
    Sleep    10s 
   
  # TVPLUS 소스 전환 
    Athub SendIR       KEY_CH_LIST    delay=2  

    Sleep    10s 

 # Soundbar 소리 출력 확인 
    TV Should Not Mute
    
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep  180s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    10s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute
    
    Sleep    10s
    
    # Source 변경 TVPLUS에서 STB로 변경
   Athub SendIR     KEY_SOURCE    delay=3    
   Athub SendIR     KEY_RIGHT    delay=3    
   Athub SendIR     KEY_OK    delay=3   
  
    Sleep    10s
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute


    # Keysender disconnect

NEWFEATURE_24 AUTOMATION TEST (MBR)
    [Documentation]  STB TVPLUS 소스 전환 및 POWER OFF/ON
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # OFF_TV_STB
    Sleep  10s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    20s

    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    # Soundbar 소리 출력 확인
    TV Should Not Mute
 
    Sleep    10s 
   
  # TVPLUS 소스 전환 
    Athub SendIR     KEY_SOURCE    delay=2    
    Athub SendIR     KEY_LEFT    delay=2   
    Athub SendIR     KEY_OK    delay=2 

    Sleep    10s 

 # Soundbar 소리 출력 확인 
    TV Should Not Mute
    
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep  180s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    20s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute
    
    Sleep    10s
    
    # Source 변경 TVPLUS에서 STB로 변경
   Athub SendIR     KEY_SOURCE    delay=2    
   Athub SendIR     KEY_RIGHT    delay=2   
   Athub SendIR     KEY_OK    delay=2   
  
    Sleep    10s
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute


    # Keysender disconnect


24 AUTOMATION TEST (NETFLIX)
    [Documentation]  STB TVPLUS NETFLIX 소스 전환 및 POWER OFF/ON
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # OFF_TV_STB
    Sleep  10s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    20s

    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    # Soundbar 소리 출력 확인
    TV Should Not Mute
 
    Sleep    10s 
   
  # TVPLUS 소스 전환 
    Athub SendIR     KEY_SOURCE    delay=2    
    Athub SendIR     KEY_LEFT    delay=2   
    Athub SendIR     KEY_OK    delay=2 

    Sleep    10s 

 # Soundbar 소리 출력 확인 
    TV Should Not Mute
    
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep  180s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    20s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute
    
    Sleep    10s
    
    # Source 변경 TVPLUS에서 STB로 변경
   Athub SendIR     KEY_SOURCE    delay=2    
   Athub SendIR     KEY_RIGHT    delay=2   
   Athub SendIR     KEY_OK    delay=2   
  
    Sleep    10s
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute

    Athub SendIR     KEY_CONTENTS    delay=2    
    Athub SendIR     KEY_UP    delay=2    
    Athub SendIR     KEY_RIGHT    delay=2       
    Athub SendIR     KEY_OK    delay=2  

    Sleep    10s

    Athub SendIR     KEY_OK    delay=2    
    Athub SendIR     KEY_OK    delay=2

    # Soundbar 소리 출력 확인
    Sleep    180s

    TV Should Not Mute 

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep  180s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    # Keysender disconnect
25 AUTO TEST (Coldboot)
    [Documentation]   Set Coldboot
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    
    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes

    Athub Setmasterpower    OFF
    
    Sleep  30s

    Athub Setmasterpower    ON
    # OFF_TV_STB

    Sleep  100s
 
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute
   
    Sleep    10s

 # Keysender disconnect 

25 AUTO TEST ( TV Instant Power Test )
    [Documentation]  TV Instant Power Off On
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    # OFF_TV_STB
    Sleep  20s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    
    # Athub Setmasterpower    OFF
    # Coldboot 
    # Sleep    30s
    
    # Athub Setmasterpower    ON

    Sleep    30s

    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    # Soundbar 소리 출력 확인
    TV Should Not Mute
   
    Sleep    10s

 # Keysender disconnect 

24 AUTO TEST (STB에서 TVPLUS로 소스 변경 #2)
    [Documentation]  STB TVPLUS 소스 전환 
    [Setup]    None
    [Teardown]    None
    
    Sleep    30s
    # TVPLUS 소스 전환 
    Athub SendIR     KEY_SOURCE    delay=2    
    Athub SendIR     KEY_LEFT      delay=2    
    Athub SendIR     KEY_OK        delay=2    
 
    Sleep    60s

  # Soundbar 소리 출력 확인 
    TV Should Not Mute

    Sleep    30s
    
  # Keysender disconnect 

24 AUTO TEST (TVPLUS에서 Suspend Power #3)
    [Documentation]   TVPLUS에서 Suspend Power
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep  10s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    30s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    20s

    # Keysender disconnect 

24 Random Time Power Test
    [Documentation]   Random 으로 SLEEP TIME 설정 POWER TEST
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep Timing    30s    150s   300s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    30s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    20s

    # Keysender disconnect 

24 AUTO TEST (TVPLUS에서 STB 소스 전환 #4)
    [Documentation]   TVPLUS에서 Suspend Power
    [Setup]    None
    [Teardown]    None  
    
    Sleep    30s
    # Source 변경 TVPLUS에서 STB로 변경
    Athub SendIR     KEY_SOURCE    delay=2  
    Athub SendIR     KEY_RIGHT    delay=2   
    Athub SendIR     KEY_OK    delay=2   
  
    Sleep    30s
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute

    Sleep    10s

24 AUTO TEST (TVPLUS에서 NETFLIX 실행 #5)
    [Documentation]   TVPLUS에서 NETFLIX로
    [Setup]    None
    [Teardown]    None
    
    Sleep    10s

    Athub SendIR     KEY_FUNCTIONS_NETFLIX 

    Sleep    10s

    Athub SendIR     KEY_OK    delay=2    
    
    Sleep    60s

    TV Should Not Mute 
     # Soundbar 소리 출력 확인 

    # Athub Setmasterpower    OFF
    # Coldboot 
    Sleep   10s   

    Athub SendIR    KEY_SOURCE    delay=3       
    Athub SendIR    KEY_OK    delay=2 

    # Athub Setmasterpower    ON

    # Keysender disconnect

24 AUTO TEST (TVPLUS에서 20Min Power #6)
    [Documentation]   TVPLUS에서 Suspend Power
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep  1200s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    120s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    20s

24 AUTO TEST (TVPLUS에서 30Min Power #7)
    [Documentation]   TVPLUS에서 Suspend Power
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep  1800s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    120s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    20s
    # Keysender disconnect 

    
24 AUTO TEST (자동 OTN TEST)
    [Documentation]   TVPLUS에서 Suspend Power
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    
    Sleep  1800s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    600s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    20s
    # Keysender disconnect 

24 AUTO TEST (OTN TEST_AUTO UPDATE CASE)
    [Documentation]   TVPLUS에서 Suspend Power
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    
    Sleep  60s

    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON     
        
    Sleep  1200s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    60s
  
    

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    20s
    # Keysender disconnect 

25 AUTO TEST ( TV Suspend Power Test )
    [Documentation]   TV Suspend Power Off On
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    # OFF_TV_STB
    Sleep  180s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    
    # Athub Setmasterpower    OFF
    # Coldboot 
    # Sleep    30s
    
    # Athub Setmasterpower    ON

    Sleep    30s

    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    # Soundbar 소리 출력 확인
    TV Should Not Mute
   
    Sleep    10s

 # Keysender disconnect 


25 AUTO TEST ( S/Bar Hiddenboot Test )
    [Documentation]  Soundbar Hiddenboot Test
    [Setup]    None
    [Teardown]    None
   
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    

    # TV Power Off
    # Log    DISCRET_POWER_OFF    console=yes
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    
    Athub Setmasterpower    OFF
    
    Sleep  30s

    Athub Setmasterpower    ON


    # OFF_TV_STB
    Sleep  30s
    # Soft Power Reboot

    # Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    Athub SendIR       DISCRET_POWER_ON 
    
    # Athub Setmasterpower    OFF
    # Coldboot 
    # Sleep    30s
    
    # Athub Setmasterpower    ON

    Sleep    120s

    # OSD 확인
    # Check Current Sound Output     ${SoundOutput}
    # sleep    2s
    # Athub SendIR    KEY_VOLUP    delay=2 
    # sleep    2s    
    # Athub SendIR    KEY_VOLDOWN  delay=2  
    # Soundbar 소리 출력 확인
    TV Should Not Mute
   
    Sleep    10s
 # Keysender disconnect 


24 AUTO TEST ( Aging Mute Check #10)
    [Documentation]  APP에서 5분주기로 무음 CHECK 
    [Setup]    None
    [Teardown]    None
   power off
    # Retry sdb connect
    # Navigation Connect
    # Keysender Connect
    # ${timestring} =          Get Current Date       result_format=%m%d_%H%M%S
      
    # ${variable}=    Log    ${TEST_NAME}    console=yes
    # Log    [Video Record Start]    console=yes    
    # Webcam Videorecordstart     VIDEO_${timestring}.avi    show_timestamp=ON 
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    # Log    [${SoundOutput}]    console=yes
    # Select Sound Output    ${SoundOutput}
    
    Sleep    300Sec

    TV Should Not Mute

    Sleep    10s

 # Keysender disconnect 

25 AUTO TEST ( TV Power Off 20분후 Power On )
    [Documentation]   TV Power Off On 10분후
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    
    Sleep  1200s
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    60s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    10s

25 AUTO TEST ( TV Power Off 후 S/Bar Coldoboot TV Power On)
    [Documentation]  TV Power Off 후 S/Bar Coldoboot TV Power On
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    
    Athub Setmasterpower    OFF
    
    Sleep  30s

    Athub Setmasterpower    ON
  
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 

    Sleep    120s
  
    # ${videofile} =    Webcam Videorecordstop 
    # Log    [Video Record stop]    console=yes
    # Log    Sleep 20s

    # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    10s

25 AUTO OTN TEST (Case #1 Standby 상태 2분후 Power On / Off 후 업데이트 후 검증)
    [Documentation]   업데이트 중 TV Power On/Off 업데이트 중지 후 다시 업데이트 이후 콜드붓
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # STANDBY 상태 진입

    Sleep  120s
    # STANDBY 상태 업데이트 진입

    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 
    # STANDBY 상태 업데이트 중 강제 업데이트 중지

    Sleep  60s

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    
    Sleep  1200s 
    # STANDBY 상태 진입하여 업데이트 다시 진행
    
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON
   # 업데이트 완료 
    Sleep  30s

    Athub Setmasterpower    OFF
    
    Sleep  20s

    Athub Setmasterpower    ON
    # Partition 삭제 유무 CHECK

    Sleep    120s
  
   # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    10s

25 AUTO OTN TEST (Case #2 Standby 상태 업데이트 검증)
    [Documentation]   정상 업데이트 후 콜드붓 후 동작 확인
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # STANDBY 상태 진입

    Sleep  1200s
    # STANDBY 상태 업데이트 진행/완료

    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON 
    # 업데이트 후 SET Power On 

    Sleep  60s

    Athub Setmasterpower    OFF
    
    Sleep  20s

    Athub Setmasterpower    ON
    # Partition 삭제 유무 CHECK 

    Sleep    1200s
  
   # Soundbar 소리 출력 확인
    TV Should Not Mute

    Sleep    10s

24 AUTO TEST ( SOUNDOUT #11 )
    [Documentation]  GO TO SOUNDOUT 
    [Setup]    None
    [Teardown]    None
   
    
    Athub SendIR  KEY_MENU    delay=2    
    Athub SendIR  KEY_DOWN    delay=2    
    Athub SendIR  KEY_RIGHT    delay=2    
    Athub SendIR  KEY_OK    delay=2    
    Athub SendIR  KEY_DOWN    delay=2    
    Athub SendIR  KEY_OK    delay=2   

    Sleep    30s 

    TV Should Not Mute
   
    Sleep    10s
 # Keysender disconnect 

24 WiFi Coldboot TEST (TVPLUS)
    [Documentation]  STB Coldboot
    [Setup]    None
    [Teardown]    None
      
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # TV Power Off

    Sleep  10s

    Athub Setmasterpower    OFF
    
    Sleep  30s

    Athub Setmasterpower    ON
    # Soundbar Coldboot

    Sleep  60s
     
    TV Should Not Mute
    # Soundbar 소리 출력 확인
   
    Sleep    10s

 # Keysender disconnect 

25 Soundbar Test (Soundbar Coldboot 5S)
    [Documentation]  Soundbar Coldboot
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # TV Power Off

    Sleep  10s

    Athub Setmasterpower    OFF
    # Soundbar Coldboot

    Sleep  10s

    Athub Setmasterpower    ON
        
    Sleep  10s

    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 

    Sleep  60s
 
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute
   
    Sleep    10s

 # Keysender disconnect 

25 Soundbar Test (Soundbar Coldboot 30S)
    [Documentation]  Soundbar Coldboot
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # TV Power Off

    Sleep  10s

    Athub Setmasterpower    OFF
    # Soundbar Coldboot

    Sleep  10s

    Athub Setmasterpower    ON
        
    Sleep  30s

    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 

    Sleep  60s
 
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute
   
    Sleep    10s

 # Keysender disconnect 

 
25 Soundbar Test (Soundbar Coldboot Suspend)
    [Documentation]  Soundbar Coldboot
    [Setup]    None
    [Teardown]    None

    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    # TV Power Off

    Sleep  180s

    Athub Setmasterpower    OFF
    # Soundbar Coldboot

    Sleep  10s

    Athub Setmasterpower    ON
        
    Sleep  10s

    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON        
    Athub SendIR       DISCRET_POWER_ON 
    
    Sleep  10s

    Athub SendIR       KEY_VOLUP
    Athub SendIR       KEY_VOLDOWN

    Sleep  60s
 
    # Soundbar 소리 출력 확인
    
    TV Should Not Mute
   
    Sleep    10s

 # Keysender disconnect 


 RELEASE PowerOff/On_30s~300s_Random
    [Documentation]   TV 리모컨으로 TV Power Off-on 후 mute check
    [Setup]    None
    [Teardown]    None
    
    # TV Power Off
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF
    Athub SendIR       DISCRET_POWER_OFF

    Sleep Timing    30s    150s   300s
    # Sleep    30s

    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON
    Athub SendIR       DISCRET_POWER_ON

       
    # Soundbar 소리 출력 확인
    TV Should Not Mute
    
    # Keysender disconnect

C_inputSpec+Procedure_Power_A/C PowerOff/On(ColdBoot)_1.1Ver
    [Setup]    None
    [Teardown]    None
     
    Retry sdb connect
    Navigation Connect
    Keysender Connect
    
       Log    ${TEST_NAME}    console=yes
    
    # # 조건 변경 전 설정되어 있는 SoundOutput 확인
    # ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    # Log    [${SoundOutputMemo}]    console=yes
    # Select Sound Output    ${SoundOutputMemo}
    Log    [${SoundOutput}]    console=yes
    Select Sound Output    ${SoundOutput}
  
    Log    POWER_OFF    console=yes
    
    Athub Setmasterpower    OFF
    
    Sleep    30s
    
    Log    POWER_ON    console=yes
    
    Athub Setmasterpower    ON
    Sleep    30s
    
    Retry sdb connect

    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
       
    Log    Sleep_180s    console=yes
    Sleep    180s
    
    
    
    # Sdb Set Root mode      ON 
    Log    Current_Sound Output_SPK    console=yes
    # Check Current Sound Output     ${SoundOutputMemo}
    Check Current Sound Output     ${SoundOutput}
    
    # Soundbar 소리 출력 확인
    Log    Sound_Mute Check    console=yes
    TV Should Not Mute
    
    Keysender disconnect



*** Keywords ***
SuiteSetupKW
    Log    [SuiteSetupKW]   console=yes
 
    ${dir} =     Get Log Dir
    Set Suite Variable    ${LOG_DIR}    ${dir}
    
    # Test
    Log    [TestSetupKW]    console=yes
    ${timestring} =    GetTimeString
    # SDB_TV.Sdb Enable Hyperuart          ${LOG_DIR}${/}Log_${TEST_NAME}_Hyper(TV)_${timestring}.txt
    # SDB_SOUNDBAR.Sdb Enable Hyperuart    ${LOG_DIR}${/}Log_${TEST_NAME}_Hyper(SOUNDBAR)_${timestring}.txt
    # Webcam Videorecordstart              ${LOG_DIR}${/}Log_${timestring}.avi    show_timestamp=ON
       
    Athub Connect

    # SDB_TV.Sdb Connect
    # Retry sdb connect
    # SDB_SOUNDBAR.Sdb Connect
    # Keysender Connect
    # Navigation Connect
    
    
    Webcam Fullscreen    ON
    # Webcam Showwebcam    ON
    
    Sound Set DB Threshold    ${DB_Threshold}    # Should be measured before test. (DeviceController.CheckDBThreshold)        
    Log    LOG_DIR [${LOG_DIR}]    console=yes    


TestSetupKW
    Log    [TestSetupKW]    console=yes
    ${timestring} =    GetTimeString
    # SDB_TV.Sdb Enable Hyperuart          ${LOG_DIR}${/}Log_${TEST_NAME}_Hyper(TV)_${timestring}.txt
    # SDB_SOUNDBAR.Sdb Enable Hyperuart    ${LOG_DIR}${/}Log_${TEST_NAME}_Hyper(SOUNDBAR)_${timestring}.txt
    Webcam Videorecordstart              ${LOG_DIR}${/}Log_${TEST_NAME}.avi    show_timestamp=ON
    

TestTeardownKW
    Log    [TestTeardownKW]    console=yes
    
    # FAIL이면 재부팅 후 초기 설정
    ${SoundOutputMemo} =    Get File    ${SoundOutputMemoFile}
    # Run Keyword If Test Failed    ColdbootAndRestoreSoundOutput    ${SoundOutputMemo}
    # Run Keyword If Test Failed    Select Sound Output Once    ${SoundOutputMemo}
    
    # Webcam Videorecordstop
    # SDB_SOUNDBAR.Sdb Disable Hyperuart
    # SDB_TV.Sdb Disable Hyperuart

    # # PASS이면 로그 파일 삭제
    # Run Keyword If Test Passed    Remove temp files


# Remove temp files
    # Log    Remove log files.    console=yes
    # Run Keyword And Ignore Error    Remove File    ${LOG_DIR}${/}Log_*
    # Run Keyword And Ignore Error    Remove File    ${LOG_DIR}${/}VideoMuteCheck_*
    # Run Keyword And Ignore Error    Remove File    ${LOG_DIR}${/}SoundMuteCheck_*



SuiteTeardownKW
    Run Keyword If Any Tests Failed    Power On    

    # SDB_SOUNDBAR.Sdb Disconnect
    # SDB_TV.Sdb Disconnect
    Athub Disconnect
    Navigation Disconnect
    Keysender Disconnect
    
    Webcam Videorecordstop
    # Axidraw Disconnect
    Debugshell Disconnect
    sdb disconnect
    
# Check Current Sound Output
    # [Arguments]    ${soundoutput}
    # Log    [Check Current Sound Output] ${soundoutput}    console=yes
    
        # FOR    ${retry_cnt}    IN RANGE    5
        # ${passed} =    Run Keyword And Return Status    Check Current Sound Output Once    ${SoundOutput}
        # Exit For Loop If    ${passed}

        # Log     Retry [Check Current Sound Output Once(${retry_cnt})]   console=yes
    # END
    # Should Be True    ${passed}

Check Current Sound Output
    [Arguments]    ${soundoutput}
    
    Retry sdb connect
    Navigation Connect
    Keysender Connect
    
    Log    ${TEST_NAME}    console=yes
   
    wait until keyword succeeds    5x    5s    GotoSoundOutput  
    
    # Keysender disconnect
    
     
 
    
     #[Arguments]    ${soundoutput}
     # FOR    ${retry_cnt}    IN RANGE    5
        # Keysender Sendkey   KEY_MENU    delay=10
        # Keysender Sendkey   KEY_DOWN    delay=5
        # Keysender Sendkey   KEY_OK    delay=10
        
        # ${status}  ${EFL_focused_text} =    Run Keyword And Ignore Error    Navigation Efl Get Focused Texts
        # # ${EFL_focused_text} =  Navigation Efl Get Focused Texts
        # Log   [EFL_focused_text] ${EFL_focused_text}    console=yes
        # ${issoundoutput} =    Run Keyword And Return Status    Should Contain     ${EFL_focused_text}    Sound Output
        # Exit For Loop If    ${issoundoutput}
        
        # Run Keyword If    ${retry_cnt}>2     Soft Power Reboot
        # Log    Retry to read current sound output    console=yes
    # END
    # Should Contain     ${EFL_focused_text}    ${soundoutput}
    
Get Current Sound Output
    Keysender Sendkey   KEY_MENU    delay=3
    Keysender Sendkey   KEY_DOWN    delay=3
    Keysender Sendkey   KEY_RIGHT    delay=3
    
    ${EFL_focused_text} =  Navigation Efl Get Focused Texts
    Log   [EFL_focused_text] ${EFL_focused_text}    console=yes
    
    [Return]    ${EFL_focused_text}[3]
    
     Keysender Sendkey   KEY_RETURN    delay=3
     Keysender Sendkey   KEY_RETURN    delay=3
    
CheckDBThreshold
    Athub SendIR    KEY_VOLUP    # disable mute
    Athub SendIR    KEY_MUTE    
    ${dbFS} =   Sound Set DBFS Threshold Automatically
    Log    ${dbFS}    console=yes
    Athub SendIR    KEY_VOLDOWN
    
GET_EFL_TEXTS
    Log    [GET_EFL_TEXTS]    console=yes

    ${EFL_texts} =  Navigation Efl Get Texts
    Log   [EFL_texts] ${EFL_texts}    console=yes
    
    ${EFL_focused_text} =  Navigation Efl Get Focused Texts
    Log   [EFL_focused_text] ${EFL_focused_text}    console=yes

    ${timestring} =    GetTimeString
    # ${timestring} =    Get Current Date
    SDB_TV.Sdb Get Current Screen     ${LOG_DIR}${/}Log_captured_screen_${timestring}.png
    
GetTimeString
    ${datetime} =    Get Current Date
    Log To Console    DATETIME: ${datetime}
    
    ${timestring} =	   Convert Date	    ${datetime}    	result_format=%m%d_%H%M%S
    Log To Console    ${timestring}
    [Return]   ${timestring}


Soundbar Should Not Mute
    Log    [Soundbar Should Not Mute]    console=yes

    ${timestring} =    GetTimeString
    ${recordfile} =    Set Variable    ${LOG_DIR}${/}Log_${TEST_NAME}_${timestring}.wav
    Log    [recordfile : ${recordfile}]    console=yes
    SOUND RECORD    10s    ${recordfile}
    # ${noisereducedsound} =    Sound Noise Reduction    ${recordfile}    ${noise_path}
    # ${ret} =    Sound Has Mute    ${recordfile}    2
    # Log    HasMute? ${ret}    console=yes
        
    ${ret} =    Sound Is Mute    ${recordfile}
    Log    IsMute? ${ret}    console=yes
    Should Not Be True    ${ret}


TV Should Not Mute
    Log    [TV Should Not Mute]    console=yes

    ${timestring} =    GetTimeString
    Webcam Videorecordstart    ${LOG_DIR}${/}VideoMuteCheck_${timestring}.mp4    show_timestamp=ON
    Sound Record Start    ${LOG_DIR}${/}SoundMuteCheck_${timestring}.wav
    Sleep    30s
     
    Athub SendIR    KEY_MENU   delay=5   
    Athub SendIR    KEY_OK   delay=2 
    Athub SendIR    KEY_OK   delay=2 

    Sleep    10s

    ${videofile} =    Webcam Videorecordstop
    ${soundfile} =    Sound Record Stop

    ${status}    ${mixed_file}    Run Keyword And Ignore Error    Mix Video And Audio    ${videofile}    ${soundfile}
    Log    AV Mixed : ${status}, ${mixed_file}    console=yes
        
    ${ret} =    Sound Is Mute    ${soundfile}
    Log    IsMute? ${ret}    console=yes
    ${variable}=    Should Not Be True    ${ret}
    
    
GotoSoundMode
    
     Log    GotoSoundMode    console=yes
    
    Navigation Gotomenu       Sound > Sound Mode
    ${ReturnValue}    Navigation Efl Focused Texts Should Contain     Sound Mode 
    

    # Old Ver
    # Log    SoundMode   console=yes
    
    # FOR    ${retry_cnt}    IN RANGE    5
        # keysender sendkey   KEY_CONTENTS    delay=3
        # keysender sendkey   KEY_LEFT    delay=3
        # Keysender Sendkey   KEY_DOWN    delay=5
        # Keysender Sendkey   KEY_OK    delay=5
        # Keysender Sendkey   KEY_OK    delay=5
        # Keysender Sendkey   KEY_OK    delay=5
        # Keysender Sendkey   KEY_DOWN    delay=3
        # Keysender Sendkey   KEY_OK    delay=5
        # Keysender Sendkey   KEY_DOWN    delay=3
        # Keysender Sendkey   KEY_OK    delay=5

        # ${passed} =    Run Keyword And Return Status    Navigation Efl Texts Should Contain    Sound Mode
        # Exit For Loop If    ${passed}
        
        # Log    Retry to go [Digital Output Audio Format] (${retry_cnt})   console=yes
    # END
    
    
GotoSoundOutput
    
     Log    GotoSoundOutput    console=yes
    
    Navigation Gotomenu       Sound > Sound Output
    # ${ReturnValue}    Navigation Efl Focused Texts Should Contain     Sound Output 
    # ${status}    ${value} =    Run Keyword And Ignore Error    Navigation Efl Focused Texts Should Contain    Sound Output 
    
    # ${status}    ${value} =    Run Keyword And Ignore Error    Navigation Efl Focused Texts Should Contain        ${SoundOutputMemo}
    ${status}    ${value} =    Run Keyword And Ignore Error    Navigation Efl Focused Texts Should Contain    ${SoundOutput}
    
    Log    Test_${value}_display    console=yes

    run keyword if    '${status}'=='FAIL'
    ...               Run Keywords    log to console    This Test is failed   
    ...    AND        Webcam Videorecordstart              ${LOG_DIR}${/}GotoSoundOutput_${TEST_NAME}.avi    show_timestamp=ON
    ...    AND        sleep  3s
    ...    AND        Webcam Videorecordstop
    ...    AND        Fail

GotoSoundOutput_Old

    Log    GotoSoundOutput    console=yes
    
    Navigation Gotomenu       Sound > Sound Output
    # ${ReturnValue}    Navigation Efl Focused Texts Should Contain     Sound Output 
    ${status}    ${value} =    Run Keyword And Ignore Error    Navigation Efl Focused Texts Should Contain    Sound Output 
    
    run keyword if    '${status}'=='FAIL'
    ...               Run Keywords    log to console    This Test is failed   
    ...    AND        Webcam Videorecordstart              ${LOG_DIR}${/}GotoSoundOutput_${TEST_NAME}.avi    show_timestamp=ON
    ...    AND        sleep  3s
    ...    AND        Webcam Videorecordstop
    ...    AND        Fail


GotoSoundExpertSettingseARCMode
    
     Log    GotoSoundExpertSettingseARCMode    console=yes
    
    Navigation Gotomenu       Sound > Expert Settings > HDMI-eARC Mode
    ${ReturnValue}    Navigation Efl Focused Texts Should Contain     HDMI-eARC Mode   


    #old Ver
    #Log    GotoSoundExpertSettingseARCMode    console=yes
    
    #FOR    ${retry_cnt}    IN RANGE    5
    #keysender sendkey   KEY_CONTENTS    delay=3
    #keysender sendkey   KEY_LEFT    delay=3
    #Keysender Sendkey   KEY_DOWN    delay=5
    #Keysender Sendkey   KEY_RIGHT    delay=5
    #Keysender Sendkey   KEY_OK    delay=5
    #Keysender Sendkey   KEY_OK    delay=5
    #Keysender Sendkey   KEY_DOWN    delay=3
    # Sound
    #Keysender Sendkey   KEY_OK    delay=5
    #Keysender Sendkey   KEY_DOWN    delay=3
    #Keysender Sendkey   KEY_DOWN    delay=3
    #Keysender Sendkey   KEY_DOWN    delay=3
    #Keysender Sendkey   KEY_OK    delay=10
    #Log    Sound Expert Settings    console=yes
    #Keysender Sendkey   KEY_DOWN    delay=3
    #Keysender Sendkey   KEY_DOWN    delay=3

    # Navigation Efl Texts Should Contain    HDMI-eARC Mode
    #${passed} =    Run Keyword And Return Status    Navigation Efl Texts Should Contain    HDMI-eARC Mode
    #Exit For Loop If    ${passed}
        
    #Log    Retry to go [HDMI-eARC Mode] (${retry_cnt})   console=yes
    #END
    #Keysender Sendkey   KEY_OK    delay=3
    


GotoSoundExpertSettingsDigitaloutputaudioformat
    Log    GotoSoundExpertSettingsDigitaloutputaudioformat    console=yes
    
    Navigation Gotomenu       Sound > Expert Settings > Digital Output Audio Format
    ${ReturnValue}    Navigation Efl Focused Texts Should Contain     Digital Output Audio Format



GotoConnected Devices
    Log    Connected Devices   console=yes
    
        keysender sendkey   KEY_SOURCE     delay=3    

        ${ReturnValue}=    Navigation NUI Focused Texts Should Contain    Connected Devices
       
        

    
    
Select Sound Output
    [Arguments]    ${SoundOutput}    ${LIMIT_COUNT}=10
    Log    Select Sound Output (${SoundOutput})    console=yes
    
    FOR    ${retry_cnt}    IN RANGE    5
        ${passed} =    Run Keyword And Return Status    Select Sound Output Once    ${SoundOutput}    ${LIMIT_COUNT}        
        Exit For Loop If    ${passed}        

        Run Keyword If    ${retry_cnt}>2     Master Power Reboot
        Log     Retry [Select Sound Output Once(${retry_cnt})]   console=yes
    END
    Should Be True    ${passed}

  


Select Sound Output Once
    [Documentation]    Search SoundOutput from list. If cannot find the ${SoundOutput} in ${LIMIT_COUNT}, return fail.
    [Arguments]    ${SoundOutput}    ${LIMIT_COUNT}=10
    
    Log    Select Sound Output Once (${SoundOutput})    console=yes
    
    ${Passed} =    Run Keyword And Return Status    Check Current Sound Output    ${SoundOutput}
    Return From Keyword If    ${Passed}    ${True}
    
    # GotoSoundOutputList
    Keysender Sendkey    KEY_OK    delay=10
    
    # 이미 원하는 SoundOutput이 현재 선택되어 있으면 return
    ${current_focus} =    Navigation Efl Get Focused Texts
    ${ret} =    Run Keyword And Return Status    Should Contain    ${current_focus}    ${SoundOutput}        
    Run Keyword If    ${ret}    Return From Keyword    ${ret}
            
    # 다른 SoundOutput이 선택되어 있으면
    # 맨 위 항목으로 이동
    Keysender Sendkey    KEY_UP    delay=3    repeat=${LIMIT_COUNT}
    
    # 찾을 때 까지 KEY_DOWN 하면서 확인
    Log    ${SoundOutput}    console=yes
    ${ret} =	Run Keyword And Return Status    Navigation Efl Sendkey Until Focused Text Is    ${SPACE}${SoundOutput}    KEY_DOWN    retry=${LIMIT_COUNT}x
    Run Keyword If    ${ret}    Keysender Sendkey    KEY_OK    
    sleep      5s
    ${current_focus} =    Navigation Efl Get Focused Texts
    Log    ${current_focus}    console=yes
    
    Should Be True    ${ret}
    
    # GotoSourceSelection
    # Keysender Sendkey   KEY_PANEL_EXIT
    # Keysender Sendkey   KEY_PANEL_EXIT
    # Keysender Sendkey   KEY_SOURCE
    # Sleep    2s
    # Keysender Sendkey   KEY_DOWN

SetSourceSTB
    Log    TBD    console=yes
    
SetSourceRF
    Log To Console    SetSourceRF    
    Keysender Sendkey    KEY_EXIT    repeat=3
    Sleep    10s
    
    keysender sendkey    KEY_1    delay=1
    keysender sendkey    KEY_1    delay=1
    keysender sendkey    KEY_OK    delay=1
    Sleep    5s
    
    # Keysender Sendkey    KEY_EXIT    delay=5
    # SDB_TV.Sdb Sendshellcmd     launch_app org.tizen.channel-list
    # Sleep    10s
    # Keysender Sendkey    KEY_LEFT
    # Keysender Sendkey    KEY_UP    repeat=5
    # # Navigation Nui Sendkey Until Focused Text Is    TV    KEY_DOWN
    # Keysender Sendkey    KEY_DOWN
    # Keysender Sendkey    KEY_DOWN
    # Keysender Sendkey    KEY_DOWN
    # Keysender Sendkey    KEY_OK
    
SetSourceTVPlus
    Log To Console    SetSourceTVPlus
    
    # Keysender Sendkey    KEY_EXIT    delay=5
    # SDB_TV.Sdb Sendshellcmd     launch_app org.tizen.channel-list
    # Sleep    10s
    # Keysender Sendkey    KEY_LEFT
    # Keysender Sendkey    KEY_UP    repeat=5
    # # Navigation Nui Sendkey Until Focused Text Is    TV    KEY_DOWN
    # Keysender Sendkey    KEY_DOWN
    # Keysender Sendkey    KEY_DOWN
    # Keysender Sendkey    KEY_OK
    
    # 501
    Keysender Sendkey    KEY_EXIT    repeat=3
    Sleep    10s
    keysender sendkey    KEY_5    delay=1
    keysender sendkey    KEY_0    delay=1
    keysender sendkey    KEY_1    delay=1
    keysender sendkey    KEY_OK    delay=1    
    Sleep    15s
    
SetSourceNetflix
    Log To Console    SetSourceNetflix
    # GotoSourceSelection
    # Navigation Nui Sendkey Until Focused Text Is    Watch on Netflix    KEY_RIGHT    10x
    # Keysender Sendkey    KEY_OK    delay=10
    Log to console    Netflix App Launch
    SDB_TV.Sdb Sendshellcmd    launch_app org.tizen.netflix-app
    Sleep    15s
    
SetSourceYoutube
    Log to console   SetSourceYoutube
    SDB_TV.Sdb Sendshellcmd    launch_app com.samsung.tv.cobalt-yt
    Sleep    15s
    
ColdbootAndRestoreSoundOutput
    [Arguments]   ${SoundOutput}
    Log    Master Power OFF    console=yes
    Athub Setmasterpower    off
    sleep      10s
    
    Log    Master Power ON    console=yes
    Athub Setmasterpower    on
    sleep      10s
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON
    sleep      120s
    
    Log    Set SoundOutput : ${SoundOutput}    console=yes
    ${ret} =    Select Sound Output Once   ${SoundOutput}
    
ON_TV_STB
    Redrat SendIR   OLLEH_POWER_K    delay=0
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON
    Athub SendIR    DISCRET_POWER_ON

OFF_TV_STB
    Redrat SendIR    OLLEH_POWER_K    delay=0
    Keysender Sendkey    DISCRET_POWER_OFF

STB_CH_UP
    Redrat SendIR    OLLEH_CH_UP_K
    
STB_CH_DOWN
    Redrat SendIR    OLLEH_CH_DOWN_K    
    
Soft Power Reboot
    Log To Console    <Soft Power Reboot>
    # TV P  safekey=False
    # ON_TV_STBower On
    Log    DISCRET_POWER_ON    console=yes
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON    
    Athub SendIR       DISCRET_POWER_ON  
    
   Log    Sleep 30s    console=yes
     
   Sdb Set Root mode      ON      
    Log to console    </Soft Power Reboot>
  
    #${ret} =    Sound Is Mute    ${recordfile}
    # Log    IsMute? ${ret}    console=yes
    

    #Should Not Be True    ${ret}

Soft Power Reboot_Record
    Log To Console    <Soft Power Reboot>
    # TV P  safekey=False
    # ON_TV_STBower On
    Log    DISCRET_POWER_ON    console=yes
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON    safekey=False
    Keysender Sendkey    DISCRET_POWER_ON  
    
    ${timestring} =    GetTimeString
    ${recordfile} =    Set Variable    ${LOG_DIR}${/}Record_${TEST_NAME}_${timestring}.wav
    Log    [recordfile : ${recordfile}]    console=yes
    SOUND RECORD    10s    ${recordfile}

    Log    Sleep 40s    console=yes
    Sleep    40s   
    Log to console    </Soft Power Reboot>
  
    #${ret} =    Sound Is Mute    ${recordfile}
    # Log    IsMute? ${ret}    console=yes
    

    #Should Not Be True    ${ret}

Master Power Reboot
    Log To Console   <Master Power OOFF>
     Athub Setmasterpower    OFF
    
    Log    [Sleep Timing 30s ~ 300s Random]    console=yes
     Sleep Timing    60s    150s   300s
    
    Athub Setmasterpower    ON

     Log    [Sleep 120s]    console=yes
     Sleep      120s

    Log To Console   <Master Power ON>
    
Power On
    Log To Console    [Power On]
    Athub SendIR    DISCRET_POWER_ON    repeat=5
    Sleep    30s
    
    
Master Power Reboot for SDB
    Log To Console    [ Master Power Reboot]    
    sleep      10s
    athub setmasterpower    off
    sleep      10s
    athub setmasterpower    on
	sleep      10s
	athub sendIR    DISCRET_POWER_ON    repeat=5    delay=3
    sleep      180s

Retry sdb connect
    ${status}    ${value} =    Run Keyword And Ignore Error    wait until keyword succeeds     5 times     5s     check sdb connection
    run keyword if    '${status}'=='FAIL'
    ...     Run keywords    Log    sdb connect is failed total 5 times, try to kill SDB process     Error
    ...     AND             sleep   10s
    ...     AND             check sdb connection

check sdb connection
    ${passed} =     Run Keyword And Return Status    SDB_TV.sdb connect
    run keyword if    '${passed}'=='False'
    ...     Run keywords    Log    sdb connect is fail, try to reboot TV     Error
    ...     AND             Master Power Reboot for SDB	
    ...     AND             SDB_TV.sdb disconnect
    ...     AND             SDB_TV.sdb connect
    ...     ELSE            Log    sdb connect is success   console=yes
    sleep    5s
    
NUI OCR Check
    [Arguments]    ${find String}     
    ${ret}        navigation_nui_get_all_texts    
    log to console   ${ret}
    run keyword if    '${ret}'!='None'
    ...        Should not Contain Match    ${ret}    *${find String}    case_insensitive=False

EFL OCR Check_
    [Arguments]    ${find String}     
    ${ret}        navigation_efl get texts    
    log to console   ${ret}
    run keyword if    '${ret}'!='None'
    ...        Should not Contain Match    ${ret}    *${find String}    case_insensitive=False
EFL OCR Check_Next Step
    [Arguments]    ${find String}     
    ${ret}        navigation_efl get texts    
    log to console   ${ret}
    ${count}    Get Length     ${ret}   
    run keyword if    '${count}'!='0'
    ...        Should Contain Match   ${ret}    *${find String}    case_insensitive=False
    ...    ELSE
    ...        FAIL

Find Sub Menu
    [Arguments]    ${find String}    
    Keysender sendkey     KEY_UP      repeat=10   delay=1   
    ${ReturnValue}    Navigation efl sendkey until focused text is   ${find String}    KEY_DOWN     10x 
    Log to console  ${ReturnValue}    
    Keysender sendkey     KEY_OK       delay=5
    
    
Find Sub Menu_NUI
    [Arguments]    ${find String}    
    Keysender sendkey     KEY_LEFT      repeat=10   delay=1   
    ${ReturnValue}    Navigation NUI sendkey Until Focused Text Is  ${find String}    KEY_RIGHT     10x 
    Log to console  ${ReturnValue}    
    Keysender sendkey     KEY_OK       delay=5
        

Record Video And Sound
    [Arguments]    ${duration}
    Sound Record Start
    Webcam Videorecordstart
    Sleep    ${duration}
    ${sound} =  Sound Record Stop
    ${video} =   Webcam Videorecordstop
    
    [Return]    ${video}    ${sound}
    
Vol_longpress_UPDown
    Log   Vol long Press  console=yes    
    
    
    Axidraw Sendkey    KEY_VOLUP    delay=2    longpress_time=3
    Axidraw Sendkey    KEY_VOLDOWN    delay=2    longpress_time=3

    # keysender sendkey    KEY_VOLUP    delay=2    longpress_time=3
    # keysender sendkey    KEY_VOLDOWN    delay=2    longpress_time=3

SearchDevice
    [Arguments]        ${FindingMessage}
    Log    [Move to ${FindingMessage}]    console=yes

    Sleep       3s
    # keysender sendkey    KEY_EXIT       delay=3   
    keysender sendkey    KEY_SOURCE    delay=2    
    keysender sendkey    KEY_LEFT       repeat=7   delay=3   
        
    ${result}    ${ReturnValue}         Run Keyword And Ignore Error    Navigation NUI sendkey Until Focused Text Is     ${FindingMessage}     KEY_RIGHT       
    run keyword if    '${ReturnValue}'!='${FindingMessage}'
    ...        FAIL     Not Found '${FindingMessage}'
    
    
    
VideoCheck_IsStatic
    [Return]    ${isStatic}
    Webcam Videorecordstart
    sleep   10s
    ${recordVideo}    Webcam Videorecordstop

    ${isStatic}        Video Isstatic    ${recordVideo}  

Random_Repeat_Delay
    FOR    ${i}    IN RANGE    2
        Log    [MBR Chup]    console=yes
        
        ${Delay_Value}=    Evaluate    random.choice(${KEY_DELAY})
        ${Navigation_Count_Value}    Evaluate    random.choice(${REPEAT_COUNT})
        ${Sleep_Value}    Evaluate    random.choice(${RANDOM_SLEEP})
        Log    [repeat]:${Navigation_Count_Value}, [delay]:${Delay_Value}, [Sleep]:${Sleep_Value}    console=yes
        ${status}    ${value}   Run Keyword And Ignore Error    keysender sendkey    KEY_CHUP    repeat=${Navigation_Count_Value}    delay=${Delay_Value}
        run keyword if  '${status}'=='FAIL'    
        ...                     Run Keywords      pause execution   error occur
        ...                     FAIL    No response   

        Log    Sleep_Time    console=yes
            Sleep    ${Sleep_Value}

        Log    [MBR Chdown]    console=yes    
        ${Delay_Value}=    Evaluate    random.choice(${KEY_DELAY})
        ${Navigation_Count_Value}    Evaluate    random.choice(${REPEAT_COUNT})
        ${Sleep_Value}    Evaluate    random.choice(${RANDOM_SLEEP})
        Log    [repeat]:${Navigation_Count_Value}, [delay]:${Delay_Value}, [Sleep]:${Sleep_Value}    console=yes
        ${status}    ${value}   Run Keyword And Ignore Error    keysender sendkey    KEY_CHDOWN    repeat=${Navigation_Count_Value}    delay=${Delay_Value}    safekey=False   
        run keyword if  '${status}'=='FAIL'    
        ...                     Run Keywords      pause execution   error occur
        ...                     FAIL    No response   
    END


Random_ALL
    FOR    ${i}    IN RANGE    4
        # Random key, repeat, Delay 선언 
        ${Navigation_Direction_Value}=    Evaluate    random.choice(${NAVIGATION})
        ${Delay_Value}=    Evaluate    random.choice(${KEY_DELAY})
        ${Navigation_Count_Value}    Evaluate    random.choice(${REPEAT_COUNT})
        ${Sleep_Value}    Evaluate    random.choice(${RANDOM_SLEEP})
        
        Log    [Direction]: ${Navigation_Direction_Value}, [repeat]:${Navigation_Count_Value}, [delay]:${Delay_Value}, [Sleep]:${Sleep_Value}    console=yes
        
        Log    [MBR Ch Change]    console=yes
                    ${status}    ${value}   Run Keyword And Ignore Error    keysender sendkey    ${Navigation_Direction_Value}    repeat=${Navigation_Count_Value}    delay=${Delay_Value}
            run keyword if  '${status}'=='FAIL'    
            ...                     Run Keywords      pause execution   error occur
            ...                     FAIL    No response   

        Log    Sleep_Time    console=yes
            Sleep    ${Sleep_Value}
    END