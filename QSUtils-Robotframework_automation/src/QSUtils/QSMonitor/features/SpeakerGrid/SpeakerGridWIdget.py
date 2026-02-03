from PySide6.QtWidgets import (
    QLabel,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

from QSUtils.QSMonitor.core.Events import QSMonitorEventType
from QSUtils.UIFramework.widgets.BaseEventWidget import BaseEventWidget, UIElementGroup
from QSUtils.Utils import LOGD, LOGE

GROUP_MINIMUM_WIDTH = 400  # 다른 Feature들과 유사한 너비로 증가


class SpeakerGridGroup(BaseEventWidget):
    """스피커 그리드 관리 클래스 - 이벤트 기반으로 동작"""

    def __init__(self, parent_widget, event_manager):
        super().__init__(parent_widget, event_manager, self.__class__.__name__)
        self.parent = parent_widget
        self.position_labels = {}
        self.current_position_id = None
        self.current_surround_active_ids = []

        self._setup_ui()
        self.setup_grid()  # 그리드 생성 호출
        self._apply_styles()

        # 이벤트 구독
        self._setup_event_subscriptions()

    def _setup_ui(self):
        # 메인 레이아웃 설정
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Speaker Grid 그룹 생성
        self.speaker_grid_group = self._create_speaker_grid_group()
        self.speaker_grid_group.setMinimumWidth(GROUP_MINIMUM_WIDTH)
        main_layout.addWidget(self.speaker_grid_group)

    def _create_speaker_grid_group(self):
        """Speaker Grid 그룹 생성"""
        speaker_grid_group_box = QGroupBox("Speaker Layout")
        speaker_grid_group_layout = QFormLayout()
        speaker_grid_group_layout.setContentsMargins(0, 0, 0, 0)
        speaker_grid_group_box.setLayout(speaker_grid_group_layout)

        # 스피커 그리드를 위한 컨테이너 위젯 생성
        self.speaker_grid_container = QWidget()
        self.speaker_grid_layout = QGridLayout()
        self.speaker_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.speaker_grid_container.setLayout(self.speaker_grid_layout)

        # FormLayout에 컨테이너 추가
        speaker_grid_group_layout.addRow(self.speaker_grid_container)

        return speaker_grid_group_box

    def _setup_event_subscriptions(self):
        """이벤트 구독 설정"""

        # SPEAKER_GRID_UPDATED 이벤트 구독
        self.event_manager.register_event_handler(
            QSMonitorEventType.SPEAKER_GRID_UPDATED, self._on_speaker_grid_update
        )
        LOGD("SpeakerGridManager: Registered handler for SPEAKER_GRID_UPDATED")

    def _on_speaker_grid_update(self, args):
        """스피커 그리드 업데이트 이벤트 처리"""
        try:
            update_type = args.get("update_type")
            data = args.get("data")

            if update_type == "speaker_remap":
                # 스피커 리맵핑 데이터 처리
                if data and "position_id" in data:
                    self.current_position_id = data.get("position_id")
                    self._apply_styles()
                    LOGD(
                        f"SpeakerGridManager: Updated speaker remap position: {self.current_position_id}"
                    )

            elif update_type == "surround_speaker":
                # 서라운드 스피커 데이터 처리
                if data and isinstance(data, list):
                    # 서라운드 스피커 데이터는 리스트 형태로 직접 처리
                    self.current_surround_active_ids = [
                        s_id for s_id in data if s_id != 0
                    ]
                    self._apply_styles()
                    LOGD(
                        f"SpeakerGridManager: Updated surround speakers: {self.current_surround_active_ids}"
                    )

        except Exception as e:
            LOGE(f"SpeakerGridManager: Error processing speaker grid update event: {e}")

    def setup_grid(self):
        """2x3 스피커 그리드 설정 - 라벨만 생성"""
        position_ids = [[8, 6, 9], [10, 12, 11]]

        label_style = """
            QLabel {
                min-height: 30px;
                min-width: 60px;
                qproperty-alignment: AlignCenter;
                color: black;
            }
        """

        for r in range(2):
            for c in range(3):
                pos_id = position_ids[r][c]
                label = self.create_widget(
                    QLabel,
                    f"position_label_{pos_id}",
                    UIElementGroup.ALWAYS_DISABLED,
                    "",
                )
                label.setStyleSheet(label_style)
                self.speaker_grid_layout.addWidget(label, r, c)
                if pos_id != -1:
                    self.position_labels[pos_id] = label

    def _apply_styles(self):
        """스타일 적용"""
        default_style = """
            QLabel {
                border: 1px solid black;
                min-height: 30px;
                min-width: 60px;
                qproperty-alignment: AlignCenter;
                background-color: white;
                color: black;
                border-radius: 8px;
            }
        """

        # 모든 라벨 리셋 - 코너 라벨도 기본 스타일을 유지하여 빈 공간이 보이지 않도록 함
        for pos_id, label in self.position_labels.items():
            label.setStyleSheet(default_style)
            label.setText("")

        # 위치별 스타일 적용
        for pos_id, label in self.position_labels.items():
            is_blue = pos_id == self.current_position_id
            is_green = pos_id in self.current_surround_active_ids

            if is_blue and is_green:
                label.setStyleSheet(
                    "QLabel { border: 1px solid black; min-height: 30px; min-width: 30px; "
                    "qproperty-alignment: AlignCenter; background-color: cyan; color: black; "
                    "border-radius: 8px; }"
                )
                label.setText("THIS")
            elif is_blue:
                label.setStyleSheet(
                    "QLabel { border: 1px solid black; min-height: 30px; min-width: 30px; "
                    "qproperty-alignment: AlignCenter; background-color: blue; color: white; "
                    "border-radius: 8px; }"
                )
                label.setText("THIS")
            elif is_green:
                label.setStyleSheet(
                    "QLabel { border: 1px solid black; min-height: 30px; min-width: 30px; "
                    "qproperty-alignment: AlignCenter; background-color: green; color: white; "
                    "border-radius: 8px; }"
                )
                label.setText("SPK")

    def _register_specific_event_handlers(self, event_manager):
        """구체적인 Event 핸들러 등록 로직 구현"""
        event_manager.register_event_handler(
            QSMonitorEventType.SPEAKER_GRID_UPDATED, self._on_speaker_grid_update
        )
        LOGD("SpeakerGridManager: Registered specific event handlers")

    def update_ui(self, data):
        """UI 업데이트 메서드 구현"""
        if isinstance(data, dict):
            update_type = data.get("update_type")
            if update_type == "speaker_remap":
                if data.get("data") and "position_id" in data.get("data"):
                    self.current_position_id = data.get("data").get("position_id")
                    self._apply_styles()
            elif update_type == "surround_speaker":
                if data.get("data") and isinstance(data.get("data"), list):
                    self.current_surround_active_ids = [
                        s_id for s_id in data.get("data") if s_id != 0
                    ]
                    self._apply_styles()

    def cleanup(self):
        """리소스 정리"""
        try:
            # 이벤트 구독 해제
            self.event_manager.unregister_event_handler(
                QSMonitorEventType.SPEAKER_GRID_UPDATED, self._on_speaker_grid_update
            )
            LOGD("SpeakerGridManager: Unregistered handler for SPEAKER_GRID_UPDATED")
        except Exception as e:
            LOGE(f"SpeakerGridManager: Error during cleanup: {e}")
