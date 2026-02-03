#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device Context for UIFramework
디바이스별 컨텍스트를 관리하는 공통 클래스
"""

from typing import Dict, Any, Optional

from QSUtils.ADBDevice.ADBDevice import ADBDevice
from QSUtils.UIFramework.base.EventManager import EventManager
from QSUtils.UIFramework.base.FeatureRegistry import FeatureRegistry
from QSUtils.UIFramework.config.SettingsManager import SettingsManager
from QSUtils.Utils.Logger import LOGD


class DeviceContext:
    """
    디바이스별 컨텍스트 관리 클래스

    QSMonitor와 QSLogger에서 공통으로 사용하는 컴포넌트들을 캡슐화하고,
    self.parent 접근 패턴을 개선하기 위한 클래스입니다.
    """

    def __init__(
        self,
        event_manager: EventManager,
        adb_device: ADBDevice,
        settings_manager: SettingsManager,
    ):
        """
        DeviceContext 초기화

        Args:
            event_manager: 이벤트 관리자
            adb_device: ADB 디바이스 객체
            settings_manager: 설정 관리자
        """
        # 핵심 컴포넌트 (모든 앱에서 공통)
        self.event_manager = event_manager
        self.adb_device = adb_device
        self.settings_manager = settings_manager

        # FeatureRegistry 인스턴스
        self.feature_registry = FeatureRegistry()

        # 공통 서비스/매니저들
        self.logging_manager = None  # DeviceLoggingManager
        self.dump_manager = None  # DumpProcessManager

        # 공통 상태 관리
        self.is_running = False
        self.is_monitoring = False
        self.monitoring_interval = 500
        self.device_info: Dict[str, Any] = {}
        self.connection_status = "disconnected"

        # 앱별 확장을 위한 딕셔너리
        self.app_components: Dict[str, Any] = {}  # 앱별 컴포넌트 저장
        self.app_settings: Dict[str, Any] = {}  # 앱별 설정 저장

        LOGD(f"DeviceContext: Initialized for device {self.serial}")

    @property
    def serial(self) -> str:
        """디바이스 시리얼 번호 반환"""
        return self.adb_device.serial

    # 앱별 컴포넌트 관리 메서드
    def register_app_component(self, key: str, component: Any) -> None:
        """
        앱별 컴포넌트 등록

        Args:
            key: 컴포넌트 키
            component: 컴포넌트 객체
        """
        self.app_components[key] = component
        LOGD(
            f"DeviceContext: Registered app component '{key}' for device {self.serial}"
        )

    def get_app_component(self, key: str, default: Any = None) -> Any:
        """
        앱별 컴포넌트 가져오기

        Args:
            key: 컴포넌트 키
            default: 기본값

        Returns:
            컴포넌트 객체 또는 기본값
        """
        return self.app_components.get(key, default)

    def unregister_app_component(self, key: str) -> bool:
        """
        앱별 컴포넌트 제거

        Args:
            key: 컴포넌트 키

        Returns:
            제거 성공 여부
        """
        if key in self.app_components:
            del self.app_components[key]
            LOGD(
                f"DeviceContext: Unregistered app component '{key}' for device {self.serial}"
            )
            return True
        return False

    # 앱별 설정 관리 메서드
    def set_app_setting(self, key: str, value: Any) -> None:
        """
        앱별 설정 저장

        Args:
            key: 설정 키
            value: 설정 값
        """
        self.app_settings[key] = value
        LOGD(
            f"DeviceContext: Set app setting '{key}' = {value} for device {self.serial}"
        )

    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """
        앱별 설정 가져오기

        Args:
            key: 설정 키
            default: 기본값

        Returns:
            설정 값 또는 기본값
        """
        return self.app_settings.get(key, default)

    def remove_app_setting(self, key: str) -> bool:
        """
        앱별 설정 제거

        Args:
            key: 설정 키

        Returns:
            제거 성공 여부
        """
        if key in self.app_settings:
            del self.app_settings[key]
            LOGD(f"DeviceContext: Removed app setting '{key}' for device {self.serial}")
            return True
        return False

    # 공통 상태 관리 메서드
    def set_running_state(self, is_running: bool) -> None:
        """
        실행 상태 설정

        Args:
            is_running: 실행 상태
        """
        self.is_running = is_running
        LOGD(
            f"DeviceContext: Set running state to {is_running} for device {self.serial}"
        )

    def set_monitoring_state(self, is_monitoring: bool) -> None:
        """
        모니터링 상태 설정

        Args:
            is_monitoring: 모니터링 상태
        """
        self.is_monitoring = is_monitoring
        LOGD(
            f"DeviceContext: Set monitoring state to {is_monitoring} for device {self.serial}"
        )

    def set_connection_status(self, status: str) -> None:
        """
        연결 상태 설정

        Args:
            status: 연결 상태
        """
        self.connection_status = status
        LOGD(
            f"DeviceContext: Set connection status to '{status}' for device {self.serial}"
        )

    def update_device_info(self, info: Dict[str, Any]) -> None:
        """
        디바이스 정보 업데이트

        Args:
            info: 디바이스 정보 딕셔너리
        """
        self.device_info.update(info)
        LOGD(f"DeviceContext: Updated device info for device {self.serial}")

    # 유틸리티 메서드
    def get_all_app_components(self) -> Dict[str, Any]:
        """
        모든 앱별 컴포넌트 반환

        Returns:
            앱별 컴포넌트 딕셔너리
        """
        return self.app_components.copy()

    def get_all_app_settings(self) -> Dict[str, Any]:
        """
        모든 앱별 설정 반환

        Returns:
            앱별 설정 딕셔너리
        """
        return self.app_settings.copy()

    def clear_app_components(self) -> None:
        """모든 앱별 컴포넌트 제거"""
        self.app_components.clear()
        LOGD(f"DeviceContext: Cleared all app components for device {self.serial}")

    def clear_app_settings(self) -> None:
        """모든 앱별 설정 제거"""
        self.app_settings.clear()
        LOGD(f"DeviceContext: Cleared all app settings for device {self.serial}")

    def get_log_directory(self) -> Optional[str]:
        """
        현재 로그 디렉토리 반환 (logging_manager 통해)

        Returns:
            현재 로그 디렉토리 경로, 없으면 None
        """
        if self.logging_manager:
            return self.logging_manager.get_log_directory()
        return None

    def set_log_directory(self, directory: str) -> None:
        """
        로그 저장 디렉토리 설정 (데이터 컨테이너 역할에 충실)

        Args:
            directory: 로그 저장 디렉토리 경로
        """
        if self.logging_manager:
            self.logging_manager.set_log_directory(directory)
            LOGD(
                f"DeviceContext: Set log directory to '{directory}' for device {self.serial}"
            )

    def cleanup(self) -> None:
        """
        디바이스 컨텍스트 정리

        앱 종료 시 리소스 정리를 위해 호출됩니다.
        """
        LOGD(f"DeviceContext: Starting cleanup for device {self.serial}")

        # 앱별 컴포넌트 정리
        for key, component in self.app_components.items():
            try:
                if hasattr(component, "cleanup") and callable(
                    getattr(component, "cleanup")
                ):
                    component.cleanup()
                    LOGD(f"DeviceContext: Cleaned up app component '{key}'")
                elif hasattr(component, "stop") and callable(
                    getattr(component, "stop")
                ):
                    component.stop()
                    LOGD(f"DeviceContext: Stopped app component '{key}'")
            except Exception as e:
                LOGD(f"DeviceContext: Error cleaning up app component '{key}': {e}")

        # 공통 서비스 정리
        try:
            if self.logging_manager and hasattr(self.logging_manager, "stop_logging"):
                self.logging_manager.stop_logging()
        except Exception as e:
            LOGD(f"DeviceContext: Error stopping logging manager: {e}")

        try:
            if self.dump_manager and hasattr(self.dump_manager, "cleanup"):
                self.dump_manager.cleanup()
        except Exception as e:
            LOGD(f"DeviceContext: Error cleaning up dump manager: {e}")

        # 데이터 정리
        self.clear_app_components()
        self.clear_app_settings()
        self.device_info.clear()

        LOGD(f"DeviceContext: Cleanup completed for device {self.serial}")

    def __str__(self) -> str:
        """문자열 표현"""
        return (
            f"DeviceContext(serial={self.serial}, components={len(self.app_components)}, "
            f"settings={len(self.app_settings)})"
        )

    def __repr__(self) -> str:
        """상세 문자열 표현"""
        return (
            f"DeviceContext(serial={self.serial}, is_running={self.is_running}, "
            f"is_monitoring={self.is_monitoring}, "
            f"connection_status={self.connection_status}, "
            f"components={list(self.app_components.keys())}, "
            f"settings={list(self.app_settings.keys())})"
        )
