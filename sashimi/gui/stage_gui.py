from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
)
from lightparam.gui import ParameterGui



class StageMotorWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.wid_settings = ParameterGui(state.stage_setting)
        self.layout().addWidget(self.wid_settings)

