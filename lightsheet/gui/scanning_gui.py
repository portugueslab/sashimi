from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
)
from lightparam.gui import ParameterGui
from lightsheet.gui.waveform import WaveformWidget


class PlanarScanningWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_planar = ParameterGui(state.planar_setting)
        self.layout().addWidget(self.wid_planar)


class VolumeScanningWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_volume = ParameterGui(state.volume_setting)
        self.layout().addWidget(self.wid_volume)
        self.wid_wave = WaveformWidget(state.scanner.waveform_queue, timer)
        self.layout().addWidget(self.wid_wave)
