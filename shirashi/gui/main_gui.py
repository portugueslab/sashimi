from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QDockWidget, QTabWidget
from shirashi.gui.preview_gui import PreviewWidget
from shirashi.gui.experiment_gui import (
    ExperimentWidget,
    TBDWidget,
)
from shirashi.gui.save_settings_gui import SavingSettingsWidget
from shirashi.gui.camera_gui import ViewingWidget, CameraSettingsContainerWidget
from shirashi.gui.save_gui import SaveWidget
from shirashi.state import State


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
        self.wid_camera = CameraSettingsContainerWidget(
            st, self.timer
        )

        self.setCentralWidget(self.wid_display)

        self.addDockWidget(
            Qt.LeftDockWidgetArea, DockedWidget(widget=self.wid_status, title="Mode"),
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_camera, title="Camera settings"),
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_save_options, title="Saving"),
        )
        self.addDockWidget(
            Qt.RightDockWidgetArea,
            DockedWidget(widget=self.wid_settings_tree, title="Metadata"),
        )

        self.timer.start()
        self.timer.timeout.connect(self.check_end_experiment)

    def closeEvent(self, a0) -> None:
        self.st.wrap_up()
        a0.accept()

    def refresh_param_values(self, omit_wid_camera=False):
        # TODO should be possible with lightparam, when it's implemented there remove here
        self.wid_status.wid_preview.refresh_widgets()
        self.wid_status.wid_tbd.refresh_widgets()
        self.wid_display.wid_display_settings.refresh_widgets()
        if not omit_wid_camera:
            self.wid_camera.wid_camera_settings.refresh_widgets()
        self.wid_save_options.wid_save_options.refresh_widgets()
        self.wid_save_options.set_locationbutton()

    def check_end_experiment(self):
        if self.st.saver.saver_stopped_signal.is_set():
            self.st.toggle_experiment_state()
            if self.st.pause_after:
                self.wid_status.setCurrentIndex(0)
            self.refresh_param_values(omit_wid_camera=True)
            self.wid_display.experiment_progress.hide()
            self.wid_display.lbl_experiment_progress.hide()
            self.st.saver.saver_stopped_signal.clear()


class StatusWidget(QTabWidget):
    def __init__(self, st: State, timer):
        super().__init__()

        self.state = st
        self.timer = timer
        self.scan_settings = self.state.status
        self.option_dict = {
            0: "Paused",
            1: "Preview",
            2: "TBD",
            3: "Experiment",
        }

        self.wid_paused = PausedWidget()
        self.wid_preview = PreviewWidget(st, st.preview, self.timer)
        self.wid_tbd = TBDWidget(st)
        self.wid_exp = ExperimentWidget(st, self.timer)

        self.addTab(self.wid_paused, self.option_dict[0])
        self.addTab(self.wid_preview, self.option_dict[1])
        self.addTab(self.wid_tbd, self.option_dict[2])
        self.addTab(self.wid_exp, self.option_dict[3])

        self.currentChanged.connect(self.update_status)

    def update_status(self):
        self.state.status.scanning_state = self.option_dict[self.currentIndex()]


class PausedWidget(QWidget):
    def __init__(self):
        super().__init__()
