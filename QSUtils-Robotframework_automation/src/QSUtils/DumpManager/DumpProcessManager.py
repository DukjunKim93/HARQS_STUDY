# -*- coding: utf-8 -*-
"""
Dump Process Manager for QSMonitor application.
Manages dump extraction processes with support for both manual and headless modes.
독립된 패키지로 리팩토링된 버전.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, QDateTime
from PySide6.QtWidgets import QDialog

from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.ADBDevice.DeviceLoggingManager import DeviceLoggingManager
from QSUtils.DumpManager.DumpDialogs import (
    DumpProgressDialog,
    DumpCancellationDialog,
    DumpCompletionDialog,
)
from QSUtils.DumpManager.DumpTypes import DumpState, DumpMode, DumpTriggeredBy
from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.Utils.DateTimeUtils import TimestampGenerator
from QSUtils.Utils.FileUtils import ensure_directory_exists
from QSUtils.Utils.Logger import LOGD, LOGI, LOGW, LOGE


class DumpProcessManager(QObject):
    """Dump 추출 Process 통합 관리 클래스 - 독립된 패키지 버전"""

    def __init__(
        self,
        parent_widget: Optional[QDialog],
        adb_device: ADBDevice,
        event_manager: EventManager,
        logging_manager: DeviceLoggingManager,
    ):
        """
        DumpProcessManager 초기화

        Args:
            event_manager: 이벤트 관리자
            adb_device: ADB 디바이스 객체
            logging_manager: 디바이스 로깅 매니저
            parent_widget: UI 부모 위젯 (선택적, 다이얼로그 표시용)
        """
        super().__init__()
        self.event_manager = event_manager
        self.adb_device = adb_device
        self.logging_manager = logging_manager
        self.device_serial = adb_device.serial  # adb_device에서 serial 가져오기
        self.parent_widget = parent_widget

        self.state = DumpState.IDLE
        self.dump_process: Optional[QProcess] = None
        self.timeout_timer: Optional[QTimer] = None
        self.headless_status_timer: Optional[QTimer] = None
        self.working_dir: Optional[Path] = None
        self.dump_mode = DumpMode.DIALOG  # 기본값으로 DIALOG 모드 설정
        self.triggered_by: Optional[DumpTriggeredBy] = None
        self.progress_dialog: Optional[DumpProgressDialog] = None
        self.cancellation_requested = False
        self.headless_start_time: Optional[QDateTime] = None
        self.previous_dump_mode: Optional[DumpMode] = None  # Mode 저장/복구용
        # 전역 이슈 디렉토리에서 작업할 경우 지정되는 경로(있으면 우선 사용)
        self._override_working_dir: Optional[Path] = None

        # 업로드 활성화 상태 (Dialog에서 전달받음)
        self.upload_enabled: bool = False

        self._setup_process()
        self._setup_timer()
        self._setup_event_handlers()

        LOGD(f"DumpProcessManager: Initialized with dump_mode: {self.dump_mode.value}")

    def _setup_process(self):
        """QProcess 초기 설정"""
        self.dump_process = QProcess(self)
        self.dump_process.setProcessChannelMode(QProcess.MergedChannels)

        # 시그널 연결
        self.dump_process.started.connect(self._on_process_started)
        self.dump_process.finished.connect(self._on_process_finished)
        self.dump_process.errorOccurred.connect(self._on_process_error)
        self.dump_process.readyReadStandardOutput.connect(self._on_output_available)

    def _setup_timer(self):
        """타임아웃 타이머 설정"""
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_timeout)

    def get_state(self) -> DumpState:
        return self.state

    def _set_state(self, new_state: DumpState):
        """상태 전환"""
        old_state = self.state
        self.state = new_state
        LOGD(
            f"DumpProcessManager: State changed from {old_state.value} to {new_state.value}"
        )

    def get_dump_mode(self) -> DumpMode:
        """Dump 모드 getter 메서드"""
        return self.dump_mode

    def set_dump_mode(self, mode: DumpMode):
        """Dump 모드 setter 메서드"""
        LOGI(f"DumpProcessManager: Setting dump mode to {mode.value}")
        self.dump_mode = mode

    def set_upload_enabled(self, enabled: bool):
        """업로드 활성화 상태 설정"""
        self.upload_enabled = enabled

    def _create_dump_completed_event_data(
        self, dump_path: str, success: bool, triggered_by: str
    ) -> Dict[str, Any]:
        """DUMP_COMPLETED 이벤트 데이터 생성"""
        return {
            "device_id": self.adb_device.serial,
            "dump_path": dump_path,
            "success": success,
            "triggered_by": triggered_by,
            "upload_enabled": self.upload_enabled,
        }

    def start_dump_extraction(self, triggered_by: DumpTriggeredBy) -> bool:
        """
        통합 dump 추출 시작 메서드

        Args:
            triggered_by: DumpTriggeredBy.MANUAL, CRASH_MONITOR, QS_FAILED

        Returns:
            성공 여부
        """
        if self.state != DumpState.IDLE:
            LOGW(f"DumpProcessManager: Already running (state: {self.state.value})")
            return False

        # dump_process가 None이거나 유효하지 않은 경우 새로 설정
        if self.dump_process is None:
            LOGD("DumpProcessManager: dump_process is None, setting up new process")
            self._setup_process()
        elif self.dump_process.state() != QProcess.ProcessState.NotRunning:
            LOGE(
                f"DumpProcessManager: dump_process is still running (state: {self.dump_process.state()})"
            )
            return False

        self.triggered_by = triggered_by
        self.cancellation_requested = False

        try:
            self._set_state(DumpState.STARTING)

            # 필수 속성 검증
            if self.logging_manager is None:
                raise AttributeError("logging_manager is None or not available")

            if self.device_serial is None:
                raise AttributeError("device_serial is None or not available")

            if self.dump_mode is None:
                raise AttributeError("dump_mode is not initialized")

            # 작업 디렉토리 설정 (전역 이슈 디렉토리 우선)
            if self._override_working_dir is not None:
                self.working_dir = self._override_working_dir
            else:
                self.working_dir = (
                    Path(self.logging_manager.log_directory)
                    / "dumps"
                    / self.device_serial
                )
            ensure_directory_exists(self.working_dir)

            # 작업 디렉토리 생성 확인
            if not self.working_dir.exists():
                raise FileNotFoundError(
                    f"Failed to create working directory: {self.working_dir}"
                )

            # 환경 변수 설정
            env = QProcessEnvironment.systemEnvironment()
            env.insert("ADB_SERIAL", self.device_serial)
            if self.dump_process is not None:
                self.dump_process.setProcessEnvironment(env)

            # 스크립트 경로 확인
            script_path = self._get_script_path()
            if not script_path.exists():
                raise FileNotFoundError(f"Dump script not found: {script_path}")

            # Process 시작
            if self.dump_process is not None:
                self.dump_process.setWorkingDirectory(str(self.working_dir))
                self.dump_process.start(str(script_path))

            # DIALOG 모드일 때만 진행 상황 다이얼로그 생성
            if self.dump_mode == DumpMode.DIALOG:
                self._create_progress_dialog()

            # 타임아웃 타이머 시작
            timeout_ms = (
                300000 if self.dump_mode == DumpMode.HEADLESS else 600000
            )  # headless: 5분, dialog: 10분
            if self.timeout_timer is not None:
                self.timeout_timer.start(timeout_ms)

            LOGD(
                f"DumpProcessManager: Started {self.dump_mode.value} dump extraction triggered by "
                f"{triggered_by.value} (timeout: {timeout_ms}ms)"
            )
            return True

        except Exception as e:
            self._handle_error(f"Failed to start dump: {e}")
            return False

    def _get_script_path(self) -> Path:
        """스크립트 파일 경로 가져오기"""
        # 스크립트 파일 경로 (DumpManager 패키지 내부로 이동됨)
        # 여러 방법으로 스크립트 파일 존재 여부 확인
        possible_paths = [
            Path(__file__).parent / "coredump_extraction_script.sh",
            # QSUtils/DumpManager/coredump_extraction_script.sh (현재 패키지 내부)
            Path(__file__).parent.parent
            / "DumpManager"
            / "coredump_extraction_script.sh",
            # QSUtils/DumpManager/coredump_extraction_script.sh (한 단계 상위에서)
            Path.cwd() / "QSUtils" / "DumpManager" / "coredump_extraction_script.sh",
            # 현재 작업 디렉토리/QSUtils/DumpManager/coredump_extraction_script.sh
        ]

        script_path = None
        for candidate_path in possible_paths:
            LOGD(f"DumpProcessManager: Checking script path: {candidate_path}")
            LOGD(f"DumpProcessManager: Script path exists: {candidate_path.exists()}")
            if candidate_path.exists():
                script_path = candidate_path
                LOGD(f"DumpProcessManager: Found script at: {script_path}")
                break

        # 스크립트를 찾지 못한 경우 현재 작업 디렉토리에서 확인 (fallback)
        if script_path is None:
            script_path = (
                Path.cwd() / "QSUtils" / "DumpManager" / "coredump_extraction_script.sh"
            )
            LOGD(f"DumpProcessManager: Fallback script_path: {script_path}")
            LOGD(
                f"DumpProcessManager: Fallback script_path exists: {script_path.exists()}"
            )

        return script_path

    def _create_progress_dialog(self):
        """DIALOG 모드용 진행 상황 다이얼로그 생성"""
        self.progress_dialog = DumpProgressDialog(self.parent_widget, self.dump_mode)
        self.progress_dialog.canceled.connect(self._on_user_cancelled)
        self.progress_dialog.setLabelText("Starting dump extraction...")
        self.progress_dialog.setRange(0, 100)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

    def _on_user_cancelled(self):
        """사용자 취소 요청 처리 (2단계 확인)"""
        LOGD("DumpProcessManager: Cancellation signal received")

        # Process가 이미 종료되었거나 취소된 경우 무시
        if (
            not self.dump_process
            or self.dump_process.state() != QProcess.ProcessState.Running
        ):
            LOGD("DumpProcessManager: Process not running, ignoring cancellation")
            return

        if self.cancellation_requested:
            LOGD(
                "DumpProcessManager: Cancellation already requested, ignoring duplicate request"
            )
            return

        # 2단계 확인 다이얼로그
        cancel_dialog = DumpCancellationDialog(self.parent_widget)
        result = cancel_dialog.exec()

        if result == QDialog.Accepted:
            # 사용자가 취소 확인
            cleanup_requested = cancel_dialog.should_cleanup_target()

            LOGD(
                f"DumpProcessManager: Cancellation confirmed - cleanup target: {cleanup_requested}"
            )
            self.cancellation_requested = True

            # Process 종료
            if (
                self.dump_process
                and self.dump_process.state() == QProcess.ProcessState.Running
            ):
                LOGD("DumpProcessManager: Terminating dump process")
                self.dump_process.terminate()

                # 5초 후 강제 종료
                QTimer.singleShot(
                    5000, lambda: self._force_terminate_process(cleanup_requested)
                )
        else:
            # 취소하지 않음 - 다이얼로그 계속 표시
            LOGD("DumpProcessManager: Cancellation cancelled by user, continuing dump")
            if self.progress_dialog and self.dump_mode == DumpMode.DIALOG:
                self.progress_dialog.show()

    def _force_terminate_process(self, cleanup_target: bool):
        """Process 강제 종료 및 target cleanup"""
        if (
            self.dump_process
            and self.dump_process.state() == QProcess.ProcessState.Running
        ):
            LOGD("DumpProcessManager: Force killing dump process")
            self.dump_process.kill()

        # coredump 파일 삭제 (요청된 경우)
        if cleanup_target:
            self._cleanup_target_coredump_files()

    def _cleanup_target_coredump_files(self):
        """Target device의 coredump 파일 삭제"""
        try:
            LOGD("DumpProcessManager: Cleaning up coredump files from target device")

            # coredump 디렉토리 삭제
            cleanup_commands = [
                "rm -rf /data/var/lib/systemd/systemd-coredump/*",
                "rm -rf /data/tmp/crash-alarm/*",
            ]

            for cmd in cleanup_commands:
                result = self.adb_device.execute_adb_shell(cmd)
                if result is None:
                    LOGD(
                        f"DumpProcessManager: Failed to execute cleanup command: {cmd}"
                    )
                else:
                    LOGD(f"DumpProcessManager: Successfully executed: {cmd}")

            LOGD("DumpProcessManager: Coredump cleanup completed")

        except Exception as e:
            LOGD(f"DumpProcessManager: Error during coredump cleanup: {e}")

    def _on_process_started(self):
        """Process 시작 핸들러"""
        # STARTING 상태가 아닌 경우 무시 (에러 상태에서의 호출 방지)
        if self.state != DumpState.STARTING:
            LOGW(
                f"DumpProcessManager: _on_process_started called in invalid state: {self.state.value}"
            )
            return

        self._set_state(DumpState.EXTRACTING)
        pid = self.dump_process.processId()

        # DUMP_STARTED 이벤트 발생 (triggered_by 정보 포함)
        triggered_by_value = self.triggered_by.value if self.triggered_by else "unknown"
        LOGI(
            f"DumpProcessManager: Emitting DUMP_STARTED event - triggered_by: {triggered_by_value}"
        )
        self.event_manager.emit_event(
            CommonEventType.DUMP_STARTED, {"triggered_by": triggered_by_value}
        )

        # DUMP_STATUS_CHANGED 이벤트 발생 (in_progress)
        self.event_manager.emit_event(
            CommonEventType.DUMP_STATUS_CHANGED,
            {
                "status": "in_progress",
                "dump_id": "",  # 필요시 생성
                "triggered_by": triggered_by_value,
            },
        )

        if self.dump_mode == DumpMode.HEADLESS:
            # Headless 모드: UI 상태 업데이트만, 다이얼로그 없음
            LOGD(f"DumpProcessManager: Headless dump started with PID: {pid}")
            self.event_manager.emit_event(
                CommonEventType.DUMP_PROGRESS,
                {"message": f"Extracting coredump... (PID: {pid})"},
            )

            # Headless 상태 타이머 시작 (1초 간격으로 경과 시간 업데이트)
            self._start_headless_status_timer()

        else:
            # DIALOG 모드: 기존 방식대로 다이얼로그 표시
            LOGD(f"DumpProcessManager: Dialog dump started with PID: {pid}")
            self.event_manager.emit_event(
                CommonEventType.DUMP_PROGRESS,
                {"message": f"Extracting dump... (PID: {pid})"},
            )

            if self.progress_dialog:
                self.progress_dialog.setLabelText(f"Extracting dump... (PID: {pid})")
                self.progress_dialog.setValue(20)

    def _start_headless_status_timer(self):
        """Headless 모드 상태 업데이트 타이머 시작"""
        try:
            if (
                not hasattr(self, "headless_status_timer")
                or self.headless_status_timer is None
            ):
                self.headless_status_timer = QTimer(self)
                if self.headless_status_timer is None:
                    LOGD("DumpProcessManager: Failed to create headless_status_timer")
                    return
                self.headless_status_timer.setInterval(1000)  # 1초 간격
                self.headless_status_timer.timeout.connect(
                    self._on_headless_status_tick
                )

            if self.headless_status_timer is not None:
                self.headless_start_time = QDateTime.currentDateTime()
                self.headless_status_timer.start()
                LOGD("DumpProcessManager: Headless status timer started successfully")
            else:
                LOGD(
                    "DumpProcessManager: headless_status_timer is None, cannot start timer"
                )
        except Exception as e:
            LOGD(f"DumpProcessManager: Error starting headless status timer: {e}")

    def _on_headless_status_tick(self):
        """Headless 모드 상태 업데이트"""
        if self.dump_mode == DumpMode.HEADLESS and self.state == DumpState.EXTRACTING:
            elapsed = self.headless_start_time.secsTo(QDateTime.currentDateTime())
            message = f"Extracting coredump... ({elapsed}s)"
            self.event_manager.emit_event(
                CommonEventType.DUMP_PROGRESS,
                {"message": message},
            )
            # DUMP_PROGRESS_UPDATED 이벤트 발행 (상태바 연동용)
            self.event_manager.emit_event(
                CommonEventType.DUMP_PROGRESS_UPDATED,
                {
                    "progress": 0,
                    "stage": "extracting",
                    "message": message,
                    "dump_id": "",
                },
            )

    def _stop_headless_status_timer(self):
        """Headless 모드 상태 업데이트 타이머 중지"""
        if (
            hasattr(self, "headless_status_timer")
            and self.headless_status_timer
            and self.headless_status_timer.isActive()
        ):
            self.headless_status_timer.stop()

    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        """Process 종료 핸들러"""
        if self.timeout_timer is not None:
            self.timeout_timer.stop()
        self._stop_headless_status_timer()

        # Manual 모드 다이얼로그 닫기 (신호 연결 해제 후 닫기)
        if self.progress_dialog:
            # 취소 시그널 연결 해제하여 닫을 때 취소로 처리되지 않도록 방지
            try:
                self.progress_dialog.canceled.disconnect(self._on_user_cancelled)
            except Exception:
                pass  # 이미 연결이 해제된 경우 무시
            self.progress_dialog.close()
            self.progress_dialog = None

        # 사용자 취소인 경우
        if self.cancellation_requested:
            LOGD("DumpProcessManager: Dump cancelled by user")
            self._set_state(
                DumpState.IDLE
            )  # 취소는 실패가 아니므로 IDLE 상태로 바로 설정
            # DUMP_STATUS_CHANGED 이벤트 먼저 발생
            self.event_manager.emit_event(
                CommonEventType.DUMP_STATUS_CHANGED,
                {
                    "status": "cancelled",
                    "dump_id": "",
                    "triggered_by": (
                        self.triggered_by.value if self.triggered_by else "unknown"
                    ),
                },
            )

            LOGI(
                "DumpProcessManager: Emitting DUMP_ERROR event - error_message: Dump extraction cancelled by user"
            )
            self.event_manager.emit_event(
                CommonEventType.DUMP_ERROR,
                {"error_message": "Dump extraction cancelled by user"},
            )
            return

        LOGD(
            f"DumpProcessManager: Process finished - exit_code: {exit_code}, status: {exit_status}"
        )

        if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            self._set_state(DumpState.VERIFYING)
            self._verify_dump_results()
        else:
            error_msg = f"Process failed with exit_code: {exit_code}"
            self._handle_error(error_msg)

    def _on_process_error(self, error: QProcess.ProcessError):
        """Process 에러 핸들러"""
        if self.timeout_timer is not None:
            self.timeout_timer.stop()
        self._stop_headless_status_timer()

        error_messages = {
            QProcess.ProcessError.FailedToStart: "Failed to start process",
            QProcess.ProcessError.Crashed: "Process crashed",
            QProcess.ProcessError.Timedout: "Process timed out",
            QProcess.ProcessError.WriteError: "Write error",
            QProcess.ProcessError.ReadError: "Read error",
            QProcess.ProcessError.UnknownError: "Unknown error",
        }

        error_msg = error_messages.get(error, f"Unknown error: {error}")
        self._handle_error(error_msg)

    def _on_output_available(self):
        """Process 출력 처리"""
        if self.dump_process:
            output = (
                self.dump_process.readAllStandardOutput()
                .data()
                .decode("utf-8", errors="ignore")
            )
            if output:
                LOGD(f"DumpProcessManager: Process output: {output.strip()}")

    def _verify_dump_results(self):
        """Dump 추출 결과 검증"""
        try:
            # VERIFYING 상태가 아닌 경우 무시 (이미 _on_process_finished에서 상태가 변경되었어야 함)
            if self.state != DumpState.VERIFYING:
                LOGW(
                    f"DumpProcessManager: _verify_dump_results called in invalid state: {self.state.value}"
                )
                return

            if self.dump_mode == DumpMode.HEADLESS:
                self.event_manager.emit_event(
                    CommonEventType.DUMP_PROGRESS,
                    {"message": "Verifying dump results..."},
                )
            else:
                self.event_manager.emit_event(
                    CommonEventType.DUMP_PROGRESS,
                    {"message": "Verifying dump results..."},
                )
                if self.progress_dialog:
                    self.progress_dialog.setLabelText("Verifying dump results...")
                    self.progress_dialog.setValue(90)

            # 작업 디렉토리 유효성 검사
            if self.working_dir is None:
                raise AttributeError("working_dir is None")

            if not self.working_dir.exists():
                raise FileNotFoundError(
                    f"Working directory does not exist: {self.working_dir}"
                )

            # 1. zip 파일 존재 확인
            zip_files = list(self.working_dir.glob("*.zip"))
            if not zip_files:
                raise FileNotFoundError("No zip files found")

            # 2. zip 파일 유효성 확인
            valid_zips = []
            for zip_file in zip_files:
                if zip_file.exists() and zip_file.stat().st_size > 0:
                    valid_zips.append(zip_file)

            if not valid_zips:
                raise FileNotFoundError("No valid zip files found")

            # 3. 필수 항목 확인
            required_items = ["sw_version.txt", "coredump"]
            for item in required_items:
                item_path = self.working_dir / item
                if not item_path.exists():
                    LOGD(
                        f"DumpProcessManager: Warning - Required item not found: {item}"
                    )

            # 4. 성공 처리
            self._set_state(DumpState.COMPLETED)
            success_msg = (
                f"Dump completed successfully - {len(valid_zips)} zip files created"
            )
            LOGD(f"DumpProcessManager: {success_msg}")

            # Headless 모드에서는 추가 로깅
            if self.dump_mode == DumpMode.HEADLESS:
                LOGD(
                    f"DumpProcessManager: Headless dump completed - will trigger auto reboot"
                )

            # DIALOG 모드인 경우 성공 다이얼로그 표시
            if self.dump_mode == DumpMode.DIALOG:
                DumpCompletionDialog.show_completion_dialog(
                    self.parent_widget, True, success_msg, self.working_dir
                )

            # DUMP_STATUS_CHANGED 이벤트 먼저 발생 (UI 상태 업데이트 우선)
            self.event_manager.emit_event(
                CommonEventType.DUMP_STATUS_CHANGED,
                {
                    "status": "completed",
                    "dump_id": "",
                    "triggered_by": (
                        self.triggered_by.value if self.triggered_by else "unknown"
                    ),
                },
            )

            # DUMP_COMPLETED 이벤트 발생 (triggered_by, upload_enabled, dump_path 정보 포함)
            triggered_by_val = self.triggered_by.value if self.triggered_by else None
            LOGI(
                f"DumpProcessManager: Emitting DUMP_COMPLETED event - "
                f"triggered_by: {triggered_by_val}, success: True, "
                f"upload_enabled: {self.upload_enabled}"
            )
            self.event_manager.emit_event(
                CommonEventType.DUMP_COMPLETED,
                {
                    "triggered_by": (
                        self.triggered_by.value if self.triggered_by else None
                    ),
                    "success": True,
                    "upload_enabled": self.upload_enabled,
                    "dump_path": str(self.working_dir) if self.working_dir else None,
                },
            )

            # 성공 완료 후에도 상태를 IDLE로 복귀시켜 다음 dump 실행 및 외부 가드 조건들이
            # COMPLETED 상태에 의해 영구히 막히지 않도록 한다.
            try:
                QTimer.singleShot(0, self._reset_state)
            except Exception:
                # singleShot 사용 불가 환경에서도 즉시 복구
                self._reset_state()

        except Exception as e:
            error_msg = f"Result verification failed: {e}"
            self._handle_error(error_msg)

    def _on_timeout(self):
        """타임아웃 핸들러"""
        LOGD("DumpProcessManager: Dump extraction timed out")

        if (
            self.dump_process
            and self.dump_process.state() == QProcess.ProcessState.Running
        ):
            self.dump_process.kill()
            LOGD("DumpProcessManager: Dump process killed due to timeout")

        self._handle_error("Dump extraction timed out")

    def _handle_error(self, error_msg: str):
        """에러 처리 및 상태 복구"""
        LOGD(f"DumpProcessManager: Error - {error_msg}")

        # 상태 설정
        if self.timeout_timer is not None and self.timeout_timer.isActive():
            self._set_state(DumpState.TIMEOUT)
        else:
            self._set_state(DumpState.FAILED)

        # Manual 모드 다이얼로그 닫기
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # Process 정리
        if (
            self.dump_process
            and self.dump_process.state() == QProcess.ProcessState.Running
        ):
            self.dump_process.kill()

        self._stop_headless_status_timer()

        # Headless 모드에서는 상세한 에러 로깅
        if self.dump_mode == DumpMode.HEADLESS:
            LOGD(f"DumpProcessManager: Headless dump error details:")
            LOGD(f"  - Error message: {error_msg}")
            LOGD(
                f"  - Process state: {self.dump_process.state() if self.dump_process else 'None'}"
            )
            LOGD(
                f"  - Exit code: {self.dump_process.exitCode() if self.dump_process else 'N/A'}"
            )
            LOGD(f"  - Working directory: {self.working_dir}")

        # DUMP_STATUS_CHANGED 이벤트 먼저 발생
        self.event_manager.emit_event(
            CommonEventType.DUMP_STATUS_CHANGED,
            {
                "status": "failed",
                "dump_id": "",
                "triggered_by": (
                    self.triggered_by.value if self.triggered_by else "unknown"
                ),
                "error_message": error_msg,
            },
        )

        # 에러 시그널 발신
        LOGI(
            f"DumpProcessManager: Emitting DUMP_ERROR event - error_message: {error_msg}"
        )
        self.event_manager.emit_event(
            CommonEventType.DUMP_ERROR, {"error_message": error_msg}
        )

        # DIALOG 모드인 경우 에러 다이얼로그 표시
        if self.dump_mode == DumpMode.DIALOG:
            DumpCompletionDialog.show_completion_dialog(
                self.parent_widget, False, error_msg, self.working_dir
            )

        # 상태 복구 (headless 모드에서는 더 빠른 복구)
        reset_delay = 1000 if self.dump_mode == DumpMode.HEADLESS else 3000
        QTimer.singleShot(reset_delay, self._reset_state)

    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        if self.event_manager:
            self.event_manager.register_event_handler(
                CommonEventType.DUMP_REQUESTED, self._on_dump_requested
            )
            LOGD("DumpProcessManager: Registered DUMP_REQUESTED event handler")

    def _on_dump_requested(self, args: Dict[str, Any]) -> None:
        """DUMP_REQUESTED 이벤트 핸들러"""
        try:
            triggered_by_str = args.get("triggered_by")

            # 문자열을 enum으로 변환
            triggered_by = DumpTriggeredBy(triggered_by_str)

            # Dump 모드 설정 (전달된 경우)
            dump_mode_str = args.get("dump_mode")
            if dump_mode_str:
                try:
                    self.set_dump_mode(DumpMode(dump_mode_str))
                except ValueError:
                    LOGW(f"DumpProcessManager: Unknown dump mode: {dump_mode_str}")

            # 업로드 활성화 여부 설정 (전달된 경우)
            if "upload_enabled" in args:
                self.set_upload_enabled(bool(args.get("upload_enabled")))

            # 전역 이슈 디렉토리 지정이 있으면 작업 디렉토리 override
            issue_dir_str = args.get("issue_dir")
            if issue_dir_str:
                try:
                    self._override_working_dir = Path(issue_dir_str)
                    ensure_directory_exists(self._override_working_dir)
                    # 캡처 중 로그 파일을 이슈 디렉토리로 복사 (best-effort)
                    self._copy_capturing_logs_to_issue_dir(self._override_working_dir)
                except Exception as e:
                    LOGD(
                        f"DumpProcessManager: Failed to prepare issue_dir '{issue_dir_str}': {e}"
                    )

            LOGI(
                f"DumpProcessManager: Dump requested - triggered_by: {triggered_by.value}"
            )

            # dump 추출 시작
            self.start_dump_extraction(triggered_by)

        except Exception as e:
            LOGD(f"DumpProcessManager: Error handling dump requested event: {e}")

    def _copy_capturing_logs_to_issue_dir(self, issue_dir: Path) -> None:
        """디바이스에서 캡처 중인 로그 파일을 이슈 디렉토리로 복사 (best-effort)"""
        try:
            if self.logging_manager is None:
                return

            log_dir = getattr(self.logging_manager, "log_directory", None)
            # 가능한 메서드 이름들 호환
            filename: Optional[str] = None
            if hasattr(self.logging_manager, "get_current_log_filename"):
                filename = self.logging_manager.get_current_log_filename()  # type: ignore[attr-defined]
            elif hasattr(self.logging_manager, "get_current_log_file_name"):
                filename = self.logging_manager.get_current_log_file_name()  # type: ignore[attr-defined]

            if not log_dir or not filename:
                return

            src = Path(log_dir) / filename
            if not src.exists() or not src.is_file():
                return

            dest_dir = issue_dir / "logs"
            ensure_directory_exists(dest_dir)
            dest = dest_dir / src.name

            # 파일이 클 수 있으므로 스트림 복사
            with src.open("rb") as rf, dest.open("wb") as wf:
                while True:
                    chunk = rf.read(1024 * 1024)
                    if not chunk:
                        break
                    wf.write(chunk)

            LOGD(f"DumpProcessManager: Copied current log file to issue dir: {dest}")

        except Exception as e:
            LOGD(f"DumpProcessManager: Best-effort log copy failed: {e}")

    def _reset_state(self):
        """상태 초기화"""
        self._set_state(DumpState.IDLE)
        self.dump_process = None
        self.working_dir = None
        self._override_working_dir = None
        self.cancellation_requested = False
        LOGD("DumpProcessManager: State reset to IDLE")

    def cleanup(self):
        """리소스 정리"""
        LOGD("DumpProcessManager: Starting cleanup")

        # 프로세스 정리
        if (
            self.dump_process
            and self.dump_process.state() == QProcess.ProcessState.Running
        ):
            self.dump_process.kill()

        # 타이머 정리
        if self.timeout_timer is not None and self.timeout_timer.isActive():
            self.timeout_timer.stop()

        self._stop_headless_status_timer()

        # 다이얼로그 정리
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # 상태 초기화
        self._reset_state()

        LOGD("DumpProcessManager: Cleanup completed")
