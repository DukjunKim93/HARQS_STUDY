*** Settings ***
# Standard libraries of Robot Framework
Library    BuiltIn
Library    Collections
# Library    DateTime
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
# Library    BTS.BTS_APC   ${APC01}
# Library    BTS.BTS_ATHub   ${ATHub01}
# Library    BTS.BTS_AxiDraw   ${AxiDraw01}
# Library    BTS.BTS_Common
# Library    BTS.BTS_DebugShell   ${DebugShell01}
# Library    BTS.BTS_HIDKeyboard   ${HIDKeyboard01}  
# Library    BTS.BTS_Image
# Library    BTS.BTS_KeySender   ${ATHub01}   ${DebugShell01}
# Library    BTS.BTS_MDC   ${MDC01}
# Library    BTS.BTS_Monitor   ${Monitor01}
# Library    BTS.BTS_Navigation   ${SDB01}   ${SDB01}   ${SDB01}
# Library    BTS.BTS_OCR
# Library    BTS.BTS_PatternGenerator   ${PatternGenerator01}
# Library    BTS.BTS_Picasso    ${Arduino01}
# Library    BTS.BTS_RedRat
# Library    BTS.BTS_Sdb   ${SDB01}
# Library    BTS.BTS_Sound   ${Sound01}
# Library    BTS.BTS_Tab    ${TAB01}
# Library    BTS.BTS_USBSelector   ${USBSeletor01}  
# Library    BTS.BTS_Video
# Library    BTS.BTS_WebCam   ${WebCam01}


# BTS common userkeyword
Resource    ${EXECDIR}${/}CommonKeyword.robot

# Setup and Teardown
Suite Setup     Log    [[Executed before any test cases or sub test suites in that test suite.]]    console=yes
Suite Teardown    Log    [[Executed after any test cases or sub test suites in that test suite.]]    console=yes

Test Setup      Log    [A test setup is something that is executed before a test case.]    console=yes
Test Teardown   Log    [A test teardown is executed after a test case.]    console=yes

*** Variables ***
# ${STRING}=        cat
# ${NUMBER}=        ${1}
# @{LIST}=          one    two    three
# &{DICTIONARY}=    string=${STRING}    number=${NUMBER}    list=@{LIST}
# ${ENVIRONMENT_VARIABLE}=    %{PATH}

*** Test Cases ***
Example Hello BTS
    Log To Console    Hello BTS

*** Keywords ***