*** Settings ***
Documentation    Simple script to control TV power using ATHub
Variables   BTS_Device_Settings.py
Library    BTS.BTS_ATHub    ${ATHub01}

*** Test Cases ***
Power On TV
    [Documentation]    Send IR command to power on the TV
    athub_connect
    athub_sendIR       DISCRET_POWER_ON
    athub_sendIR       DISCRET_POWER_ON
    athub_sendIR       DISCRET_POWER_ON
    athub_sendIR       DISCRET_POWER_ON
    athub_sendIR       DISCRET_POWER_ON
    athub_disconnect

Power Off TV
    [Documentation]    Send IR command to power off the TV
    athub_connect
    athub_sendIR       DISCRET_POWER_OFF
    athub_sendIR       DISCRET_POWER_OFF
    athub_sendIR       DISCRET_POWER_OFF
    athub_sendIR       DISCRET_POWER_OFF
    athub_sendIR       DISCRET_POWER_OFF
    Sleep    5s
    athub_disconnect

Power On Off Test
    [Documentation]    Test sequence: Power on, wait, then power off
    athub_connect
    athub_sendIR    KEY_POWER
    Sleep    10s
    athub_sendIR    KEY_POWER
    Sleep    5s
    athub_disconnect