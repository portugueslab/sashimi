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
from lightsheet.calibration_gui import CalibrationWidget
from lightsheet.scanning_gui import PlanarScanningWidget
from lightsheet.state import CalibrationState

if __name__ == "__main__":
    app = QApplication([])
    st = CalibrationState()

    timer = QTimer()
    wid_calib = CalibrationWidget(st, timer)
    wid_scan = PlanarScanningWidget(st, timer)

    timer.start()
    app.exec()
