#!/usr/bin/env python3

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from QSUtils.QSLogger.config import QSLoggerConfig
from QSUtils.QSLogger.views.DeviceWindow import DeviceWindow
from QSUtils.UIFramework.base.BaseMainWindow import BaseMainWindow


class MainWindow(BaseMainWindow):
    """
    QSLogger 전용 메인 윈도우.
    공통 로직/UI는 BaseMainWindow가 담당하고, 여기서는 앱 설정 객체와 디바이스 윈도우 클래스를 지정하고
    추가적인 타일/스왑 기능 메뉴만 확장합니다.
    """

    def __init__(self, app_config: QSLoggerConfig):
        super().__init__(
            app_config=app_config,
            device_window_cls=DeviceWindow,
        )

        # QSLogger 전용 기능 설정
        app_config.setup_specific_features()

    def _setup_menu(self):
        # 공통 메뉴 구성
        super()._setup_menu()

        # 추가 Window 메뉴 액션들 삽입
        window_menu = self.menuBar().addMenu("Arrange")

        act_tile_horizontally = QAction("Tile Horizontally", self)
        act_tile_horizontally.triggered.connect(self.tile_sub_windows_horizontally)
        window_menu.addAction(act_tile_horizontally)

        act_tile_vertically = QAction("Tile Vertically", self)
        act_tile_vertically.triggered.connect(self.tile_sub_windows_vertically)
        window_menu.addAction(act_tile_vertically)

        window_menu.addSeparator()

        act_swap_horizontal = QAction("Swap Horizontal Positions", self)
        act_swap_horizontal.triggered.connect(self.swap_horizontal_positions)
        window_menu.addAction(act_swap_horizontal)

        act_swap_vertical = QAction("Swap Vertical Positions", self)
        act_swap_vertical.triggered.connect(self.swap_vertical_positions)
        window_menu.addAction(act_swap_vertical)

    # ----- 추가 배치 기능 -----
    def tile_sub_windows_horizontally(self):
        sub_windows = self.mdi_area.subWindowList()
        if len(sub_windows) == 0:
            return
        if len(sub_windows) == 1:
            sub_windows[0].showMaximized()
            return
        if len(sub_windows) == 2:
            mdi_area_width = self.mdi_area.width()
            mdi_area_height = self.mdi_area.height()
            window_width = mdi_area_width // 2
            window_height = mdi_area_height
            sub_windows[0].showNormal()
            sub_windows[0].setGeometry(0, 0, window_width, window_height)
            sub_windows[1].showNormal()
            sub_windows[1].setGeometry(window_width, 0, window_width, window_height)
            return
        self.mdi_area.tileSubWindows()

    def tile_sub_windows_vertically(self):
        sub_windows = self.mdi_area.subWindowList()
        if len(sub_windows) == 0:
            return
        if len(sub_windows) == 1:
            sub_windows[0].showMaximized()
            return
        if len(sub_windows) == 2:
            mdi_area_width = self.mdi_area.width()
            mdi_area_height = self.mdi_area.height()
            window_width = mdi_area_width
            window_height = mdi_area_height // 2
            sub_windows[0].showNormal()
            sub_windows[0].setGeometry(0, 0, window_width, window_height)
            sub_windows[1].showNormal()
            sub_windows[1].setGeometry(0, window_height, window_width, window_height)
            return
        self.mdi_area.tileSubWindows()

    def swap_horizontal_positions(self):
        sub_windows = self.mdi_area.subWindowList()
        if len(sub_windows) != 2:
            QMessageBox.information(
                self, "Swap Positions", "창이 2개일 때만 위치를 교환할 수 있습니다."
            )
            return
        pos1 = sub_windows[0].pos()
        pos2 = sub_windows[1].pos()
        size1 = sub_windows[0].size()
        size2 = sub_windows[1].size()
        sub_windows[0].setGeometry(pos2.x(), pos2.y(), size1.width(), size1.height())
        sub_windows[1].setGeometry(pos1.x(), pos1.y(), size2.width(), size2.height())

    def swap_vertical_positions(self):
        sub_windows = self.mdi_area.subWindowList()
        if len(sub_windows) != 2:
            QMessageBox.information(
                self, "Swap Positions", "창이 2개일 때만 위치를 교환할 수 있습니다."
            )
            return
        pos1 = sub_windows[0].pos()
        pos2 = sub_windows[1].pos()
        size1 = sub_windows[0].size()
        size2 = sub_windows[1].size()
        sub_windows[0].setGeometry(pos1.x(), pos2.y(), size1.width(), size1.height())
        sub_windows[1].setGeometry(pos2.x(), pos1.y(), size2.width(), size2.height())
