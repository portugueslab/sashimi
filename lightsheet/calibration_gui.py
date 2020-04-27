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
from lightsheet.state import CalibrationState


class CalibrationWidget(QWidget):
    def __init__(self, calibration_state: CalibrationState):
        super().__init__()
        self.state = calibration_state
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(ParameterGui(self.state.z_settings))
        self.btn_add_points = QPushButton("+")
        self.btn_add_points.clicked.connect(self.state.add_calibration_point)
        self.btn_rm_points = QPushButton("-")
        self.btn_rm_points.clicked.connect(self.state.remove_calibration_point)
        self.lbl_calibration = QLabel("")
        self.layout().addWidget(self.btn_add_points)
        self.layout().addWidget(self.btn_rm_points)
        self.layout().addWidget(self.lbl_calibration)

    def update_label(self):
        self.lbl_calibration.setText(
            "\n".join(
                [
                    "piezo: {:0.2f} lat. galvo: {:0.2f} front. galvo {:0.2f}".format(
                        *pt
                    )
                    for pt in self.state.calibrations_points
                ]
                + (
                    ["not enough points"]
                    if self.state.calibration is None
                    else [
                        "offset: {:0.3f} amplitude {:0.3f}".format(*list(calib_row))
                        for calib_row in self.state.calibration
                    ]
                )
            )
        )


if __name__ == "__main__":
    app = QApplication([])
    st = CalibrationState()
    wid = CalibrationWidget(st)
    wid.show()
    timer = QTimer()
    timer.timeout.connect(wid.update_label)
    timer.start()
    app.exec()
