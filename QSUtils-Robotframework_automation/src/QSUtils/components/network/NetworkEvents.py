"""
Network event definitions for event-based architecture.
This module provides structured event classes for network-related notifications.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class NetworkEventType(Enum):
    """네트워크 이벤트 타입 정의"""

    WIFI_INFO_UPDATED = "wifi_info_updated"
    CONNECTION_STATUS_CHANGED = "connection_status_changed"
    NETWORK_ERROR = "network_error"
    SCAN_COMPLETED = "scan_completed"


class NetworkEvent(ABC):
    """네트워크 이벤트의 기본 클래스"""

    @property
    @abstractmethod
    def event_type(self) -> NetworkEventType:
        """이벤트 타입 반환"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """이벤트 데이터를 딕셔너리로 변환"""
        return self.__dict__


@dataclass
class WiFiInfoUpdatedEvent(NetworkEvent):
    """WiFi 정보 업데이트 이벤트"""

    ssid: str
    ip_address: str
    router_address: str
    rssi: str

    @property
    def event_type(self) -> NetworkEventType:
        return NetworkEventType.WIFI_INFO_UPDATED


@dataclass
class NetworkConnectionEvent(NetworkEvent):
    """네트워크 연결 상태 변경 이벤트"""

    connected: bool
    ssid: str = ""
    error_message: str = ""

    @property
    def event_type(self) -> NetworkEventType:
        return NetworkEventType.CONNECTION_STATUS_CHANGED


@dataclass
class NetworkErrorEvent(NetworkEvent):
    """네트워크 오류 이벤트"""

    error_code: str
    error_message: str
    recoverable: bool = True

    @property
    def event_type(self) -> NetworkEventType:
        return NetworkEventType.NETWORK_ERROR


@dataclass
class NetworkScanEvent(NetworkEvent):
    """네트워크 스캔 완료 이벤트"""

    available_networks: List[str]
    signal_strengths: Dict[str, int]

    @property
    def event_type(self) -> NetworkEventType:
        return NetworkEventType.SCAN_COMPLETED


class EventSubscriber:
    """이벤트 구독자 인터페이스"""

    def handle_event(self, event: NetworkEvent):
        """이벤트 처리 메서드"""
        pass


class EventBus:
    """이벤트 버스 - 이벤트 발행 및 구독 관리"""

    def __init__(self):
        self._subscribers: Dict[NetworkEventType, List[EventSubscriber]] = {}

    def subscribe(self, event_type: NetworkEventType, subscriber: EventSubscriber):
        """이벤트 타입에 구독자 등록"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(subscriber)

    def unsubscribe(self, event_type: NetworkEventType, subscriber: EventSubscriber):
        """이벤트 타입에서 구독자 해제"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(subscriber)
            except ValueError:
                pass

    def publish(self, event: NetworkEvent):
        """이벤트 발행"""
        event_type = event.event_type
        if event_type in self._subscribers:
            for subscriber in self._subscribers[event_type]:
                try:
                    subscriber.handle_event(event)
                except Exception as e:
                    # 구독자의 예외가 다른 구독자에게 영향을 주지 않도록 처리
                    print(f"Error in event subscriber: {e}")


# 전역 이벤트 버스 인스턴스
event_bus = EventBus()
