#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FeatureRegistry - Feature 등록 및 관리를 위한 레지스트리 시스템
"""

from typing import Dict, List, Type, Any

from QSUtils.Utils.Logger import LOGD


class FeatureRegistry:
    """
    Feature 등록 및 관리를 위한 레지스트리

    Feature별 필요한 command handler를 관리하고
    활성화된 feature에 따라 동적으로 handler 목록을 제공
    """

    def __init__(self):
        """FeatureRegistry 초기화"""
        self._registered_features: Dict[str, Dict[str, Any]] = {}
        self._feature_instances: Dict[str, Any] = {}
        LOGD("FeatureRegistry: Initialized")

    def register_feature(
        self,
        feature_name: str,
        feature_class: Type,
        command_handlers: List[Type] = None,
    ):
        """
        Feature와 필요한 command handlers 등록

        Args:
            feature_name: Feature 이름 (예: 'DefaultMonitor')
            feature_class: Feature 클래스 타입
            command_handlers: Feature가 필요한 command handler 클래스 목록
        """
        if feature_name in self._registered_features:
            LOGD(
                f"FeatureRegistry: Feature {feature_name} already registered, updating"
            )

        self._registered_features[feature_name] = {
            "feature_class": feature_class,
            "command_handlers": command_handlers or [],
            "enabled": True,  # 기본 활성화
        }

        LOGD(
            f"FeatureRegistry: Registered feature {feature_name} with {len(command_handlers or [])} command handlers"
        )

    def enable_feature(self, feature_name: str):
        """Feature 활성화"""
        if feature_name in self._registered_features:
            self._registered_features[feature_name]["enabled"] = True
            LOGD(f"FeatureRegistry: Enabled feature {feature_name}")

    def disable_feature(self, feature_name: str):
        """Feature 비활성화"""
        if feature_name in self._registered_features:
            self._registered_features[feature_name]["enabled"] = False
            LOGD(f"FeatureRegistry: Disabled feature {feature_name}")

    def get_command_handlers_for_features(self, feature_names: List[str]) -> List[Type]:
        """
        활성화된 feature들의 command handlers 반환

        Args:
            feature_names: 활성화할 feature 이름 목록

        Returns:
            List[Type]: command handler 클래스 목록
        """
        command_handlers = []

        for feature_name in feature_names:
            if feature_name in self._registered_features:
                feature_info = self._registered_features[feature_name]

                if feature_info["enabled"]:
                    command_handlers.extend(feature_info["command_handlers"])
                    LOGD(
                        f"FeatureRegistry: Added {len(feature_info['command_handlers'])} handlers from {feature_name}"
                    )
                else:
                    LOGD(f"FeatureRegistry: Skipped disabled feature {feature_name}")
            else:
                LOGD(f"FeatureRegistry: Feature {feature_name} not found")

        # 중복 제거
        unique_handlers = list(set(command_handlers))

        LOGD(f"FeatureRegistry: Returning {len(unique_handlers)} command handlers")

        return unique_handlers

    def get_all_command_handlers(self) -> List[Type]:
        """
        등록된 모든 활성화된 feature의 command handlers 반환

        Returns:
            List[Type]: command handler 클래스 목록
        """
        enabled_features = [
            name for name, info in self._registered_features.items() if info["enabled"]
        ]

        return self.get_command_handlers_for_features(enabled_features)

    def get_registered_features(self) -> Dict[str, Dict[str, Any]]:
        """
        등록된 모든 feature 정보 반환

        Returns:
            Dict[str, Dict[str, Any]]: feature 정보 딕셔너리
        """
        return {
            name: {
                "enabled": info["enabled"],
                "handler_count": len(info["command_handlers"]),
                "feature_class": info["feature_class"].__name__,
            }
            for name, info in self._registered_features.items()
        }

    def clear_registry(self):
        """레지스트리 초기화"""
        self._registered_features.clear()
        self._feature_instances.clear()
        LOGD("FeatureRegistry: Registry cleared")
