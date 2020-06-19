from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QMessageBox,
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

    def perform_noise_substraction(self, n_images=10, dtype=np.uint16):
        '''
        Substracts the average noise of n_images to all the acquired ones both for display and saving
        '''
        if self.state.calibration_ref is None:
            current_laser = self.state.laser_settings.laser_power
            self.state.laser.set_current(0)
            self.show_dialog_box(finished=False)
            calibration_image = None
            n_image = 0
            while not calibration_image or n_image < n_images:
                current_image = self.state.get_image()
                if current_image:
                    if n_image == 0:
                        calibration_set = np.empty(shape=(n_images, *current_image.shape), dtype=dtype)
                    calibration_set[n_image, ...] = current_image
                    n_image += 1
                    calibration_image = None
            self.state.calibration_ref = np.average(calibration_set, axis=0)
            self.state.calibration_ref = self.state.calibration_ref.astype(dtype=dtype)
            self.show_dialog_box(finished=True)
            self.state.laser.set_current(current_laser)
        else:
            self.state.calibration_ref = None

    def show_dialog_box(self, finished):
        dialog_box = QMessageBox()
        dialog_box.setIcon(QMessageBox.Information)
        dialog_box.setWindowTitle("Noise subtraction mode")
        dialog_box.setText(
            "Turn off the lights. If you change camera settings (e.g. exposure) you will have to perform noise "
            "subtraction again"
        )
        if finished:
            dialog_box.setText("Noise subtraction completed")
        dialog_box.setStandardButtons(QMessageBox.ok)
