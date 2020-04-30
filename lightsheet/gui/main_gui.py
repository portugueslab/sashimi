from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QRadioButton,
    QHBoxLayout,
    QVBoxLayout,
)
from lightsheet.gui.calibration_gui import CalibrationWidget
from lightsheet.gui.scanning_gui import PlanarScanningWidget, VolumeScanningWidget
from lightsheet.gui.laser_gui import LaserControlWidget
from lightsheet.gui.save_settings_gui import SavingWidget
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

        self.wid_save = SavingWidget(st)
        self.left_layout.addWidget(self.wid_save)
        self.wid_save.sig_params_loaded.connect(self.refresh_param_values)

        self.full_layout.addWidget(self.wid_status)

        self.control_layout = QHBoxLayout()
        self.full_layout.addLayout(self.control_layout)

        self.wid_laser = LaserControlWidget(st.laser, st.laser_settings, self.timer)
        self.wid_scan = PlanarScanningWidget(st)
        self.wid_calib = CalibrationWidget(st.calibration, self.timer)
        self.wid_volume = VolumeScanningWidget(st, self.timer)

        self.left_layout.addWidget(self.wid_laser)
        self.control_layout.addLayout(self.left_layout)
        self.control_layout.addWidget(self.wid_scan)
        self.control_layout.addWidget(self.wid_calib)
        self.control_layout.addWidget(self.wid_volume)

        self.setLayout(self.full_layout)
        self.refresh_visible()
        self.timer.start()

    def refresh_visible(self):
        if self.st.status.scanning_state == "Volume":
            self.wid_calib.hide()
            self.wid_volume.show()
        elif self.st.status.scanning_state == "Calibration":
            self.wid_calib.show()
            self.wid_volume.hide()
        elif self.st.status.scanning_state == "Paused":
            self.wid_calib.hide()
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


if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    st = State()
    wid = ContainerWidget(st)
    wid.show()
    app.exec()
