# -*- coding: utf-8 -*-
"""
Unified Dump Coordinator for QSMonitor
통합된 덤프 요청을 처리하고 경로 전략을 관리하는 코디네이터 클래스입니다.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Callable, Any

from QSUtils.DumpManager.DumpTypes import DumpTriggeredBy, DumpMode
from QSUtils.JFrogUtils.JFrogManager import JFrogManager
from QSUtils.QSMonitor.core.GlobalEvents import GlobalEventType
from QSUtils.UIFramework.base.CommonEvents import CommonEventType
from QSUtils.UIFramework.base.DeviceContext import DeviceContext
from QSUtils.UIFramework.base.GlobalEventManager import get_global_event_bus
from QSUtils.Utils.DateTimeUtils import TimestampGenerator
from QSUtils.Utils.Logger import LOGD, LOGI, LOGW


class DumpPathStrategy(ABC):
    """덤프 경로 결정 전략의 추상 기본 클래스"""

    @abstractmethod
    def create_dump_directory(
        self, device_serial: str, timestamp: str, triggered_by: str
    ) -> Path:
        """덤프 디렉토리 생성"""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """전략 이름 반환"""
        pass


class UnifiedPathStrategy(DumpPathStrategy):
    """통합된 경로 구조 전략 (logs/{prefix}/{timestamp}/)"""

    def __init__(self, log_directory: Optional[str] = None, settings_manager=None):
        self.log_directory = log_directory or "logs"
        self.settings_manager = settings_manager
        self._directory_prefix = self._load_directory_prefix()

    def _load_directory_prefix(self) -> str:
        """설정에서 디렉토리 접두사 로드"""
        try:
            if self.settings_manager:
                upload_settings = self.settings_manager.get("dump.upload_settings", {})
                return upload_settings.get("local_directory_prefix", "issues")
            return "issues"
        except Exception:
            return "issues"

    def create_dump_directory(
        self, device_serial: str, timestamp: str, triggered_by: str
    ) -> Path:
        """통합된 경로 구조 생성 (설정된 디렉토리 접두사 사용)"""
        base_path = Path(self.log_directory) / self._directory_prefix / timestamp
        device_path = base_path / device_serial
        return device_path

    def get_strategy_name(self) -> str:
        return "unified"


class IndividualPathStrategy(DumpPathStrategy):
    """개별 디바이스 경로 구조 전략 (logs/dumps/{serial}/)"""

    def __init__(self, log_directory: Optional[str] = None):
        self.log_directory = log_directory or "logs"

    def create_dump_directory(
        self, device_serial: str, timestamp: str, triggered_by: str
    ) -> Path:
        """개별 디바이스 경로 구조 생성"""
        base_path = Path(self.log_directory) / "dumps" / device_serial
        return base_path

    def get_strategy_name(self) -> str:
        return "individual"


class HybridPathStrategy(DumpPathStrategy):
    """하이브리드 경로 구조 전략 (트리거에 따라 선택)"""

    def __init__(self, log_directory: Optional[str] = None):
        self.log_directory = log_directory or "logs"
        self.unified_strategy = UnifiedPathStrategy(log_directory)
        self.individual_strategy = IndividualPathStrategy(log_directory)

    def create_dump_directory(
        self, device_serial: str, timestamp: str, triggered_by: str
    ) -> Path:
        """트리거 타입에 따라 경로 전략 선택"""
        if triggered_by in [DumpTriggeredBy.QS_FAILED.value]:
            return self.unified_strategy.create_dump_directory(
                device_serial, timestamp, triggered_by
            )
        else:
            return self.individual_strategy.create_dump_directory(
                device_serial, timestamp, triggered_by
            )

    def get_strategy_name(self) -> str:
        return "hybrid"


class UnifiedDumpCoordinator:
    """통합 덤프 요청을 처리하는 코디네이터"""

    def __init__(self, main_window):
        """
        UnifiedDumpCoordinator 초기화
        Args:
            main_window: QSMonitor 메인 윈도우
        """
        self._mw = main_window
        self._bus = get_global_event_bus()

        # 진행 중 이슈 상태
        self._active_issue_id: Optional[str] = None
        self._active_triggered_by: str = "unknown"
        self._active_dump_mode: DumpMode = DumpMode.DIALOG
        self._targets: Set[str] = set()
        self._completed: Set[str] = set()
        self._success_count: int = 0
        self._fail_count: int = 0
        self._issue_root: Optional[Path] = None

        # 디바이스 이벤트 핸들러 레지스트리: serial -> [(event_type, handler), ...]
        self._device_handlers: Dict[str, List[Tuple[Any, Callable]]] = {}

        # 동시성 제어
        self._max_concurrency: int = 3
        self._inflight: int = 0
        self._pending_contexts: List[DeviceContext] = []

        # 경로 전략
        self._path_strategy: DumpPathStrategy = self._create_path_strategy()

        # JFrog 업로드 매니저 초기화
        self._upload_manager = None
        self._init_upload_manager()

        # 업로드 전용 스레드 풀 (동시 업로드 방지를 위해 max_workers=1 설정)
        self._upload_executor = ThreadPoolExecutor(max_workers=1)

        LOGD(
            f"UnifiedDumpCoordinator: Initialized with path strategy: {self._path_strategy.get_strategy_name()}"
        )

    def _create_path_strategy(self) -> DumpPathStrategy:
        """설정에 따라 경로 전략 생성"""
        strategy_name = "unified"
        settings_manager = None
        try:
            if hasattr(self._mw, "controller") and hasattr(
                self._mw.controller, "settings_manager"
            ):
                settings_manager = self._mw.controller.settings_manager
                strategy_name = settings_manager.get("dump.path_strategy", "unified")
        except Exception:
            pass

        log_directory = self._get_log_directory()

        if strategy_name == "unified":
            return UnifiedPathStrategy(log_directory, settings_manager)
        elif strategy_name == "individual":
            return IndividualPathStrategy(log_directory)
        elif strategy_name == "hybrid":
            return HybridPathStrategy(log_directory)
        else:
            LOGW(f"Unknown path strategy: {strategy_name}, falling back to unified")
            return UnifiedPathStrategy(log_directory, settings_manager)

    # ---------------- Lifecycle ----------------

    def start(self) -> None:
        """코디네이터 시작 및 이벤트 핸들러 등록"""
        # Common 이벤트 핸들러 등록
        self._bus.register_event_handler(
            CommonEventType.UNIFIED_DUMP_REQUESTED, self._on_unified_dump_requested
        )

        # Global 이벤트 핸들러 등록
        self._bus.register_event_handler(
            GlobalEventType.UNIFIED_DUMP_REQUESTED, self._on_unified_dump_requested
        )
        self._bus.register_event_handler(
            GlobalEventType.GLOBAL_DUMP_REQUESTED, self._on_unified_dump_requested
        )

        # JFrog 업로드 결과 수신 (UI에서 수행한 업로드 결과 반영을 위함)
        self._bus.register_event_handler(
            GlobalEventType.JFROG_UPLOAD_COMPLETED, self._on_jfrog_upload_completed
        )

        LOGI("UnifiedDumpCoordinator: Started and registered event handlers")

    def stop(self) -> None:
        """코디네이터 중지 및 이벤트 핸들러 해제"""
        try:
            self._bus.unregister_event_handler(
                CommonEventType.UNIFIED_DUMP_REQUESTED, self._on_unified_dump_requested
            )
            self._bus.unregister_event_handler(
                GlobalEventType.UNIFIED_DUMP_REQUESTED, self._on_unified_dump_requested
            )
            self._bus.unregister_event_handler(
                GlobalEventType.GLOBAL_DUMP_REQUESTED, self._on_unified_dump_requested
            )
            self._bus.unregister_event_handler(
                GlobalEventType.JFROG_UPLOAD_COMPLETED, self._on_jfrog_upload_completed
            )
        except Exception:
            pass

        self._unregister_all_device_handlers()

        # 스레드 풀 정리
        try:
            self._upload_executor.shutdown(wait=False)
        except Exception:
            pass

        LOGI("UnifiedDumpCoordinator: Stopped")

    # ---------------- Event handlers ----------------

    def _on_unified_dump_requested(self, args: Dict) -> None:
        """통합 덤프 요청 수신"""
        if self._active_issue_id is not None:
            # 간단한 중복 방지: 진행 중이면 무시
            LOGW(
                f"UnifiedDumpCoordinator: Another unified dump is in progress "
                f"(issue_id={self._active_issue_id}), ignoring"
            )
            return

        triggered_by = args.get("triggered_by", "unknown")
        self._active_triggered_by = triggered_by

        # 트리거 타입에 따라 기본 덤프 모드 결정
        # QS_FAILED, CRASH_MONITOR는 HEADLESS 모드로 실행 (Dialog 방지)
        self._active_dump_mode = DumpMode.DIALOG
        if triggered_by in [
            DumpTriggeredBy.QS_FAILED.value,
            DumpTriggeredBy.CRASH_MONITOR.value,
        ]:
            self._active_dump_mode = DumpMode.HEADLESS

        LOGI(
            f"UnifiedDumpCoordinator: Received unified dump request - triggered_by: {triggered_by}, mode: {self._active_dump_mode.value}"
        )

        # 대상 디바이스 목록 확인
        device_contexts: List[DeviceContext] = self._get_active_device_contexts()
        if not device_contexts:
            LOGW("UnifiedDumpCoordinator: No active devices to dump")
            return

        # 이슈 ID/디렉토리 설정
        issue_id = args.get("timestamp") or TimestampGenerator.get_log_timestamp()
        self._active_issue_id = issue_id

        # 경로 전략으로 이슈 디렉토리 생성
        self._issue_root = self._path_strategy.create_dump_directory(
            device_contexts[0].serial,  # 첫 번째 디바이스로 기본 경로 생성
            issue_id,
            triggered_by,
        ).parent  # 상위 디렉토리 (issues/{timestamp})

        if not self._ensure_directory_exists(self._issue_root):
            LOGW(
                f"UnifiedDumpCoordinator: Failed to create issue directory: {self._issue_root}"
            )
            return

        # manifest 초기 작성
        request_device_id = args.get("request_device_id", "unknown")
        upload_enabled = args.get("upload_enabled")

        # 시리얼 번호 수집 (내부 추적용이므로 공백을 포함한 원본 시리얼 사용)
        target_serials = [str(ctx.serial) for ctx in device_contexts]

        self._targets = set(target_serials)
        self._completed = set()
        self._success_count = 0
        self._fail_count = 0

        self._write_manifest(
            {
                "issue_id": issue_id,
                "triggered_by": triggered_by,
                "path_strategy": self._path_strategy.get_strategy_name(),
                "request_device_id": request_device_id,
                "targets": target_serials,
                "results": {},
                "success_count": 0,
                "fail_count": 0,
                "issue_dir": str(self._issue_root),
                "upload_enabled": upload_enabled,
            }
        )

        # 디바이스 이벤트 핸들러 등록 및 병렬 제한을 적용한 덤프 요청 큐잉
        self._pending_contexts = list(device_contexts)
        self._inflight = 0
        self._launch_more_if_possible()

    # ---------------- Device result handling ----------------

    def _register_device_handlers(self, ctx: DeviceContext) -> None:
        """디바이스별 이벤트 핸들러 등록"""

        def on_completed(args: Dict):
            success = bool(args.get("success", False))
            self._handle_device_result(ctx.serial, success, args)

        def on_error(args: Dict):
            self._handle_device_result(ctx.serial, False, args)

        ctx.event_manager.register_event_handler(
            CommonEventType.DUMP_COMPLETED, on_completed
        )
        ctx.event_manager.register_event_handler(CommonEventType.DUMP_ERROR, on_error)

        self._device_handlers.setdefault(ctx.serial, []).extend(
            [
                (CommonEventType.DUMP_COMPLETED, on_completed),
                (CommonEventType.DUMP_ERROR, on_error),
            ]
        )

    def _unregister_all_device_handlers(self) -> None:
        """모든 디바이스 이벤트 핸들러 해제"""
        for serial, handlers in list(self._device_handlers.items()):
            ctx = self._find_device_context(serial)
            if ctx is not None:
                for et, h in handlers:
                    try:
                        ctx.event_manager.unregister_event_handler(et, h)
                    except Exception:
                        pass
            self._device_handlers.pop(serial, None)

    def _handle_device_result(self, serial: str, success: bool, args: Dict) -> None:
        """디바이스 덤프 결과 처리"""
        if self._active_issue_id is None or self._issue_root is None:
            return

        if serial in self._completed:
            return

        self._completed.add(serial)
        if success:
            self._success_count += 1
        else:
            self._fail_count += 1

        # manifest 갱신
        manifest = self._read_manifest()
        results = manifest.get("results", {})
        results[serial] = {
            "success": success,
            "args": args,
        }
        manifest["results"] = results
        manifest["success_count"] = self._success_count
        manifest["fail_count"] = self._fail_count
        self._write_manifest(manifest)

        LOGD(
            f"UnifiedDumpCoordinator: Device {serial} completed: success={success} "
            f"({len(self._completed)}/{len(self._targets)})"
        )

        # 진행률 이벤트 발행
        try:
            self._bus.emit_event(
                GlobalEventType.GLOBAL_DUMP_PROGRESS,
                {
                    "issue_id": self._active_issue_id or "",
                    "completed": len(self._completed),
                    "total": len(self._targets),
                },
            )
        except Exception:
            pass

        # 전체 완료 시 전역 완료 이벤트 발행 및 정리
        if self._targets and self._completed >= self._targets:
            try:
                self._bus.emit_event(
                    GlobalEventType.GLOBAL_DUMP_COMPLETED,
                    {
                        "issue_id": self._active_issue_id,
                        "success_count": self._success_count,
                        "fail_count": self._fail_count,
                        "issue_dir": str(self._issue_root),
                    },
                )
                LOGI(
                    f"UnifiedDumpCoordinator: GLOBAL_DUMP_COMPLETED issued "
                    f"(issue_id={self._active_issue_id})"
                )

                # 덤프 완료 후 JFrog 업로드 처리
                self._handle_upload_after_dump_completion()
            finally:
                # 핸들러 해제 및 상태 초기화
                self._unregister_all_device_handlers()
                self._active_issue_id = None
                self._targets.clear()
                self._completed.clear()
                self._success_count = 0
                self._fail_count = 0
                self._issue_root = None
                self._pending_contexts = []
                self._inflight = 0
        else:
            # 더 실행할 수 있다면 다음 작업 시작
            if self._inflight > 0:
                self._inflight -= 1
            self._launch_more_if_possible()

    # ---------------- Helpers ----------------

    def _launch_more_if_possible(self) -> None:
        """동시성 제어 내에서 가능한 만큼 덤프 실행"""
        if self._issue_root is None or self._active_issue_id is None:
            return

        while self._pending_contexts and self._inflight < self._max_concurrency:
            ctx = self._pending_contexts.pop(0)
            self._register_device_handlers(ctx)

            device_issue_dir = self._issue_root / ctx.serial
            if not self._ensure_directory_exists(device_issue_dir):
                LOGW(
                    f"UnifiedDumpCoordinator: Failed to create device directory: {device_issue_dir}"
                )
                continue

            LOGI(
                f"UnifiedDumpCoordinator: Requesting dump for device {ctx.serial} -> {device_issue_dir}"
            )

            try:
                self._inflight += 1

                # manifest에서 upload_enabled 가져오기
                manifest = self._read_manifest()
                upload_enabled = manifest.get("upload_enabled", False)

                ctx.event_manager.emit_event(
                    CommonEventType.DUMP_REQUESTED,
                    {
                        "triggered_by": self._active_triggered_by,
                        "issue_dir": str(device_issue_dir),
                        "issue_id": self._active_issue_id,
                        "dump_mode": self._active_dump_mode.value,
                        "upload_enabled": upload_enabled,
                    },
                )
            except Exception as e:
                LOGW(
                    f"UnifiedDumpCoordinator: Failed to request dump for {ctx.serial}: {e}"
                )

    def _get_active_device_contexts(self) -> List[DeviceContext]:
        """활성 디바이스 컨텍스트 목록 가져오기"""
        if hasattr(self._mw, "get_active_device_contexts"):
            try:
                return list(self._mw.get_active_device_contexts())
            except Exception:
                return []
        # Fallback: 접근 불가
        return []

    def _find_device_context(self, serial: str) -> Optional[DeviceContext]:
        """시리얼 번호로 디바이스 컨텍스트 찾기"""
        for ctx in self._get_active_device_contexts():
            if getattr(ctx, "serial", None) == serial:
                return ctx
        return None

    def _get_log_directory(self) -> Optional[str]:
        """로그 디렉토리 가져오기"""
        try:
            return self._mw.controller.settings_manager.get_log_directory()
        except Exception:
            return None

    def _get_upload_directory_prefix(self) -> str:
        """설정에서 업로드 디렉토리 접두사 로드"""
        try:
            if hasattr(self._mw, "controller") and hasattr(
                self._mw.controller, "settings_manager"
            ):
                upload_settings = self._mw.controller.settings_manager.get(
                    "dump.upload_settings", {}
                )
                return upload_settings.get("upload_directory_prefix", "issues")
            return "issues"
        except Exception:
            return "issues"

    def _manifest_path(self) -> Path:
        """manifest 파일 경로 반환"""
        assert self._issue_root is not None
        return self._issue_root / "manifest.json"

    def _read_manifest(self) -> Dict:
        """manifest 파일 읽기"""
        try:
            path = self._manifest_path()
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _write_manifest(self, manifest: Dict) -> None:
        """manifest 파일 쓰기"""
        try:
            path = self._manifest_path()
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            LOGW(f"UnifiedDumpCoordinator: Failed to write manifest: {e}")

    def _ensure_directory_exists(self, path: Path) -> bool:
        """디렉토리 생성 시 Windows 권한 문제 처리"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            LOGW(
                f"UnifiedDumpCoordinator: Permission denied creating directory: {path}"
            )
            return False
        except Exception as e:
            LOGW(f"UnifiedDumpCoordinator: Failed to create directory {path}: {e}")
            return False

    def _init_upload_manager(self) -> None:
        """JFrog 업로드 매니저 초기화"""
        try:
            self._upload_manager = JFrogManager()
            LOGD("UnifiedDumpCoordinator: JFrog upload manager initialized")
        except Exception as e:
            LOGW(
                f"UnifiedDumpCoordinator: Failed to initialize JFrog upload manager: {e}"
            )
            self._upload_manager = None

    def _should_upload_after_dump(
        self, triggered_by: str, upload_enabled: Optional[bool]
    ) -> bool:
        """덤프 완료 후 업로드할지 결정 (통합된 마스터 설정 기반)"""
        # 명시적으로 업로드가 비활성화된 경우
        if upload_enabled is False:
            return False

        # 명시적으로 업로드가 활성화된 경우
        if upload_enabled is True:
            return True

        # 설정이 없는 경우, 통합된 마스터 설정 확인
        try:
            if hasattr(self._mw, "controller") and hasattr(
                self._mw.controller, "settings_manager"
            ):
                upload_settings = self._mw.controller.settings_manager.get(
                    "dump.upload_settings", {}
                )
                auto_upload_enabled = upload_settings.get("auto_upload_enabled", True)
                return auto_upload_enabled
        except Exception:
            pass

        # 설정을 읽을 수 없는 경우, 기본값은 업로드 안 함
        return False

    def _handle_upload_after_dump_completion(self) -> None:
        """덤프 완료 후 JFrog 업로드 처리"""
        if self._upload_manager is None or self._issue_root is None:
            return

        manifest = self._read_manifest()
        upload_enabled = manifest.get("upload_enabled")
        triggered_by = manifest.get("triggered_by", "unknown")

        if not self._should_upload_after_dump(triggered_by, upload_enabled):
            LOGD("UnifiedDumpCoordinator: Upload not required for this dump")
            return

        # JFrog 설정 확인
        setup_result = self._upload_manager.verify_setup()
        if not setup_result.success:
            LOGW(
                f"UnifiedDumpCoordinator: JFrog setup verification failed: {setup_result.message}"
            )
            self._update_manifest_upload_result(
                False, setup_result.message, issue_root=self._issue_root
            )
            return

        # 업로드에 필요한 정보 캡처
        issue_id = self._active_issue_id
        issue_root = self._issue_root
        targets = list(self._targets) if self._targets else []

        if issue_id is None or issue_root is None:
            LOGW(
                "UnifiedDumpCoordinator: active_issue_id or issue_root is None, cannot upload"
            )
            return

        # UI 표시 여부 결정: 수동 덤프이거나 upload_enabled가 활성화된 경우 (사용자 요청 반영)
        show_dialog = (
            triggered_by == DumpTriggeredBy.MANUAL.value or upload_enabled is True
        )

        # 업로드 시작 이벤트 발행
        try:
            device_serial = targets[0] if targets else None
            self._bus.emit_event(
                GlobalEventType.JFROG_UPLOAD_STARTED,
                {
                    "issue_id": issue_id,
                    "device_serial": device_serial,
                    "show_dialog": show_dialog,
                    "issue_root": str(issue_root),
                    "targets": targets,
                    "triggered_by": triggered_by,
                },
            )
        except Exception as e:
            LOGW(
                f"UnifiedDumpCoordinator: Failed to emit JFROG_UPLOAD_STARTED event: {e}"
            )

        if show_dialog:
            LOGI(
                f"UnifiedDumpCoordinator: UI upload requested for issue {issue_id}. Waiting for UI results."
            )
            # 직접 업로드를 수행하지 않고 UI의 처리를 기다림
            return

        # 자동화 트리거나 Headless 모드인 경우 백그라운드에서 직접 업로드 수행
        LOGI(
            f"UnifiedDumpCoordinator: Starting asynchronous background upload for issue {issue_id}"
        )
        self._upload_executor.submit(
            self._perform_upload, issue_id, issue_root, targets
        )

    def _on_jfrog_upload_completed(self, args: Dict) -> None:
        """JFrog 업로드 완료 이벤트 핸들러 (UI 또는 백그라운드 작업 결과 수신)"""
        issue_id = args.get("issue_id")
        success = bool(args.get("success", False))
        message = args.get("message", "")
        upload_info = args.get("upload_info")
        issue_root_str = args.get("manifest_path")  # manifest_path에서 디렉토리 추출

        issue_root = None
        if issue_root_str:
            issue_root = Path(issue_root_str).parent

        LOGD(
            f"UnifiedDumpCoordinator: JFROG_UPLOAD_COMPLETED received for issue {issue_id} - success: {success}"
        )

        # manifest 갱신
        self._update_manifest_upload_result(
            success, message, upload_info, issue_root=issue_root
        )

    def _perform_upload(
        self, issue_id: str, issue_root: Path, targets: List[str]
    ) -> None:
        """JFrog 업로드 수행 (별도 스레드에서 실행됨)"""
        if self._upload_manager is None:
            return

        try:
            # 업로드 디렉토리 접두사 로드
            upload_prefix = self._get_upload_directory_prefix()

            # 이슈 디렉토리 전체 업로드
            upload_result = self._upload_manager.upload_directory(
                local_path=str(issue_root),
                target_path=f"{upload_prefix}/{issue_id}",
                repo=None,  # 기본 저장소 사용
            )

            # 결과 데이터 수집
            uploaded_files = []
            if issue_root and issue_root.exists():
                for file_path in issue_root.rglob("*"):
                    if file_path.is_file():
                        uploaded_files.append(str(file_path))

            jfrog_links = {}
            if upload_result.data:
                if "repo_url" in upload_result.data:
                    jfrog_links["repository"] = upload_result.data["repo_url"]
                if "target_url" in upload_result.data:
                    jfrog_links["upload"] = upload_result.data["target_url"]

            # 업로드 완료 이벤트 발행 (QTimer를 사용하여 메인 스레드 안전성 확보)
            from PySide6.QtCore import QTimer

            event_data = {
                "issue_id": issue_id,
                "success": upload_result.success,
                "message": upload_result.message,
                "upload_info": upload_result.data,
                "device_serial": targets[0] if targets else None,
                "device_serials": targets,
                "uploaded_files": uploaded_files,
                "jfrog_links": jfrog_links,
                "manifest_path": str(issue_root / "manifest.json"),
                "upload_id": issue_id,
            }

            QTimer.singleShot(
                0,
                lambda: self._bus.emit_event(
                    GlobalEventType.JFROG_UPLOAD_COMPLETED, event_data
                ),
            )

        except Exception as e:
            LOGW(f"UnifiedDumpCoordinator: Upload exception occurred: {e}")
            from PySide6.QtCore import QTimer

            event_data = {
                "issue_id": issue_id,
                "success": False,
                "message": str(e),
                "device_serial": targets[0] if targets else None,
                "device_serials": targets,
                "uploaded_files": [],
                "jfrog_links": {},
                "manifest_path": str(issue_root / "manifest.json"),
                "upload_id": issue_id,
            }

            QTimer.singleShot(
                0,
                lambda: self._bus.emit_event(
                    GlobalEventType.JFROG_UPLOAD_COMPLETED, event_data
                ),
            )

    def _update_manifest_upload_result(
        self,
        success: bool,
        message: str,
        upload_info: Optional[Dict] = None,
        issue_root: Optional[Path] = None,
    ) -> None:
        """manifest에 업로드 결과 기록"""
        try:
            # issue_root를 인자로 받거나 멤버 변수 사용
            root = issue_root or self._issue_root
            if root is None:
                return

            path = root / "manifest.json"
            if not path.exists():
                return

            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["upload_result"] = {
                "success": success,
                "message": message,
                "upload_info": upload_info,
                "timestamp": TimestampGenerator.get_log_timestamp(),
            }
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            LOGW(
                f"UnifiedDumpCoordinator: Failed to update manifest with upload result: {e}"
            )
