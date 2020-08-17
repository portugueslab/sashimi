from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
)
from shirashi.state import Preview
from lightparam.param_qt import ParametrizedQt
from lightparam import Param


class NoiseSubtractionSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "Average of n frames"
        self.average_n_frames = Param(50, (5, 500))


class PreviewWidget(QWidget):
    def __init__(self, state, preview_state: Preview, timer: QTimer):
        super().__init__()
        self.state = state
        self.preview_state = preview_state
        self.timer = timer

    def refresh_widgets(self):
        pass

