# -*- coding: utf-8 -*-
"""
GlobalDumpCoordinator (Deprecated)
이 클래스는 하위 호환성을 위해 유지되며, 모든 기능은 UnifiedDumpCoordinator로 이관되었습니다.
이제 UnifiedDumpCoordinator를 사용하십시오.
"""

from __future__ import annotations

from QSUtils.Utils.Logger import LOGW


class GlobalDumpCoordinator:
    """
    @deprecated: UnifiedDumpCoordinator를 사용하십시오.
    """

    def __init__(self, main_window) -> None:
        self._mw = main_window
        LOGW(
            "GlobalDumpCoordinator is deprecated. All its functions are now handled by UnifiedDumpCoordinator."
        )

    def start(self) -> None:
        """아무 작업도 하지 않습니다. UnifiedDumpCoordinator가 이벤트를 처리합니다."""
        pass

    def stop(self) -> None:
        """아무 작업도 하지 않습니다."""
        pass
