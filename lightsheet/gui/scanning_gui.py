from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt5.QtCore import QTimer
from lightparam.gui import ParameterGui
from lightsheet.gui.waveform import WaveformWidget
from lightsheet.scanning import ExperimentPrepareState
from lightparam.param_qt import ParametrizedQt, Param

class ScopeAlignmentInfo(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name= "scope_alignment_info"
        self.waist_width = Param(6.5, (0.1, 100), unit="um")


class PlanarScanningWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_planar = ParameterGui(state.planar_setting)
        self.layout().addWidget(self.wid_planar)


STATE_TEXTS = {
    ExperimentPrepareState.PREPARED: "Start recording",
    ExperimentPrepareState.PREVIEW: "Prepare recording",
    ExperimentPrepareState.EXPERIMENT_STARTED: "Recording started. Press to abort",
    ExperimentPrepareState.ABORT: "Experiment aborted"
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
        self.btn_start.clicked.connect(self.state.toggle_experiment_state)

        self.scope_alignment = ScopeAlignmentInfo()

        self.wid_alignment = ParameterGui(self.scope_alignment)
        self.lbl_interplane_distance = QLabel()

        self.layout().addWidget(self.wid_volume)
        self.layout().addWidget(self.btn_start)
        self.layout().addWidget(self.wid_alignment)
        self.layout().addWidget(self.lbl_interplane_distance)
        self.wid_wave = WaveformWidget(state.scanner.waveform_queue, timer)
        self.layout().addWidget(self.wid_wave)

        self.timer_scope_info.start()

        self.updateBtnText()
        self.timer.timeout.connect(self.updateBtnText)

        self.timer_scope_info.timeout.connect(self.update_alignment)

    def updateBtnText(self):
        self.btn_start.setText(STATE_TEXTS[self.state.experiment_state])
        #if self.state.experiment_state == ExperimentPrepareState.PREVIEW or \
        #        self.state.experiment_state == ExperimentPrepareState.ABORTED:
        #    self.btn_start.setChecked(False)
        #if self.state.experiment_state == ExperimentPrepareState.PREPARED or \
        #        self.state.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED:
        #    self.btn_start.setChecked(True)

    def update_alignment(self):
        scan_width = self.state.volume_setting.scan_range[1] - self.state.volume_setting.scan_range[0]
        num_planes = self.state.volume_setting.n_planes - \
                 self.state.volume_setting.n_skip_start - self.state.volume_setting.n_skip_end
        plane_distance = scan_width / num_planes - self.scope_alignment.waist_width
        if plane_distance > 0:
            self.lbl_interplane_distance.setText(
                "With the current configuration, distance between planes is {:0.2f} um".format(plane_distance)
            )
        if plane_distance <= 0:
            self.lbl_interplane_distance.setText(
                "The current configuration covers the whole volume. Plane overlap is {:0.2f} um".format(-plane_distance)
            )
