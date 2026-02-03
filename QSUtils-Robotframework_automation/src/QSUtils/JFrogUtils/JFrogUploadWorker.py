#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrog 업로드 Worker

백그라운드에서 JFrog 업로드를 처리하는 QThread 기반 Worker 클래스입니다.
"""

import time
from pathlib import Path
from typing import List, Tuple, Dict, Any

from PySide6.QtCore import QThread, Signal

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.JFrogUploader import JFrogUploader
from QSUtils.Utils.Logger import get_logger


class JFrogUploadWorker(QThread):
    """JFrog 업로드 백그라운드 Worker"""

    # 시그널 정의
    progress_updated = Signal(dict)  # 진행 상태 업데이트
    file_completed = Signal(str, dict)  # 파일 업로드 완료
    upload_completed = Signal(bool, str, dict)  # 전체 업로드 완료
    error_occurred = Signal(str)  # 에러 발생

    def __init__(self, config: JFrogConfig, parent=None):
        """
        JFrogUploadWorker 초기화

        Args:
            config: JFrog 설정 객체
            parent: 부모 QObject
        """
        super().__init__(parent)
        self.config = config
        self.logger = get_logger()
        self.uploader = JFrogUploader(config)

        # 업로드 작업 관리
        self.files_to_upload: List[Tuple[str, str]] = (
            []
        )  # [(local_path, target_path), ...]
        self.upload_id: str = ""
        self.repo: str = ""
        self._cancelled = False
        self._paused = False

        # 진행 상태 추적
        self.total_files = 0
        self.completed_files = 0
        self.total_bytes = 0
        self.uploaded_bytes = 0
        self.start_time = 0.0
        self.current_file = ""
        self.current_file_size = 0
        self.current_file_uploaded = 0

        self.logger.info(f"JFrogUploadWorker 초기화 완료")

    def setup_upload(
        self, files: List[Tuple[str, str]], repo: str = None, upload_id: str = None
    ):
        """
        업로드 작업 설정

        Args:
            files: 업로드할 파일 리스트 [(local_path, target_path), ...]
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
            upload_id: 업로드 ID
        """
        self.files_to_upload = files
        self.repo = repo or self.config.default_repo

        if not upload_id:
            upload_id = f"upload_{int(time.time())}_{hash(str(files))}"
        self.upload_id = upload_id

        # 전체 파일 정보 계산
        self.total_files = len(files)
        self.total_bytes = 0
        for local_path, _ in files:
            if Path(local_path).exists():
                self.total_bytes += Path(local_path).stat().st_size

        # 상태 초기화
        self.completed_files = 0
        self.uploaded_bytes = 0
        self.current_file = ""
        self._cancelled = False
        self._paused = False

        self.logger.info(
            f"업로드 작업 설정: {len(files)}개 파일, {self.total_bytes} bytes"
        )

    def setup_directory_upload(
        self,
        local_path: str,
        target_path: str = None,
        repo: str = None,
        upload_id: str = None,
    ):
        """
        디렉토리 업로드 작업 설정

        Args:
            local_path: 업로드할 로컬 디렉토리 경로
            target_path: 타겟 경로
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
            upload_id: 업로드 ID
        """
        try:
            local_dir = Path(local_path)
            if not local_dir.exists() or not local_dir.is_dir():
                raise ValueError(f"디렉토리를 찾을 수 없습니다: {local_path}")

            # 모든 파일 수집
            all_files = list(local_dir.rglob("*"))
            files_to_upload = [f for f in all_files if f.is_file()]

            if not files_to_upload:
                self.logger.warning(f"업로드할 파일이 없습니다: {local_path}")
                self.files_to_upload = []
                return

            # 파일 리스트 생성
            target_path = target_path or local_dir.name
            file_list = []

            for file_path in files_to_upload:
                relative_path = file_path.relative_to(local_dir)
                target_file_path = f"{target_path}/{relative_path}"
                file_list.append((str(file_path), target_file_path))

            self.setup_upload(file_list, repo, upload_id)

        except Exception as e:
            self.logger.error(f"디렉토리 업로드 설정 실패: {local_path}, 오류: {e}")
            self.error_occurred.emit(f"디렅토리 업로드 설정 실패: {str(e)}")

    def run(self):
        """백그라운드 업로드 실행"""
        try:
            if not self.files_to_upload:
                self.logger.warning("업로드할 파일이 없습니다")
                self.upload_completed.emit(True, "업로드할 파일이 없습니다", {})
                return

            self.start_time = time.time()
            self.logger.info(
                f"백그라운드 업로드 시작: {len(self.files_to_upload)}개 파일"
            )

            uploaded_files = []
            failed_files = []

            for i, (local_path, target_path) in enumerate(self.files_to_upload):
                if self._cancelled:
                    self.logger.info("업로드가 취소되었습니다")
                    break

                # 일시정지 상태 대기
                while self._paused and not self._cancelled:
                    self.msleep(100)

                if self._cancelled:
                    break

                self.current_file = local_path
                self.current_file_size = Path(local_path).stat().st_size
                self.current_file_uploaded = 0

                # 진행 상태 업데이트
                self._emit_progress()

                try:
                    # 파일 업로드
                    result = self.uploader.upload_file(
                        local_path, target_path, self.repo, f"{self.upload_id}_file_{i}"
                    )

                    if result.success:
                        uploaded_files.extend(result.uploaded_files)
                        self.uploaded_bytes += self.current_file_size
                        self.completed_files += 1
                        self.current_file_uploaded = (
                            self.current_file_size
                        )  # 파일 완료 표시

                        # 파일 완료 시그널 발송
                        self.file_completed.emit(
                            local_path,
                            result.uploaded_files[0] if result.uploaded_files else {},
                        )

                        self.logger.debug(f"파일 업로드 완료: {local_path}")
                    else:
                        failed_files.extend(result.failed_files)
                        self.logger.error(
                            f"파일 업로드 실패: {local_path}, 오류: {result.failed_files[0].get('error', '알 수 없는 오류') if result.failed_files else '알 수 없는 오류'}"
                        )

                except Exception as e:
                    self.logger.error(f"파일 업로드 중 예외: {local_path}, 오류: {e}")
                    failed_files.append(
                        {
                            "local_path": local_path,
                            "target_path": target_path,
                            "error": str(e),
                        }
                    )

            # 최종 진행 상태 업데이트
            self._emit_progress()

            # 결과 계산
            upload_time = time.time() - self.start_time
            success = len(failed_files) == 0 and not self._cancelled

            result_data = {
                "uploaded_files": uploaded_files,
                "failed_files": failed_files,
                "total_uploaded": len(uploaded_files),
                "total_failed": len(failed_files),
                "total_size": self.uploaded_bytes,
                "upload_time": upload_time,
                "cancelled": self._cancelled,
            }

            if self._cancelled:
                message = f"업로드가 취소되었습니다 ({len(uploaded_files)}개 파일 완료)"
            elif success:
                message = f"업로드 완료: {len(uploaded_files)}개 파일"
            else:
                message = f"업로드 부분 완료: {len(uploaded_files)}개 성공, {len(failed_files)}개 실패"

            self.logger.info(f"백그라운드 업로드 완료: {message}")
            self.upload_completed.emit(success, message, result_data)

        except Exception as e:
            self.logger.error(f"백그라운드 업로드 중 예외 발생: {e}")
            self.error_occurred.emit(f"업로드 중 오류 발생: {str(e)}")

    def cancel_upload(self):
        """업로드 취소"""
        self._cancelled = True
        self.logger.info(f"업로드 취소 요청: {self.upload_id}")

    def pause_upload(self):
        """업로드 일시정지"""
        self._paused = True
        self.logger.info(f"업로드 일시정지: {self.upload_id}")

    def resume_upload(self):
        """업로드 재개"""
        self._paused = False
        self.logger.info(f"업로드 재개: {self.upload_id}")

    def is_cancelled(self) -> bool:
        """취소되었는지 확인"""
        return self._cancelled

    def is_paused(self) -> bool:
        """일시정지되었는지 확인"""
        return self._paused

    def get_current_progress(self) -> Dict[str, Any]:
        """현재 진행 상태 정보 가져오기"""
        elapsed_time = time.time() - self.start_time if self.start_time > 0 else 0
        speed_bps = self.uploaded_bytes / elapsed_time if elapsed_time > 0 else 0.0
        remaining_bytes = self.total_bytes - self.uploaded_bytes
        eta_seconds = remaining_bytes / speed_bps if speed_bps > 0 else 0.0

        return {
            "upload_id": self.upload_id,
            "total_files": self.total_files,
            "completed_files": self.completed_files,
            "total_bytes": self.total_bytes,
            "uploaded_bytes": self.uploaded_bytes,
            "current_file": self.current_file,
            "speed_bps": speed_bps,
            "eta_seconds": eta_seconds,
            "progress_percentage": (
                (self.completed_files / self.total_files * 100)
                if self.total_files > 0
                else 0.0
            ),
            "file_progress_percentage": (
                (self.current_file_uploaded / self.current_file_size * 100)
                if self.current_file_size > 0
                else 0.0
            ),
            "elapsed_time": elapsed_time,
            "cancelled": self._cancelled,
            "paused": self._paused,
        }

    def _emit_progress(self):
        """진행 상태 시그널 발송"""
        progress_data = self.get_current_progress()
        self.progress_updated.emit(progress_data)


class JFrogChunkedUploadWorker(JFrogUploadWorker):
    """JFrog 청크 업로드 백그라운드 Worker"""

    def __init__(self, config: JFrogConfig, parent=None):
        super().__init__(config, parent)
        self.chunk_size = 10 * 1024 * 1024  # 기본 10MB
        self.large_file_threshold = 100 * 1024 * 1024  # 100MB 이상이면 청크 업로드

    def set_chunk_size(self, chunk_size: int):
        """
        청크 크기 설정

        Args:
            chunk_size: 청크 크기 (바이트)
        """
        self.chunk_size = chunk_size
        self.logger.info(f"청크 크기 설정: {chunk_size} bytes")

    def set_large_file_threshold(self, threshold: int):
        """
        대형 파일 임계값 설정

        Args:
            threshold: 임계값 (바이트)
        """
        self.large_file_threshold = threshold
        self.logger.info(f"대형 파일 임계값 설정: {threshold} bytes")

    def run(self):
        """청크 업로드 실행"""
        try:
            if not self.files_to_upload:
                self.logger.warning("업로드할 파일이 없습니다")
                self.upload_completed.emit(True, "업로드할 파일이 없습니다", {})
                return

            self.start_time = time.time()
            self.logger.info(
                f"청크 백그라운드 업로드 시작: {len(self.files_to_upload)}개 파일"
            )

            uploaded_files = []
            failed_files = []

            for i, (local_path, target_path) in enumerate(self.files_to_upload):
                if self._cancelled:
                    self.logger.info("업로드가 취소되었습니다")
                    break

                # 일시정지 상태 대기
                while self._paused and not self._cancelled:
                    self.msleep(100)

                if self._cancelled:
                    break

                self.current_file = local_path

                # 진행 상태 업데이트
                self._emit_progress()

                try:
                    file_path = Path(local_path)
                    file_size = file_path.stat().st_size if file_path.exists() else 0

                    # 대형 파일이면 청크 업로드 사용
                    if file_size > self.large_file_threshold:
                        self.logger.info(
                            f"대형 파일 청크 업로드: {local_path} ({file_size} bytes)"
                        )
                        result = self.uploader.upload_file_chunked(
                            local_path, target_path, self.repo, self.chunk_size
                        )
                    else:
                        # 일반 업로드
                        result = self.uploader.upload_file(
                            local_path,
                            target_path,
                            self.repo,
                            f"{self.upload_id}_file_{i}",
                        )

                    if result.success:
                        uploaded_files.extend(result.uploaded_files)
                        self.uploaded_bytes += file_size
                        self.completed_files += 1

                        # 파일 완료 시그널 발송
                        file_info = (
                            result.uploaded_files[0] if result.uploaded_files else {}
                        )
                        file_info["chunked"] = file_size > self.large_file_threshold
                        self.file_completed.emit(local_path, file_info)

                        self.logger.debug(
                            f"파일 업로드 완료: {local_path} (청크: {file_size > self.large_file_threshold})"
                        )
                    else:
                        failed_files.extend(result.failed_files)
                        self.logger.error(
                            f"파일 업로드 실패: {local_path}, 오류: {result.failed_files[0].get('error', '알 수 없는 오류') if result.failed_files else '알 수 없는 오류'}"
                        )

                except Exception as e:
                    self.logger.error(f"파일 업로드 중 예외: {local_path}, 오류: {e}")
                    failed_files.append(
                        {
                            "local_path": local_path,
                            "target_path": target_path,
                            "error": str(e),
                        }
                    )

            # 최종 진행 상태 업데이트
            self._emit_progress()

            # 결과 계산
            upload_time = time.time() - self.start_time
            success = len(failed_files) == 0 and not self._cancelled

            result_data = {
                "uploaded_files": uploaded_files,
                "failed_files": failed_files,
                "total_uploaded": len(uploaded_files),
                "total_failed": len(failed_files),
                "total_size": self.uploaded_bytes,
                "upload_time": upload_time,
                "cancelled": self._cancelled,
                "chunked_upload": True,
            }

            if self._cancelled:
                message = (
                    f"청크 업로드가 취소되었습니다 ({len(uploaded_files)}개 파일 완료)"
                )
            elif success:
                message = f"청크 업로드 완료: {len(uploaded_files)}개 파일"
            else:
                message = f"청크 업로드 부분 완료: {len(uploaded_files)}개 성공, {len(failed_files)}개 실패"

            self.logger.info(f"청크 백그라운드 업로드 완료: {message}")
            self.upload_completed.emit(success, message, result_data)

        except Exception as e:
            self.logger.error(f"청크 백그라운드 업로드 중 예외 발생: {e}")
            self.error_occurred.emit(f"청크 업로드 중 오류 발생: {str(e)}")
