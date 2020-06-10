from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QRadioButton,
    QHBoxLayout,
    QVBoxLayout,
    QMainWindow,
    QDockWidget,
    QTabWidget
)
from lightsheet.gui.calibration_gui import CalibrationWidget
from lightsheet.gui.scanning_gui import PlanarScanningWidget, VolumeScanningWidget, SinglePlaneScanningWidget
from lightsheet.gui.laser_gui import LaserControlWidget
from lightsheet.gui.save_settings_gui import SavingSettingsWidget
from lightsheet.gui.camera_gui import ViewingWidget
from lightsheet.gui.save_gui import SaveWidget
from lightsheet.state import State
from lightparam import Param
from lightparam.gui import ParameterGui
import qdarkstyle


class DockedWidget(QDockWidget):
    def __init__(self, widget=None, layout=None, title=""):
        super().__init__()
        if widget is not None:
            self.setWidget(widget)
        else:
            self.setWidget(QWidget())
            self.widget().setLayout(layout)
        if title != "":
            self.setWindowTitle(title)


class ContainerWidget(QMainWindow):
    def __init__(self, st: State):
        super().__init__()
        self.st = st
        self.timer = QTimer()

        self.wid_settings_tree = SavingSettingsWidget(st)
        self.wid_settings_tree.sig_params_loaded.connect(self.refresh_param_values)

        self.wid_status = StatusWidget(st)
        self.wid_display = ViewingWidget(st, self.timer)
        self.wid_save_options = SaveWidget(st, self.timer)
        self.wid_laser = LaserControlWidget(st.laser, st.laser_settings, self.timer)
        self.wid_scan = PlanarScanningWidget(st)

        self.addDockWidget(
            Qt.TopDockWidgetArea,
            DockedWidget(widget=self.wid_status, title="Mode")
        )

        # self.layout().addWidget(self.wid_status)

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_laser, title="Laser control")
        )
        self.addDockWidget(
            Qt.BottomDockWidgetArea,
            DockedWidget(widget=self.wid_scan, title="Scanning settings")
        )
        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_save_options, title="Saving options")
        )
        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_settings_tree, title="Parameter tree")
        )

        self.timer.start()

    def closeEvent(self, a0) -> None:
        self.st.wrap_up()
        a0.accept()

    def refresh_param_values(self):
        # TODO should be possible with lightparam, when it's implemented there remove here
        self.wid_laser.wid_settings.refresh_widgets()
        self.wid_scan.wid_planar.refresh_widgets()
        self.wid_status.wid_volume.wid_volume.refresh_widgets()
        self.wid_status.wid_calibration.refresh_widgets()
        self.wid_status.wid_single_plane.wid_singleplane.refresh_widgets()
        self.wid_display.wid_camera_properties.refresh_widgets()
        self.wid_display.wid_display_settings.refresh_widgets()
        self.wid_save_options.wid_save_options.refresh_widgets()


class StatusWidget(QTabWidget):
    def __init__(self, st: State):
        super().__init__()

        self.state = st
        self.scan_settings = self.state.status
        self.option_dict = {0: "Paused", 1: "Calibration", 2: "Planar", 3: "Volume"}

        self.wid_paused = PausedWidget()
        self.wid_calibration = CalibrationWidget(st.calibration, self.timer)
        self.wid_single_plane = SinglePlaneScanningWidget(st)
        self.wid_volume = VolumeScanningWidget(st, self.timer)

        self.addTab(self.wid_paused, self.option_dict[0])
        self.addTab(self.wid_calibration, self.option_dict[1])
        self.addTab(self.wid_single_plane, self.option_dict[2])
        self.addTab(self.wid_volume, self.option_dict[3])

        self.currentChanged.connect(self.update_state)

    def update_status(self):
        self.state.status.scanning_state = self.option_dict[self.currentIndex()]


class PausedWidget(QWidget):
    def __init__(self):
        super().__init__()
