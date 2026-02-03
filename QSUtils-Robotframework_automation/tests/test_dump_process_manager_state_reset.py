from QSUtils.DumpManager import DumpProcessManager, DumpMode, DumpState
from QSUtils.UIFramework.base.CommonEvents import CommonEventType


class _StubEventManager:
    def __init__(self):
        self.emitted = []

    def register_event_handler(self, event_type, handler):
        # not needed for this test
        pass

    def emit_event(self, event_type, args=None):
        self.emitted.append((event_type, args or {}))


class _StubLoggingManager:
    def __init__(self, log_directory: str):
        self.log_directory = log_directory


class _StubADBDevice:
    def __init__(self, serial: str):
        self.serial = serial


def test_dump_success_resets_state_to_idle(qtbot, tmp_path):
    logging_manager = _StubLoggingManager(str(tmp_path))
    adb_device = _StubADBDevice("TEST_SERIAL")
    em = _StubEventManager()

    dpm = DumpProcessManager(
        parent_widget=None,
        adb_device=adb_device,
        event_manager=em,
        logging_manager=logging_manager,
    )
    dpm.set_dump_mode(DumpMode.HEADLESS)

    # Arrange: VERIFYING 상태에서 검증이 성공하도록 최소 파일 구성
    zip_path = tmp_path / "dummy.zip"
    zip_path.write_bytes(b"x")
    dpm.working_dir = tmp_path
    dpm._set_state(DumpState.VERIFYING)

    # Act
    dpm._verify_dump_results()

    # Assert: 완료 이벤트 emit
    assert any(
        et == CommonEventType.DUMP_COMPLETED and args.get("success") is True
        for et, args in em.emitted
    )

    # Assert: 성공 완료 후 IDLE로 자동 복귀
    qtbot.wait(50)
    assert dpm.get_state() == DumpState.IDLE
