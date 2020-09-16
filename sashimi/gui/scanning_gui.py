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
from sashimi.hardware.scanning.scanloops import ExperimentPrepareState


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

        self.wid_alignment = ParameterGui(self.state.scope_alignment_info)
        self.lbl_interplane_distance = QLabel()
        self.lbl_interplane_distance.setStyleSheet("color: yellow")

        self.wid_wave = WaveformWidget(timer=self.timer, state=self.state)
        self.wid_collapsible_wave = CollapsibleWidget(
            child=self.wid_wave, name="Piezo impulse-response waveform"
        )
        self.wid_collapsible_wave.toggle_collapse()

        self.dialog_box = QMessageBox()
        self.dialog_ok_button = self.dialog_box.addButton(self.dialog_box.Ok)
        self.dialog_abort_button = self.dialog_box.addButton(self.dialog_box.Abort)
        self.override_overwrite = False

        self.layout().addWidget(self.wid_volume)
        self.layout().addWidget(self.btn_start)
        self.layout().addWidget(self.chk_pause)
        self.layout().addWidget(self.wid_alignment)
        self.layout().addWidget(self.lbl_interplane_distance)
        self.layout().addWidget(self.wid_collapsible_wave)

        self.timer_scope_info.start()

        self.updateBtnText()
        self.timer.timeout.connect(self.updateBtnText)

        self.timer_scope_info.timeout.connect(self.update_alignment)
        self.chk_pause.clicked.connect(self.change_pause_status)
        self.dialog_ok_button.clicked.connect(self.overwrite_anyway)

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

    def update_alignment(self):
        scan_width = (
            self.state.volume_setting.scan_range[1]
            - self.state.volume_setting.scan_range[0]
        )
        num_planes = (
            self.state.volume_setting.n_planes
            - self.state.volume_setting.n_skip_start
            - self.state.volume_setting.n_skip_end
        )
        plane_distance = (
            scan_width / num_planes - self.state.scope_alignment_info.waist_width
        )
        if plane_distance > 0:
            self.lbl_interplane_distance.setText(
                "With the current configuration, distance between planes is {:0.2f} um".format(
                    plane_distance
                )
            )
        if plane_distance <= 0:
            self.lbl_interplane_distance.setText(
                "The current configuration covers the whole volume. Plane overlap is {:0.2f} um".format(
                    -plane_distance
                )
            )

    def change_pause_status(self):
        self.state.pause_after = self.chk_pause.isChecked()

    def change_experiment_state(self):
        if self.state.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED:
            # Here what happens if experiment is aborted
            self.state.saver.saving_signal.clear()
        elif (
            self.state.save_settings.overwrite_save_folder == 1
            and not self.override_overwrite
        ):
            self.overwrite_alert_popup()
            self.override_overwrite = False
        else:
            self.state.toggle_experiment_state()

    def overwrite_alert_popup(self):
        self.dialog_box.setIcon(QMessageBox.Warning)
        self.dialog_box.setWindowTitle("Overwrite alert!")
        self.dialog_box.setText(
            "You are overwriting an existing folder with data. \n\n "
            "Press ok to start the experiment anyway or abort to change saving folder."
        )
        self.dialog_box.show()

    def overwrite_anyway(self):
        self.override_overwrite = True
        self.change_experiment_state()
