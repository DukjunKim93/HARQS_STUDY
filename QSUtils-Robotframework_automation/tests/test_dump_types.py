#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test cases for DumpManager Types
DumpManager 타입 정의 단위 테스트
"""

import unittest

from QSUtils.DumpManager.DumpTypes import DumpState, DumpMode, DumpTriggeredBy


class TestDumpTypes(unittest.TestCase):
    """DumpTypes 열거형 테스트 클래스"""

    def test_dump_state_values(self):
        """DumpState 열거형 값 테스트"""
        # 상태 값 확인
        self.assertEqual(DumpState.IDLE.value, "idle")
        self.assertEqual(DumpState.STARTING.value, "starting")
        self.assertEqual(DumpState.EXTRACTING.value, "extracting")
        self.assertEqual(DumpState.VERIFYING.value, "verifying")
        self.assertEqual(DumpState.COMPLETED.value, "completed")
        self.assertEqual(DumpState.FAILED.value, "failed")
        self.assertEqual(DumpState.TIMEOUT.value, "timeout")

    def test_dump_state_count(self):
        """DumpState 열거형 개수 확인"""
        self.assertEqual(len(DumpState), 7)

    def test_dump_mode_values(self):
        """DumpMode 열거형 값 테스트"""
        self.assertEqual(DumpMode.DIALOG.value, "dialog")
        self.assertEqual(DumpMode.HEADLESS.value, "headless")

    def test_dump_mode_count(self):
        """DumpMode 열거형 개수 확인"""
        self.assertEqual(len(DumpMode), 2)

    def test_dump_triggered_by_values(self):
        """DumpTriggeredBy 열거형 값 테스트"""
        self.assertEqual(DumpTriggeredBy.MANUAL.value, "manual")
        self.assertEqual(DumpTriggeredBy.CRASH_MONITOR.value, "crash_monitor")
        self.assertEqual(DumpTriggeredBy.QS_FAILED.value, "qs_failed")

    def test_dump_triggered_by_count(self):
        """DumpTriggeredBy 열거형 개수 확인"""
        self.assertEqual(len(DumpTriggeredBy), 3)

    def test_enum_string_representation(self):
        """열거형 문자열 표현 테스트"""
        # DumpState
        self.assertEqual(str(DumpState.IDLE), "DumpState.IDLE")
        self.assertEqual(repr(DumpState.IDLE), "<DumpState.IDLE: 'idle'>")

        # DumpMode
        self.assertEqual(str(DumpMode.DIALOG), "DumpMode.DIALOG")
        self.assertEqual(repr(DumpMode.HEADLESS), "<DumpMode.HEADLESS: 'headless'>")

        # DumpTriggeredBy
        self.assertEqual(str(DumpTriggeredBy.MANUAL), "DumpTriggeredBy.MANUAL")
        self.assertEqual(
            repr(DumpTriggeredBy.CRASH_MONITOR),
            "<DumpTriggeredBy.CRASH_MONITOR: 'crash_monitor'>",
        )

    def test_enum_equality(self):
        """열거형 동등성 비교 테스트"""
        # 동일한 값 비교
        self.assertEqual(DumpState.IDLE, DumpState.IDLE)
        self.assertEqual(DumpMode.DIALOG, DumpMode.DIALOG)
        self.assertEqual(DumpTriggeredBy.MANUAL, DumpTriggeredBy.MANUAL)

        # 다른 값 비교
        self.assertNotEqual(DumpState.IDLE, DumpState.STARTING)
        self.assertNotEqual(DumpMode.DIALOG, DumpMode.HEADLESS)
        self.assertNotEqual(DumpTriggeredBy.MANUAL, DumpTriggeredBy.CRASH_MONITOR)

    def test_enum_iteration(self):
        """열거형 순회 테스트"""
        # DumpState 순회
        states = list(DumpState)
        expected_states = [
            DumpState.IDLE,
            DumpState.STARTING,
            DumpState.EXTRACTING,
            DumpState.VERIFYING,
            DumpState.COMPLETED,
            DumpState.FAILED,
            DumpState.TIMEOUT,
        ]
        self.assertEqual(states, expected_states)

        # DumpMode 순회
        modes = list(DumpMode)
        expected_modes = [DumpMode.DIALOG, DumpMode.HEADLESS]
        self.assertEqual(modes, expected_modes)

        # DumpTriggeredBy 순회
        triggers = list(DumpTriggeredBy)
        expected_triggers = [
            DumpTriggeredBy.MANUAL,
            DumpTriggeredBy.CRASH_MONITOR,
            DumpTriggeredBy.QS_FAILED,
        ]
        self.assertEqual(triggers, expected_triggers)

    def test_enum_from_string(self):
        """문자열로부터 열거형 생성 테스트"""
        # DumpState
        self.assertEqual(DumpState("idle"), DumpState.IDLE)
        self.assertEqual(DumpState("starting"), DumpState.STARTING)

        # DumpMode
        self.assertEqual(DumpMode("dialog"), DumpMode.DIALOG)
        self.assertEqual(DumpMode("headless"), DumpMode.HEADLESS)

        # DumpTriggeredBy
        self.assertEqual(DumpTriggeredBy("manual"), DumpTriggeredBy.MANUAL)
        self.assertEqual(
            DumpTriggeredBy("crash_monitor"), DumpTriggeredBy.CRASH_MONITOR
        )
        self.assertEqual(DumpTriggeredBy("qs_failed"), DumpTriggeredBy.QS_FAILED)

    def test_enum_invalid_value(self):
        """잘못된 값으로 열거형 생성 시 예외 발생 테스트"""
        with self.assertRaises(ValueError):
            DumpState("invalid_state")

        with self.assertRaises(ValueError):
            DumpMode("invalid_mode")

        with self.assertRaises(ValueError):
            DumpTriggeredBy("invalid_trigger")


if __name__ == "__main__":
    unittest.main()
