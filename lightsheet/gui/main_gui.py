from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QMainWindow,
    QDockWidget,
    QTabWidget
)
from lightsheet.gui.calibration_gui import CalibrationWidget
from lightsheet.gui.scanning_gui import PlanarScanningWidget, VolumeScanningWidget, SinglePlaneScanningWidget
from lightsheet.gui.laser_gui import LaserControlWidget
from lightsheet.gui.save_settings_gui import SavingSettingsWidget
from lightsheet.gui.camera_gui import ViewingWidget, CameraSettingsContainerWidget
from lightsheet.gui.save_gui import SaveWidget
from lightsheet.state import State


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


class MainWindow(QMainWindow):
    def __init__(self, st: State):
        super().__init__()
        self.st = st
        self.timer = QTimer()
        self.resize(1800, 900)

        self.wid_settings_tree = SavingSettingsWidget(st)
        self.wid_settings_tree.sig_params_loaded.connect(self.refresh_param_values)

        self.wid_status = StatusWidget(st, self.timer)
        self.wid_display = ViewingWidget(st, self.timer)
        self.wid_save_options = SaveWidget(st, self.timer)
        self.wid_laser = LaserControlWidget(st.laser, st.laser_settings, self.timer)
        self.wid_scan = PlanarScanningWidget(st)
        self.wid_camera = CameraSettingsContainerWidget(st, self.wid_display.roi, self.timer)

        self.setCentralWidget(self.wid_display)

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_status, title="Mode")
        )

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_scan, title="Scanning settings")
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_laser, title="Laser control")
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_camera, title="Camera settings")
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_save_options, title="Saving")
        )
        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_settings_tree, title="Metadata")
        )

        self.st.camera_settings.sig_param_changed.connect(self.wid_status.wid_calibration.uncheck_noise)

        self.timer.start()
        self.timer.timeout.connect(self.check_end_experiment)

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
        self.wid_display.wid_display_settings.refresh_widgets()
        self.wid_camera.wid_camera_settings.refresh_widgets()
        self.wid_save_options.wid_save_options.refresh_widgets()
        self.wid_camera.set_roi()
        self.wid_save_options.set_locationbutton()

    def check_end_experiment(self):
        if self.st.saver.saver_stopped_signal.is_set():
            self.st.end_experiment()
            self.st.saver.saver_stopped_signal.clear()
            if self.st.pause_after:
                self.wid_status.setCurrentIndex(0)
                self.st.laser.set_current(0)
                self.refresh_param_values()


class StatusWidget(QTabWidget):
    def __init__(self, st: State, timer):
        super().__init__()

        self.state = st
        self.timer = timer
        self.scan_settings = self.state.status
        self.option_dict = {0: "Paused", 1: "Calibration", 2: "Planar", 3: "Volume"}

        self.wid_paused = PausedWidget()
        self.wid_calibration = CalibrationWidget(st, st.calibration, self.timer)
        self.wid_single_plane = SinglePlaneScanningWidget(st)
        self.wid_volume = VolumeScanningWidget(st, self.timer)

        self.addTab(self.wid_paused, self.option_dict[0])
        self.addTab(self.wid_calibration, self.option_dict[1])
        self.addTab(self.wid_single_plane, self.option_dict[2])
        self.addTab(self.wid_volume, self.option_dict[3])

        self.currentChanged.connect(self.update_status)

    def update_status(self):
        self.state.status.scanning_state = self.option_dict[self.currentIndex()]


class PausedWidget(QWidget):
    def __init__(self):
        super().__init__()

