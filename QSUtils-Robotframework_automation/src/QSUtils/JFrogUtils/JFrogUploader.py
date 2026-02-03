#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JFrog 업로더

JFrog Artifactory에 파일과 디렉토리를 업로드하는 기능을 제공합니다.
"""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

from QSUtils.JFrogUtils.JFrogConfig import JFrogConfig
from QSUtils.JFrogUtils.exceptions import (
    JFrogUploadError,
    JFrogConfigurationError,
)
from QSUtils.Utils.Logger import get_logger


@dataclass
class UploadProgress:
    """업로드 진행 상태 정보"""

    upload_id: str
    total_files: int
    completed_files: int
    total_bytes: int
    uploaded_bytes: int
    current_file: str
    speed_bps: float
    eta_seconds: float

    @property
    def progress_percentage(self) -> float:
        """전체 진행률 (퍼센트)"""
        if self.total_bytes == 0:
            return 0.0
        return (self.uploaded_bytes / self.total_bytes) * 100

    @property
    def file_progress_percentage(self) -> float:
        """현재 파일 진행률 (퍼센트)"""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100


@dataclass
class UploadResult:
    """업로드 결과 정보"""

    success: bool
    uploaded_files: List[Dict[str, Any]]
    failed_files: List[Dict[str, Any]]
    total_uploaded: int
    total_failed: int
    total_size: int
    upload_time: float

    def __post_init__(self):
        if not self.uploaded_files:
            self.uploaded_files = []
        if not self.failed_files:
            self.failed_files = []


class JFrogUploader:
    """JFrog Artifactory 업로더 클래스"""

    def __init__(self, config: JFrogConfig):
        """
        JFrogUploader 초기화

        Args:
            config: JFrog 설정 객체
        """
        self.config = config
        self.logger = get_logger()
        self.active_uploads: Dict[str, UploadProgress] = {}

        # 설정 유효성 검증
        if not config.is_valid():
            errors = config.validate()
            raise JFrogConfigurationError(f"설정 오류: {'; '.join(errors)}")

        self.logger.info(f"JFrogUploader 초기화 완료: {config.server_url}")

    def upload_file(
        self,
        local_path: str,
        target_path: str = None,
        repo: str = None,
        upload_id: str = None,
        progress_callback=None,
    ) -> UploadResult:
        """
        단일 파일 업로드

        Args:
            local_path: 업로드할 로컬 파일 경로
            target_path: 타겟 경로 (없으면 파일명 사용)
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
            upload_id: 업로드 ID (진행 상태 추적용)

        Returns:
            UploadResult: 업로드 결과
        """
        start_time = time.time()

        try:
            # 파일 존재 확인
            local_file = Path(local_path)
            if not local_file.exists():
                raise JFrogUploadError(f"파일을 찾을 수 없습니다: {local_path}")

            if not local_file.is_file():
                raise JFrogUploadError(f"파일이 아닙니다: {local_path}")

            # 타겟 경로 설정
            if not target_path:
                target_path = local_file.name

            # 리포지토리 설정
            target_repo = repo or self.config.default_repo
            upload_target = f"{target_repo}/{target_path.lstrip('/')}"

            # 업로드 ID 생성
            if not upload_id:
                upload_id = f"file_{int(time.time())}_{hash(local_path)}"

            # 진행 상태 초기화
            file_size = local_file.stat().st_size
            progress = UploadProgress(
                upload_id=upload_id,
                total_files=1,
                completed_files=0,
                total_bytes=file_size,
                uploaded_bytes=0,
                current_file=str(local_file),
                speed_bps=0.0,
                eta_seconds=0.0,
            )
            self.active_uploads[upload_id] = progress

            self.logger.info(f"파일 업로드 시작: {local_path} -> {upload_target}")

            # jf-cli 업로드 명령어 실행
            cmd = ["jf", "rt", "upload", "--flat=true", str(local_file), upload_target]

            result = self._execute_jf_command(cmd, timeout=self.config.upload_timeout)

            upload_time = time.time() - start_time

            if result.returncode == 0:
                # 업로드 성공
                uploaded_file = {
                    "local_path": str(local_file),
                    "target_path": target_path,
                    "upload_target": upload_target,
                    "url": f"{self.config.artifactory_url}/{upload_target}",
                    "size": file_size,
                    "upload_time": upload_time,
                }

                # 진행 상태 업데이트
                progress.completed_files = 1
                progress.uploaded_bytes = file_size
                progress.speed_bps = file_size / upload_time if upload_time > 0 else 0.0

                self.logger.info(f"파일 업로드 성공: {upload_target}")

                return UploadResult(
                    success=True,
                    uploaded_files=[uploaded_file],
                    failed_files=[],
                    total_uploaded=1,
                    total_failed=0,
                    total_size=file_size,
                    upload_time=upload_time,
                )
            else:
                # 업로드 실패
                error_msg = (
                    result.stderr.strip() if result.stderr else "알 수 없는 오류"
                )
                failed_file = {
                    "local_path": str(local_file),
                    "target_path": target_path,
                    "error": error_msg,
                }

                self.logger.error(f"파일 업로드 실패: {local_path}, 오류: {error_msg}")

                return UploadResult(
                    success=False,
                    uploaded_files=[],
                    failed_files=[failed_file],
                    total_uploaded=0,
                    total_failed=1,
                    total_size=0,
                    upload_time=upload_time,
                )

        except Exception as e:
            upload_time = time.time() - start_time
            self.logger.error(f"파일 업로드 중 예외 발생: {local_path}, 오류: {e}")

            failed_file = {
                "local_path": local_path,
                "target_path": target_path,
                "error": str(e),
            }

            return UploadResult(
                success=False,
                uploaded_files=[],
                failed_files=[failed_file],
                total_uploaded=0,
                total_failed=1,
                total_size=0,
                upload_time=upload_time,
            )
        finally:
            # 진행 상태 정리
            if upload_id in self.active_uploads:
                del self.active_uploads[upload_id]

    def upload_directory(
        self,
        local_path: str,
        target_path: str = None,
        repo: str = None,
        upload_id: str = None,
    ) -> UploadResult:
        """
        디렉토리 업로드 (재귀적)

        Args:
            local_path: 업로드할 로컬 디렉토리 경로
            target_path: 타겟 경로 (없으면 디렉토리명 사용)
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
            upload_id: 업로드 ID (진행 상태 추적용)

        Returns:
            UploadResult: 업로드 결과
        """
        start_time = time.time()

        try:
            # 디렉토리 존재 확인
            local_dir = Path(local_path)
            if not local_dir.exists():
                raise JFrogUploadError(f"디렉토리를 찾을 수 없습니다: {local_path}")

            if not local_dir.is_dir():
                raise JFrogUploadError(f"디렉토리가 아닙니다: {local_path}")

            # 타겟 경로 설정
            if not target_path:
                target_path = local_dir.name

            # 리포지토리 설정
            target_repo = repo or self.config.default_repo
            upload_target = f"{target_repo}/{target_path.lstrip('/')}/"

            # 업로드 ID 생성
            if not upload_id:
                upload_id = f"dir_{int(time.time())}_{hash(local_path)}"

            # 모든 파일 수집
            all_files = list(local_dir.rglob("*"))
            files_to_upload = [f for f in all_files if f.is_file()]

            if not files_to_upload:
                self.logger.warning(f"업로드할 파일이 없습니다: {local_path}")
                return UploadResult(
                    success=True,
                    uploaded_files=[],
                    failed_files=[],
                    total_uploaded=0,
                    total_failed=0,
                    total_size=0,
                    upload_time=time.time() - start_time,
                )

            # 전체 크기 계산
            total_size = sum(f.stat().st_size for f in files_to_upload)

            # 진행 상태 초기화
            progress = UploadProgress(
                upload_id=upload_id,
                total_files=len(files_to_upload),
                completed_files=0,
                total_bytes=total_size,
                uploaded_bytes=0,
                current_file="",
                speed_bps=0.0,
                eta_seconds=0.0,
            )
            self.active_uploads[upload_id] = progress

            self.logger.info(f"디렉토리 업로드 시작: {local_path} -> {upload_target}")
            self.logger.info(f"총 {len(files_to_upload)}개 파일, {total_size} bytes")

            uploaded_files = []
            failed_files = []
            uploaded_bytes = 0

            # 파일별 업로드
            for i, file_path in enumerate(files_to_upload):
                try:
                    # 상대 경로 계산
                    relative_path = file_path.relative_to(local_dir)
                    target_file_path = f"{target_path.rstrip('/')}/{relative_path}"

                    # 진행 상태 업데이트
                    progress.current_file = str(file_path)
                    progress.completed_files = i
                    progress.uploaded_bytes = uploaded_bytes

                    # 개별 파일 업로드
                    file_result = self.upload_file(
                        str(file_path), target_file_path, repo, f"{upload_id}_file_{i}"
                    )

                    if file_result.success:
                        uploaded_files.extend(file_result.uploaded_files)
                        uploaded_bytes += file_path.stat().st_size
                    else:
                        failed_files.extend(file_result.failed_files)

                    # 진행 상태 업데이트
                    progress.uploaded_bytes = uploaded_bytes
                    if i > 0:
                        elapsed_time = time.time() - start_time
                        progress.speed_bps = (
                            uploaded_bytes / elapsed_time if elapsed_time > 0 else 0.0
                        )
                        remaining_bytes = total_size - uploaded_bytes
                        progress.eta_seconds = (
                            remaining_bytes / progress.speed_bps
                            if progress.speed_bps > 0
                            else 0.0
                        )

                except Exception as e:
                    self.logger.error(f"파일 업로드 중 예외: {file_path}, 오류: {e}")
                    failed_file = {
                        "local_path": str(file_path),
                        "target_path": f"{target_path}/{file_path.relative_to(local_dir)}",
                        "error": str(e),
                    }
                    failed_files.append(failed_file)

            upload_time = time.time() - start_time

            # 최종 진행 상태 업데이트
            progress.completed_files = len(files_to_upload)
            progress.uploaded_bytes = uploaded_bytes

            self.logger.info(
                f"디렉토리 업로드 완료: {len(uploaded_files)} 성공, {len(failed_files)} 실패"
            )

            return UploadResult(
                success=len(failed_files) == 0,
                uploaded_files=uploaded_files,
                failed_files=failed_files,
                total_uploaded=len(uploaded_files),
                total_failed=len(failed_files),
                total_size=uploaded_bytes,
                upload_time=upload_time,
            )

        except Exception as e:
            upload_time = time.time() - start_time
            self.logger.error(f"디렉토리 업로드 중 예외 발생: {local_path}, 오류: {e}")

            return UploadResult(
                success=False,
                uploaded_files=[],
                failed_files=[
                    {
                        "local_path": local_path,
                        "target_path": target_path,
                        "error": str(e),
                    }
                ],
                total_uploaded=0,
                total_failed=1,
                total_size=0,
                upload_time=upload_time,
            )
        finally:
            # 진행 상태 정리
            if upload_id in self.active_uploads:
                del self.active_uploads[upload_id]

    def upload_file_chunked(
        self,
        local_path: str,
        target_path: str = None,
        repo: str = None,
        chunk_size: int = None,
    ) -> UploadResult:
        """
        대형 파일 청크 업로드

        Args:
            local_path: 업로드할 로컬 파일 경로
            target_path: 타겟 경로 (없으면 파일명 사용)
            repo: 리포지토리 (없으면 기본 리포지토리 사용)
            chunk_size: 청크 크기 (바이트, 기본값: 10MB)

        Returns:
            UploadResult: 업로드 결과
        """
        try:
            # 파일 존재 확인
            local_file = Path(local_path)
            if not local_file.exists():
                raise JFrogUploadError(f"파일을 찾을 수 없습니다: {local_path}")

            file_size = local_file.stat().st_size

            # 청크 크기 설정 (기본값: 10MB)
            if not chunk_size:
                chunk_size = 10 * 1024 * 1024  # 10MB

            # 파일 크기가 청크 크기보다 작으면 일반 업로드 사용
            if file_size <= chunk_size:
                self.logger.info(
                    f"파일 크기가 청크 크기보다 작아 일반 업로드를 사용합니다: {local_path}"
                )
                return self.upload_file(local_path, target_path, repo)

            self.logger.info(
                f"대형 파일 청크 업로드 시작: {local_path} ({file_size} bytes, 청크: {chunk_size} bytes)"
            )

            # jf-cli는 자동으로 청크 업로드를 지원하므로 --chunk-size 옵션 사용
            target_path = target_path or local_file.name
            target_repo = repo or self.config.default_repo
            upload_target = f"{target_repo}/{target_path.lstrip('/')}"

            cmd = [
                "jf",
                "rt",
                "upload",
                "--flat=true",
                f"--chunk-size={chunk_size}",
                str(local_file),
                upload_target,
            ]

            start_time = time.time()
            result = self._execute_jf_command(
                cmd, timeout=self.config.upload_timeout * 2
            )  # 대형 파일은 타임아웃 2배
            upload_time = time.time() - start_time

            if result.returncode == 0:
                uploaded_file = {
                    "local_path": str(local_file),
                    "target_path": target_path,
                    "upload_target": upload_target,
                    "url": f"{self.config.artifactory_url}/{upload_target}",
                    "size": file_size,
                    "upload_time": upload_time,
                    "chunked": True,
                    "chunk_size": chunk_size,
                }

                self.logger.info(f"대형 파일 청크 업로드 성공: {upload_target}")

                return UploadResult(
                    success=True,
                    uploaded_files=[uploaded_file],
                    failed_files=[],
                    total_uploaded=1,
                    total_failed=0,
                    total_size=file_size,
                    upload_time=upload_time,
                )
            else:
                error_msg = (
                    result.stderr.strip() if result.stderr else "알 수 없는 오류"
                )
                failed_file = {
                    "local_path": str(local_file),
                    "target_path": target_path,
                    "error": error_msg,
                }

                self.logger.error(
                    f"대형 파일 청크 업로드 실패: {local_path}, 오류: {error_msg}"
                )

                return UploadResult(
                    success=False,
                    uploaded_files=[],
                    failed_files=[failed_file],
                    total_uploaded=0,
                    total_failed=1,
                    total_size=0,
                    upload_time=upload_time,
                )

        except Exception as e:
            self.logger.error(
                f"대형 파일 청크 업로드 중 예외 발생: {local_path}, 오류: {e}"
            )

            failed_file = {
                "local_path": local_path,
                "target_path": target_path,
                "error": str(e),
            }

            return UploadResult(
                success=False,
                uploaded_files=[],
                failed_files=[failed_file],
                total_uploaded=0,
                total_failed=1,
                total_size=0,
                upload_time=0.0,
            )

    def get_upload_progress(self, upload_id: str) -> Optional[UploadProgress]:
        """
        업로드 진행 상태 가져오기

        Args:
            upload_id: 업로드 ID

        Returns:
            UploadProgress: 진행 상태 정보 (없으면 None)
        """
        return self.active_uploads.get(upload_id)

    def cancel_upload(self, upload_id: str) -> bool:
        """
        업로드 취소

        Args:
            upload_id: 업로드 ID

        Returns:
            bool: 취소 성공 여부
        """
        if upload_id in self.active_uploads:
            # 진행 상태에서 제거
            del self.active_uploads[upload_id]
            self.logger.info(f"업로드 취소: {upload_id}")
            return True
        return False

    def _execute_jf_command(
        self, cmd: List[str], timeout: int = None
    ) -> subprocess.CompletedProcess:
        """
        jf-cli 명령어 실행

        Args:
            cmd: 실행할 명령어 리스트
            timeout: 타임아웃 (초)

        Returns:
            subprocess.CompletedProcess: 명령어 실행 결과
        """
        try:
            self.logger.debug(f"jf-cli 명령어 실행: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.config.upload_timeout,
            )

            if result.returncode != 0:
                error_msg = (
                    result.stderr.strip() if result.stderr else result.stdout.strip()
                )
                self.logger.error(
                    f"jf-cli 명령어 실패: {' '.join(cmd)}, 오류: {error_msg}"
                )
            else:
                self.logger.debug(f"jf-cli 명령어 성공: {' '.join(cmd)}")

            return result

        except subprocess.TimeoutExpired as e:
            self.logger.error(
                f"jf-cli 명령어 타임아웃: {' '.join(cmd)}, 타임아웃: {timeout}초"
            )
            raise JFrogUploadError(f"업로드 타임아웃: {timeout}초")

        except Exception as e:
            self.logger.error(f"jf-cli 명령어 실행 실패: {' '.join(cmd)}, 오류: {e}")
            raise JFrogUploadError(f"업로드 명령어 실행 실패: {str(e)}")
