from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
)
from lightparam.gui import ParameterGui
from lightsheet.gui.waveform import WaveformWidget
from lightsheet.scanning import ExperimentPrepareState


class PlanarScanningWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_planar = ParameterGui(state.planar_setting)
        self.layout().addWidget(self.wid_planar)


STATE_TEXTS = {
    ExperimentPrepareState.NO_CAMERA: "Start recording",
    ExperimentPrepareState.NORMAL: "Prepare recording",
    ExperimentPrepareState.START: "Recording started",
}

class VolumeScanningWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_volume = ParameterGui(state.volume_setting)
        self.btn_start = QPushButton()
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.state.toggle_experiment_state)

        self.layout().addWidget(self.wid_volume)
        self.layout().addWidget(self.btn_start)
        self.wid_wave = WaveformWidget(state.scanner.waveform_queue, timer)
        self.layout().addWidget(self.wid_wave)

        self.updateBtnText()
        timer.timeout.connect(self.updateBtnText)

    def updateBtnText(self):
        self.btn_start.setText(STATE_TEXTS[self.state.experiment_state])
        if self.state.experiment_state == ExperimentPrepareState.NORMAL:
            self.btn_start.setChecked(False)
        else:
            self.btn_start.setChecked(True)
