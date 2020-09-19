from sashimi.hardware.lasers import AbstractLaser
from sashimi.state import LaserSettings
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
)
from lightparam.gui import ParameterGui


class LaserControlWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state

        self.main_layout = QHBoxLayout()

        self.lbl_text = QLabel("Laser")

        self.btn_off = QPushButton("ON")
        self.btn_off.clicked.connect(self.toggle)

        self.main_layout.addWidget(self.lbl_text)
        self.main_layout.addWidget(self.btn_off)
        self.wid_settings = ParameterGui(self.state.laser_settings)
        self.main_layout.addWidget(self.wid_settings)

        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)
        self.laser_on = False
        self.previous_current = self.state.laser_settings.laser_power
        timer.timeout.connect(self.update_current)

    def update_current(self):
        if self.laser_on and self.previous_current != self.state.laser_settings.laser_power:
            self.state.laser.current = self.state.laser_settings.laser_power
        self.previous_current = self.state.laser_settings.laser_power

    def toggle(self):
        self.laser_on = not self.laser_on
        if self.laser_on:
            self.btn_off.setText("OFF")
            self.state.laser.current = self.previous_current
        else:
            self.btn_off.setText("ON")
            self.state.laser.current = 0
