from QSUtils.QSMonitor.core.config import QSMonitorConfig
from QSUtils.QSMonitor.ui.DeviceWindow import DeviceWindow
from QSUtils.UIFramework.base.BaseMainWindow import BaseMainWindow


class MainWindow(BaseMainWindow):
    """
    QSMonitor 전용 메인 윈도우.
    공통 로직/UI는 BaseMainWindow가 담당하고, 여기서는 앱 설정 객체와 디바이스 윈도우 클래스를 지정합니다.
    """

    def __init__(self, app_config: QSMonitorConfig):
        super().__init__(
            app_config=app_config,
            device_window_cls=DeviceWindow,
        )

        # QSMonitor 전용 기능 설정
        app_config.setup_specific_features()
