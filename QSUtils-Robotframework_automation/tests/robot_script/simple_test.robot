*** Settings ***
Documentation    Simple test file for verification

*** Test Cases ***
Test Case 1
    [Documentation]    First simple test case
    Log    This is test case 1
    Should Be Equal    1    1

Test Case 2
    [Documentation]    Second simple test case
    Log    This is test case 2
    Should Be Equal    2    2

Test Case 3
    [Documentation]    Third simple test case
    Log    This is test case 3
    Should Be Equal    3    3
