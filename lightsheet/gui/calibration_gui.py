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
from lightparam.param_qt import ParametrizedQt
from lightparam import Param


class NoiseSubtractionSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "Average of n frames"
        self.n_frames_average_noise = Param(50, (5, 500))


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
        self.param_n_noise_subtraction = NoiseSubtractionSettings()
        self.wid_n_noise_subtraction = ParameterGui(self.param_n_noise_subtraction)
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

    def set_noise_subtraction_mode(self):
        '''
        Substracts the average noise of n_images to all the acquired ones both for display and saving
        '''
        if self.state.calibration_ref:
            self.show_dialog_box(finished=False)
            self.state.obtain_signal_average(n_images=self.wid_n_noise_subtraction.n_frames_average_noise)
            while True:
                if self.state.calibration_ref is not None:
                    break
            self.show_dialog_box(finished=True)

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
