#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process Manager
프로세스 생명주기 관리를 전담하는 클래스
"""

from pathlib import Path
from shutil import which
from typing import Optional

from PySide6.QtCore import QProcess

from QSUtils.Utils.Logger import LOGI, LOGE, LOGD
from QSUtils.command.command_constants import TimeoutConstants


class ProcessManager:
    """
    QProcess의 생명주기 관리를 담당하는 클래스
    """

    def __init__(self):
        """
        ProcessManager 초기화
        """
        self.process = QProcess()
        self._is_intentionally_stopping = False
        self._is_device_connected = True  # 디바이스 연결 상태 추적
        self._is_destroyed = False  # 객체 소멸 상태 추적

        # QProcess 시그널 연결은 사용하는 쪽에서 담당
        # self.process.started.connect(self._on_started)
        # self.process.finished.connect(self._on_finished)
        # self.process.errorOccurred.connect(self._on_error)
        # self.process.readyRead.connect(self._on_ready_read)

    def __del__(self):
        """소멸자에서 프로세스 안전하게 종료"""
        try:
            self._is_destroyed = True
            if self.process and self.is_running():
                LOGD("ProcessManager: Force stopping process in destructor")
                self.process.terminate()
                if not self.process.waitForFinished(1000):  # 1초 대기
                    self.process.kill()
        except Exception as e:
            LOGE(f"Exception in ProcessManager destructor: {str(e)}")

    def start_process(
        self, device_serial: str, command: str, args: list = None
    ) -> bool:
        """
        프로세스 시작

        Args:
            device_serial: 디바이스 시리얼 번호
            command: 실행할 명령어
            args: 명령어 인자 리스트

        Returns:
            bool: 성공 여부
        """
        # 디바이스 연결 상태 확인
        if not self._is_device_connected:
            LOGE("Cannot start process: Device not connected")
            return False

        if self.is_running():
            LOGE("Process already running")
            return False

        try:
            # ADB 경로 확인
            adb_path = self._resolve_adb_path()
            if not adb_path:
                return False

            # 프로세스 채널 모드 설정
            self.process.setProcessChannelMode(QProcess.MergedChannels)

            # 명령어 인자 준비
            full_args = ["-s", device_serial, "shell"]
            if args:
                full_args.extend(args)
            else:
                full_args.extend(command.split())

            LOGD(f"Starting process: {adb_path} {' '.join(full_args)}")

            # 프로세스 시작
            self.process.start(adb_path, full_args)

            # 시작 대기
            if self.process.waitForStarted(TimeoutConstants.PROCESS_START_TIMEOUT):
                LOGD("Process started successfully")
                return True
            else:
                LOGE("Failed to start process")
                return False

        except Exception as e:
            LOGE(f"Exception starting process: {str(e)}")
            return False

    def stop_process(self) -> None:
        """
        프로세스 정지
        """
        # 객체가 이미 소멸되었으면 아무 작업도 하지 않음
        if self._is_destroyed:
            return

        if not self.process or not self.is_running():
            return

        LOGD("Stopping process")

        try:
            # 의도적 종료 표시
            self._is_intentionally_stopping = True

            # 정상 종료 시도
            self.process.terminate()

            # 종료 대기
            if self.process.waitForFinished(TimeoutConstants.PROCESS_TERMINATE_TIMEOUT):
                LOGI("Process terminated gracefully")
            else:
                # 강제 종료
                LOGI("Force killing process")
                self.process.kill()
                self.process.waitForFinished(TimeoutConstants.PROCESS_KILL_TIMEOUT)

        except Exception as e:
            LOGE(f"Exception stopping process: {str(e)}")
        finally:
            self._is_intentionally_stopping = False
            # 프로세스 정지 후 디바이스 연결 상태 초기화
            self._is_device_connected = True

    def is_running(self) -> bool:
        """
        프로세스 실행 상태 확인

        Returns:
            bool: 실행 중 여부
        """
        return self.process.state() == QProcess.Running

    def read_all_data(self) -> bytes:
        """
        사용 가능한 모든 데이터 읽기

        Returns:
            bytes: 읽은 데이터
        """
        return self.process.readAll()

    def get_process_state(self) -> QProcess.ProcessState:
        """
        프로세스 상태 반환

        Returns:
            QProcess.ProcessState: 프로세스 상태
        """
        return self.process.state()

    def is_intentionally_stopping(self) -> bool:
        """
        의도적 종료 여부 확인

        Returns:
            bool: 의도적 종료 여부
        """
        return self._is_intentionally_stopping

    def set_intentionally_stopping(self, stopping: bool) -> None:
        """
        의도적 종료 플래그 설정

        Args:
            stopping: 의도적 종료 여부
        """
        self._is_intentionally_stopping = stopping

    def _resolve_adb_path(self) -> Optional[str]:
        """
        ADB 실행 파일 경로 확인

        Returns:
            Optional[str]: ADB 경로 또는 None
        """
        # PATH에서 ADB 경로 확인
        adb_path = which("adb") or "/usr/bin/adb"
        if Path(adb_path).exists():
            return adb_path

        # 대체 경로 확인
        alt_path = "/usr/local/bin/adb"
        if Path(alt_path).exists():
            return alt_path

        LOGE("ADB binary not found. Tried PATH, /usr/bin/adb, /usr/local/bin/adb")
        return None

    def _on_started(self) -> None:
        """프로세스 시작 시그널 핸들러"""
        LOGI("Process started signal received")

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """
        프로세스 종료 시그널 핸들러

        Args:
            exit_code: 종료 코드
            exit_status: 종료 상태
        """
        LOGI(f"Process finished, exit code: {exit_code}, exit status: {exit_status}")

        # 의도적 종료가 아니고 비정상 종료인 경우에만 로깅
        if not self._is_intentionally_stopping and (
            exit_code != 0 or exit_status == QProcess.CrashExit
        ):
            error_msg = f"Process exited abnormally. "
            if exit_status == QProcess.CrashExit:
                error_msg += "Process crashed. "
            error_msg += f"Exit code: {exit_code}"
            LOGE(error_msg)

    def _on_error(self, error: QProcess.ProcessError) -> None:
        """
        프로세스 에러 시그널 핸들러

        Args:
            error: 에러 타입
        """
        # 의도적 종료 중이면 무시
        if self._is_intentionally_stopping:
            LOGI("Process error ignored due to intentional stop")
            return

        error_msg = f"Process error: {self.process.errorString()}"
        LOGE(error_msg)

        # 프로세스가 이미 종료된 상태에서 접근하려는 에러 처리
        if error == QProcess.ProcessError.Crashed:
            LOGE("Process crashed unexpectedly")
            # 디바이스 연결 상태 업데이트
            self._is_device_connected = False

    def _on_ready_read(self) -> None:
        """데이터 읽기 가능 시그널 핸들러"""
        # 실제 데이터 처리는 상위 클래스에서 구현
        pass
