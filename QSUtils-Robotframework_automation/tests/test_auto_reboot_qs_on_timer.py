import pytest
from PySide6.QtWidgets import QWidget

from QSUtils.QSMonitor.features.AutoReboot.AutoRebootGroup import AutoRebootGroup


class _StubEventManager:
    def __init__(self):
        self._ready_listeners = []

    def add_ready_listener(self, cb):
        self._ready_listeners.append(cb)

    def emit_event(self, event, args):
        # no-op for tests
        pass


class _StubSettings:
    def __init__(self):
        self._store = {"auto_reboot": {}}

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value


class _StubDumpManager:
    def __init__(self):
        from QSUtils.DumpManager import DumpState

        self._state = DumpState.IDLE
        self._mode = None

    def get_state(self):
        return self._state

    def set_state(self, st):
        self._state = st

    def set_dump_mode(self, mode):
        self._mode = mode


class _StubDefaultMonitor:
    def __init__(self):
        self._is_success = False

    def is_symphony_success(self):
        return self._is_success

    def set_success(self, v: bool):
        self._is_success = v


class _StubDeviceContext:
    def __init__(self):
        self.event_manager = _StubEventManager()
        self.dump_manager = _StubDumpManager()
        self.settings_manager = _StubSettings()
        self.serial = "TEST_SERIAL"
        self._default_monitor = _StubDefaultMonitor()
        # Add adb_device attribute for testing
        self.adb_device = _StubADBDevice()

    def get_app_component(self, name: str):
        if name == "default_monitor_feature":
            return self._default_monitor
        return None


class _StubADBDevice:
    def __init__(self):
        self.is_connected = True


@pytest.fixture
def parent_with_em(qtbot):
    # parent 위젯이 event_manager를 갖도록 만들어 BaseEventWidget 초기 등록 경로를 만족시킨다.
    parent = QWidget()
    parent.event_manager = _StubEventManager()
    qtbot.addWidget(parent)
    return parent


@pytest.fixture
def group(qtbot, parent_with_em):
    dc = _StubDeviceContext()
    g = AutoRebootGroup(parent_with_em, dc)
    qtbot.addWidget(g)
    return g


def _enable_reboot_after_qs_on(g: AutoRebootGroup, enabled: bool = True):
    cb = g.ui_elements["reboot_after_qs_on_checkbox"]
    cb.setChecked(enabled)


def test_on_event_starts_qs_on_timer_without_main_timer(group, qtbot, monkeypatch):
    # Arrange: AutoReboot 실행 중, 메인 타이머는 비활성(가드 완화로도 동작해야 함)
    group.auto_reboot_running = True
    if group.auto_reboot_timer.isActive():
        group.auto_reboot_timer.stop()
    _enable_reboot_after_qs_on(group, True)

    called = {"v": 0}

    def fake_start():
        called["v"] += 1

    monkeypatch.setattr(group, "start_reboot_on_qs_timer", fake_start)

    # Act: On 이벤트 수신
    group._on_symphony_group_state_changed({"state": "On"})

    # Assert: 10s 타이머 시작 시도됨
    assert called["v"] == 1


def test_start_uses_last_state_cache(group, qtbot, monkeypatch):
    # Arrange
    group._last_symphony_state = "On"
    _enable_reboot_after_qs_on(group, True)

    called = {"v": 0}

    def fake_start():
        called["v"] += 1

    monkeypatch.setattr(group, "start_reboot_on_qs_timer", fake_start)

    # Act
    group._start_auto_reboot()

    # Assert: 시작 시점에 바로 타이머 시작
    assert called["v"] == 1


def test_checkbox_checked_uses_last_state_and_deferred(group, qtbot, monkeypatch):
    called = {"v": 0}

    def fake_start():
        called["v"] += 1

    monkeypatch.setattr(group, "start_reboot_on_qs_timer", fake_start)

    # Case 1: last_state == On → 즉시 시작 (체크박스 실제로 체크하여 시그널 경로 사용)
    group._last_symphony_state = "On"
    group.ui_elements["reboot_after_qs_on_checkbox"].setChecked(True)
    assert called["v"] >= 1

    # Case 2: last_state == Off → deferred path (DefaultMonitor가 True로 바뀌면 시작)
    group._last_symphony_state = "Off"
    group.device_context._default_monitor.set_success(True)
    start_calls_before = called["v"]
    # 토글 해제 후 다시 체크하여 deferred 경로 유발
    group.ui_elements["reboot_after_qs_on_checkbox"].setChecked(False)
    group.ui_elements["reboot_after_qs_on_checkbox"].setChecked(True)
    qtbot.wait(400)
    assert called["v"] >= start_calls_before + 1


def test_interval_paused_until_reconnect(group):
    # Arrange
    group.auto_reboot_running = True
    group.auto_reboot_elapsed_sec = 0
    group.total_run_seconds = 0
    group.ui_elements["autoreboot_interval_edit"].setText("5")
    group._waiting_for_device_reconnect = True

    # Act: reconnect 대기 중 tick
    group._on_auto_reboot_tick()

    # Assert: total duration은 증가하지만 interval 카운트는 유지
    assert group.total_run_seconds == 1
    assert group.auto_reboot_elapsed_sec == 0

    # Act: 연결 복구 이벤트 수신 후 tick
    group._on_device_connection_changed({"connected": True})
    group._on_auto_reboot_tick()

    # Assert: interval 카운트 재개
    assert group._waiting_for_device_reconnect is False
    assert group.auto_reboot_elapsed_sec == 1
