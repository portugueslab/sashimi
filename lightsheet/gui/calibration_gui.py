from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QMessageBox,
    QWidget,
    QMainWindow,
    QDockWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QGridLayout,
    QCheckBox,
)
from lightparam.gui import ParameterGui
from lightsheet.state import Calibration
import ctypes
import numpy as np
from lightparam.param_qt import ParametrizedQt
from lightparam import Param


class NoiseSubtractionSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "Average of n frames"
        self.average_n_frames = Param(50, (5, 500))


class CalibrationWidget(QWidget):
    def __init__(self, state, calibration_state: Calibration, timer: QTimer):
        super().__init__()
        self.state = state
        self.calibration_state = calibration_state
        self.timer = timer
        self.wid_settings = ParameterGui(self.calibration_state.z_settings)
        self.btn_add_points = QPushButton("+")
        self.btn_add_points.clicked.connect(self.calibration_state.add_calibration_point)
        self.btn_rm_points = QPushButton("-")
        self.btn_rm_points.clicked.connect(self.calibration_state.remove_calibration_point)
        self.lbl_calibration = QLabel("")
        self.chk_noise_subtraction = QCheckBox()
        self.chk_noise_subtraction.setText("Enable noise subtraction")
        self.param_n_noise_subtraction = NoiseSubtractionSettings()
        self.wid_n_noise_subtraction = ParameterGui(self.param_n_noise_subtraction)

        self.main_layout = QVBoxLayout()

        self.noise_layout = QHBoxLayout()
        self.noise_layout.addWidget(self.chk_noise_subtraction)
        self.noise_layout.addWidget(self.wid_n_noise_subtraction)

        self.main_layout.addWidget(self.wid_settings)
        self.main_layout.addWidget(self.btn_add_points)
        self.main_layout.addWidget(self.btn_rm_points)
        self.main_layout.addWidget(self.lbl_calibration)
        self.main_layout.addLayout(self.noise_layout)

        self.setLayout(self.main_layout)

        self.dialog_box = QMessageBox()
        self.dialog_button = self.dialog_box.addButton(self.dialog_box.Ok)

        self.chk_noise_subtraction.clicked.connect(self.set_noise_subtraction_mode)
        self.timer.timeout.connect(self.update_label)

    def uncheck_noise(self):
        if self.chk_noise_subtraction.isChecked():
            self.chk_noise_subtraction.click()
            self.show_dialog_box(deactivated=True)

    def refresh_widgets(self):
        self.wid_settings.refresh_widgets()
        self.update_label()

    def update_label(self):
        self.lbl_calibration.setText(
            "\n".join(
                [
                    "piezo: {:0.2f} lat. galvo: {:0.2f} front. galvo {:0.2f}".format(
                        *pt
                    )
                    for pt in self.calibration_state.calibrations_points
                ]
                + (
                    ["not enough points"]
                    if self.calibration_state.calibration is None
                    else [
                        "offset: {:0.5f} amplitude {:0.5f}".format(*list(calib_row))
                        for calib_row in self.calibration_state.calibration
                    ]
                )
            )
        )

    def set_noise_subtraction_mode(self):
        if self.state.calibration_ref is None:
            self.show_dialog_box(finished=False)
        else:
            self.state.calibration_ref = None
            self.dialog_button.click()

    def show_dialog_box(self, finished=True, deactivated=False):
        self.dialog_box.setIcon(QMessageBox.Information)
        self.dialog_box.setWindowTitle("Noise subtraction mode")
        self.dialog_box.setText(
            "Turn off the lights. \n\n You will have to perform noise subtraction again if camera settings change "
        )
        if deactivated:
            self.dialog_box.setText("Noise subtraction has been deactivated")
        elif not finished :
            self.dialog_button.clicked.connect(self.perform_noise_subtraction)
        else:
            self.dialog_button.clicked.disconnect(self.perform_noise_subtraction)
            self.dialog_box.setText("Noise subtraction completed")
        self.dialog_box.show()

    def perform_noise_subtraction(self):
        self.state.obtain_signal_average(n_images=self.param_n_noise_subtraction.average_n_frames)
        self.show_dialog_box(finished=True)
