from sashimi.hardware.laser import CoboltLaser
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
)
from lightparam.gui import ParameterGui


class LaserControlWidget(QWidget):
    def __init__(self, laser: CoboltLaser, laser_settings, timer):
        super().__init__()

        self.laser = laser
        self.parameters = laser_settings

        self.main_layout = QHBoxLayout()

        self.lbl_text = QLabel("Laser ")

        self.btn_off = QPushButton("ON")
        self.btn_off.clicked.connect(self.toggle)

        self.main_layout.addWidget(self.lbl_text)
        self.main_layout.addWidget(self.btn_off)
        self.wid_settings = ParameterGui(self.parameters)
        self.main_layout.addWidget(self.wid_settings)

        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)
        self.laser_on = False
        self.previous_current = self.parameters.laser_power
        timer.timeout.connect(self.update_current)

    def update_current(self):
        if self.laser_on and self.previous_current != self.parameters.laser_power:
            self.laser.set_current(self.parameters.laser_power)
        self.previous_current = self.parameters.laser_power

    def toggle(self):
        self.laser_on = not self.laser_on
        if self.laser_on:
            self.btn_off.setText("OFF")
            self.laser.set_current(self.previous_current)
        else:
            self.btn_off.setText("ON")
            self.laser.set_current(0)
