from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QRadioButton,
    QHBoxLayout,
    QVBoxLayout,
    QMainWindow,
    QDockWidget
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

        self.wid_status = ParameterGui(st.status)
        self.st.status.sig_param_changed.connect(self.refresh_visible)

        self.wid_save_settings = SavingSettingsWidget(st)
        self.wid_save_settings.sig_params_loaded.connect(self.refresh_param_values)

        self.wid_display = ViewingWidget(st, self.timer)
        self.wid_save_options = SaveWidget(st, self.timer)
        self.wid_laser = LaserControlWidget(st.laser, st.laser_settings, self.timer)
        self.wid_scan = PlanarScanningWidget(st)
        self.wid_calib = CalibrationWidget(st.calibration, self.timer)
        self.wid_single_plane = SinglePlaneScanningWidget(st)
        self.wid_volume = VolumeScanningWidget(st, self.timer)

        self.setCentralWidget(self.wid_display)

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_status, title="Mode")
        )
        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_laser, title="Laser control")
        )
        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_scan, title="Scanning settings")
        )
        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_calib, title="Calibration")
        )
        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_single_plane, title="Single plane")
        )
        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_volume, title="Volume")
        )
        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_save_options, title="Saving options")
        )
        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_save_settings, title="Parameter tree")
        )

        self.refresh_visible()
        self.timer.start()

    def refresh_visible(self):
        if self.st.status.scanning_state == "Volume":
            self.wid_calib.hide()
            self.wid_single_plane.hide()
            self.wid_volume.show()
        elif self.st.status.scanning_state == "Calibration":
            self.wid_calib.show()
            self.wid_single_plane.hide()
            self.wid_volume.hide()
        elif self.st.status.scanning_state == "Paused":
            self.wid_calib.hide()
            self.wid_single_plane.hide()
            self.wid_volume.hide()
        elif self.st.status.scanning_state == "Planar":
            self.wid_calib.hide()
            self.wid_single_plane.show()
            self.wid_volume.hide()

    def closeEvent(self, a0) -> None:
        self.st.wrap_up()
        a0.accept()

    def refresh_param_values(self):
        # TODO should be possible with lightparam, when it's implemented there remove here
        self.wid_laser.wid_settings.refresh_widgets()
        self.wid_scan.wid_planar.refresh_widgets()
        self.wid_calib.refresh_widgets()
        self.wid_volume.wid_volume.refresh_widgets()
        self.wid_display.wid_camera_properties.refresh_widgets()
        self.wid_display.wid_display_settings.refresh_widgets()
        self.wid_save_options.wid_save_options.refresh_widgets()
