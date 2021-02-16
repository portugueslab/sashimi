from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QDockWidget, QTabWidget
from sashimi.gui.calibration_gui import CalibrationWidget
from sashimi.gui.scanning_gui import (
    PlanarScanningWidget,
    VolumeScanningWidget,
    SinglePlaneScanningWidget,
)
from sashimi.gui.light_source_gui import LightSourceWidget
from sashimi.gui.save_settings_gui import SavingSettingsWidget
from sashimi.gui.camera_gui import ViewingWidget, CameraSettingsWidget
from sashimi.gui.save_gui import SaveWidget
from sashimi.gui.status_bar import StatusBarWidget
from sashimi.gui.top_bar import TopWidget
from sashimi.state import State


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
    def __init__(self, st: State, style: str):
        super().__init__()
        self.st = st
        self.timer = QTimer()
        self.showMaximized()

        self.wid_settings_tree = SavingSettingsWidget(st)
        self.wid_settings_tree.sig_params_loaded.connect(self.refresh_param_values)

        self.wid_status = StatusWidget(st, self.timer)
        self.wid_display = ViewingWidget(st, self.timer, style)
        self.wid_save_options = SaveWidget(st, self.timer)
        self.wid_laser = LightSourceWidget(st, self.timer)
        self.wid_scan = PlanarScanningWidget(st)
        self.wid_camera = CameraSettingsWidget(st, self.wid_display, self.timer)
        self.wid_status_bar = StatusBarWidget(st, self.timer)
        self.toolbar = TopWidget(st, self.timer)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.setCentralWidget(self.wid_display)

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            DockedWidget(widget=self.wid_status, title="Mode"),
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_scan, title="Scanning settings"),
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_laser, title="Light source"),
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_camera, title="Camera settings"),
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_save_options, title="Saving"),
        )

        self.setStatusBar(self.wid_status_bar)

        self.st.camera_settings.sig_param_changed.connect(
            self.st.reset_noise_subtraction
        )
        # TODO also change the check box of the button without triggering

        self.timer.start()
        self.timer.timeout.connect(self.check_end_experiment)
        self.setup_menu_bar()

        self.refresh_param_values()

    def setup_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        load = file_menu.addAction("Load presets")
        save_settings = file_menu.addAction("Save presets")
        exit = file_menu.addAction("Exit")
        load.triggered.connect(self.wid_settings_tree.load)
        save_settings.triggered.connect(self.wid_settings_tree.save)
        exit.triggered.connect(self.close)

        edit_menu = menubar.addMenu("Edit")
        edit_config = edit_menu.addAction("Configure")
        edit_guide = edit_menu.addAction("Edit user guide")
        edit_guide.triggered.connect(self.wid_settings_tree.edit_guide)
        edit_config.triggered.connect(self.wid_settings_tree.edit_config)

        help_menu = menubar.addMenu("Help")
        instructions = help_menu.addAction("User guide")
        docs = help_menu.addAction("About")
        instructions.triggered.connect(self.wid_settings_tree.show_instructions)
        docs.triggered.connect(self.wid_settings_tree.open_docs)

    def closeEvent(self, a0) -> None:
        self.wid_settings_tree.conf_window.close()
        self.wid_settings_tree.guide_window.close()
        self.st.wrap_up()
        a0.accept()

    def refresh_param_values(self, omit_wid_camera=False):
        # TODO should be possible with lightparam, when it's implemented there remove here
        self.wid_laser.wid_settings.refresh_widgets()
        self.wid_scan.wid_planar.refresh_widgets()
        self.wid_status.wid_volume.wid_volume.refresh_widgets()
        self.wid_status.wid_calibration.refresh_widgets()
        self.wid_status.wid_single_plane.wid_singleplane.refresh_widgets()
        if not omit_wid_camera:
            self.wid_camera.wid_camera_settings.refresh_widgets()
            self.wid_camera.set_roi()
        self.wid_save_options.wid_save_options.refresh_widgets()
        self.wid_save_options.set_locationbutton()

    def check_end_experiment(self):
        if self.st.saver.saver_stopped_signal.is_set():
            self.st.end_experiment()
            if self.st.pause_after:
                self.wid_status.setCurrentIndex(0)
                self.wid_laser.btn_off.click()
            self.refresh_param_values(omit_wid_camera=True)
            self.toolbar.experiment_progress.hide()
            self.toolbar.lbl_experiment_progress.hide()
            self.st.saver.saver_stopped_signal.clear()


class StatusWidget(QTabWidget):
    def __init__(self, st: State, timer):
        super().__init__()

        self.state = st
        self.timer = timer
        self.scan_settings = self.state.status
        self.option_dict = {
            0: "Paused",
            1: "Calibration",
            2: "Planar",
            3: "Volume",
        }

        self.wid_paused = PausedWidget()
        self.wid_calibration = CalibrationWidget(st, st.calibration, self.timer)
        self.wid_single_plane = SinglePlaneScanningWidget(st)
        self.wid_volume = VolumeScanningWidget(st, self.timer)

        self.addTab(self.wid_paused, self.option_dict[0])
        self.addTab(self.wid_calibration, self.option_dict[1])
        self.addTab(self.wid_single_plane, self.option_dict[2])
        self.addTab(self.wid_volume, self.option_dict[3])

        # TODO: delete this line when single-plane scanning mode is implemented
        # self.setTabEnabled(2, False)

        self.currentChanged.connect(self.update_status)
        # Make sure pulses are displayed the first time we go to volumetric.
        self.currentChanged.connect(self.wid_volume.wid_wave.update_pulses)

    def update_status(self):
        self.state.status.scanning_state = self.option_dict[self.currentIndex()]


class PausedWidget(QWidget):
    def __init__(self):
        super().__init__()
