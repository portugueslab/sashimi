from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QRadioButton,
    QHBoxLayout,
    QVBoxLayout,
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


class ContainerWidget(QWidget):
    def __init__(self, st: State):
        super().__init__()
        self.st = st
        self.timer = QTimer()

        self.full_layout = QVBoxLayout()
        self.wid_status = ParameterGui(st.status)
        self.st.status.sig_param_changed.connect(self.refresh_visible)

        self.left_layout = QVBoxLayout()

        self.wid_save_settings = SavingSettingsWidget(st)
        self.left_layout.addWidget(self.wid_save_settings)
        self.wid_save_settings.sig_params_loaded.connect(self.refresh_param_values)

        self.full_layout.addWidget(self.wid_status)

        self.control_layout = QHBoxLayout()
        self.full_layout.addLayout(self.control_layout)

        self.wid_display = ViewingWidget(st, self.timer)
        self.wid_save_options = SaveWidget(st, self.timer)
        self.wid_laser = LaserControlWidget(st.laser, st.laser_settings, self.timer)
        self.wid_scan = PlanarScanningWidget(st)
        self.wid_calib = CalibrationWidget(st.calibration, self.timer)
        self.wid_single_plane = SinglePlaneScanningWidget(st)
        self.wid_volume = VolumeScanningWidget(st, self.timer)

        self.left_layout.addWidget(self.wid_laser)
        self.control_layout.addLayout(self.left_layout)
        self.control_layout.addWidget(self.wid_scan)
        self.control_layout.addWidget(self.wid_calib)
        self.control_layout.addWidget(self.wid_single_plane)
        self.control_layout.addWidget(self.wid_volume)
        self.full_layout.addWidget(self.wid_display)
        self.full_layout.addWidget(self.wid_save_options)

        self.setLayout(self.full_layout)
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
