from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QCheckBox,
    QMessageBox,
)
from PyQt5.QtCore import QTimer
from lightparam.gui import ParameterGui
from lightparam.gui.collapsible_widget import CollapsibleWidget
from sashimi.gui.waveform_gui import WaveformWidget
from sashimi.processes.scanloops import ExperimentPrepareState


class PlanarScanningWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_planar = ParameterGui(state.planar_setting)
        self.layout().addWidget(self.wid_planar)


STATE_TEXTS = {
    ExperimentPrepareState.NO_TRIGGER: "Start recording",
    ExperimentPrepareState.PREVIEW: "Start recording",
    ExperimentPrepareState.EXPERIMENT_STARTED: "Recording started. Press to abort",
}


class SinglePlaneScanningWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_singleplane = ParameterGui(state.single_plane_settings)
        self.layout().addWidget(self.wid_singleplane)


class VolumeScanningWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.timer = timer
        self.setLayout(QVBoxLayout())
        self.timer_scope_info = QTimer()
        self.timer_scope_info.setInterval(500)
        self.wid_volume = ParameterGui(state.volume_setting)
        self.btn_start = QPushButton()
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.change_experiment_state)
        self.chk_pause = QCheckBox("Pause after experiment")

        self.lbl_interplane_distance = QLabel()
        self.lbl_interplane_distance.setStyleSheet("color: yellow")

        self.wid_wave = WaveformWidget(timer=self.timer, state=self.state)
        self.wid_collapsible_wave = CollapsibleWidget(
            child=self.wid_wave, name="Piezo impulse-response waveform"
        )
        self.wid_collapsible_wave.toggle_collapse()

        self.overwrite_dialog = QMessageBox()
        self.btn_overwrite_ok = self.overwrite_dialog.addButton(
            self.overwrite_dialog.Ok
        )
        self.btn_overwrite_abort = self.overwrite_dialog.addButton(
            self.overwrite_dialog.Abort
        )

        self.layout().addWidget(self.wid_volume)
        self.layout().addWidget(self.btn_start)
        self.layout().addWidget(self.chk_pause)
        self.layout().addWidget(self.lbl_interplane_distance)
        self.layout().addWidget(self.wid_collapsible_wave)

        self.timer_scope_info.start()

        self.updateBtnText()
        self.timer.timeout.connect(self.updateBtnText)

        self.chk_pause.clicked.connect(self.change_pause_status)
        self.btn_overwrite_ok.clicked.connect(self.state.start_experiment)

        self.chk_pause.click()

    def updateBtnText(self):
        self.btn_start.setText(STATE_TEXTS[self.state.experiment_state])
        if self.state.experiment_state == ExperimentPrepareState.PREVIEW:
            self.btn_start.setChecked(False)
        if (
            self.state.experiment_state == ExperimentPrepareState.NO_TRIGGER
            or self.state.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED
        ):
            self.btn_start.setChecked(True)

    def change_pause_status(self):
        self.state.pause_after = self.chk_pause.isChecked()

    def change_experiment_state(self):
        if self.state.is_saving_event.is_set():
            # Here what happens if experiment is aborted
            self.state.end_experiment()
        else:
            if self.state.save_settings.overwrite_save_folder == 1:
                self.overwrite_alert_popup()
            else:
                self.state.start_experiment()

    def overwrite_alert_popup(self):
        self.overwrite_dialog.setIcon(QMessageBox.Warning)
        self.overwrite_dialog.setWindowTitle("Overwrite alert!")
        self.overwrite_dialog.setText(
            "You are overwriting an existing folder with data. \n\n "
            "Press ok to start the experiment anyway or abort to change saving folder."
        )
        self.overwrite_dialog.show()
