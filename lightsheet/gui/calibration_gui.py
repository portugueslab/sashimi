from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QDockWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QFileDialog,
    QCheckBox,
)
from lightparam.gui import ParameterGui
from lightsheet.state import Calibration
import ctypes
import numpy as np


class CalibrationWidget(QWidget):
    def __init__(self, state, calibration_state: Calibration, timer: QTimer):
        super().__init__()
        self.state = state
        self.calibration_state = calibration_state
        self.setLayout(QVBoxLayout())
        self.wid_settings = ParameterGui(self.calibration_state.z_settings)
        self.layout().addWidget(self.wid_settings)
        self.btn_add_points = QPushButton("+")
        self.btn_add_points.clicked.connect(self.calibration_state.add_calibration_point)
        self.btn_rm_points = QPushButton("-")
        self.btn_rm_points.clicked.connect(self.calibration_state.remove_calibration_point)
        self.lbl_calibration = QLabel("")
        self.chk_noise_subtraction = QCheckBox()
        self.layout().addWidget(self.chk_noise_subtraction)
        self.layout().addWidget(self.btn_add_points)
        self.layout().addWidget(self.btn_rm_points)
        self.layout().addWidget(self.lbl_calibration)

        self.chk_noise_subtraction.clicked.connect(self.perform_noise_substraction)
        timer.timeout.connect(self.update_label)

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

    def perform_noise_substraction(self):
        if self.state.calibration_ref is None:
            self.state.laser.set_current(0)
            ctypes.windll.user32.MessageBoxW(
                0,
                "Turn off the lights. If you change camera settings (e.g. exposure) you will have to perform noise "
                "subtraction again",
                "Noise subtraction mode",
                0
            )
            calibration_set = []
            calibration_image = None
            while not calibration_image or len(calibration_set) < 10:
                current_image = self.state.get_image()
                if current_image:
                    calibration_set.append(current_image)
                    calibration_image = None
            self.state.calibration_ref = np.average(calibration_set)
            ctypes.windll.user32.MessageBoxW(
                0,
                "Noise subtraction completed"
                "Noise subtraction mode",
                0
            )
        else:
            self.state.calibration_ref = None
