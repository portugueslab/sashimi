from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QPushButton
)
import pyqtgraph as pg
import qdarkstyle
from lightparam.gui import ParameterGui
from lightparam.param_qt import ParametrizedQt
from lightparam import Param
import time
import numpy as np


class DisplaySettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "display_settings"
        self.replay_rate = Param(5, (1, 10))


class ViewingWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()

        self.state = state
        self.timer = timer
        self.refresh_timer = QTimer()
        self.setLayout(QVBoxLayout())

        self.image_viewer = pg.ImageView()
        self.image_viewer.ui.roiBtn.hide()
        self.image_viewer.ui.menuBtn.hide()

        self.display_settings = DisplaySettings()

        # FIXME: Camera properties parameters --> Camera API object

        self.wid_camera_properties = ParameterGui(self.state.camera_properties)
        self.wid_display_settings = ParameterGui(self.display_settings)

        # TODO: This button is only for debugging purposes. It will be triggered with start of adquisition
        self.save_button = QPushButton("Start saving")

        self.layout().addWidget(self.image_viewer)
        self.layout().addWidget(self.wid_display_settings)
        self.layout().addWidget(self.wid_camera_properties)
        self.layout().addWidget(self.save_button)
        self.is_first_image = True
        self.refresh_display = True

        # ms for display clock. Currently 5 fps replay
        self.refresh_timer.start(int(1000/self.display_settings.replay_rate))

        self.timer.timeout.connect(self.refresh)
        self.refresh_timer.timeout.connect(self.display_new_image)
        self.save_button.clicked.connect(self.toggle)
        self.display_settings.sig_param_changed.connect(self.update_replay_rate)

    def update_replay_rate(self):
        self.refresh_timer.setInterval(int(1000/self.display_settings.replay_rate))

    def toggle(self):
        self.state.saver.saving_signal.set()

    def refresh(self) -> None:
        current_image = self.state.get_image()
        if current_image is None:
            return

        # FIXME: I broke in tears when camera params change
        if self.refresh_display:
            self.image_viewer.setImage(
                current_image,
                autoLevels=self.is_first_image,
                autoRange=self.is_first_image,
                autoHistogramRange=self.is_first_image,
            )
            self.is_first_image = False
            self.refresh_display = False

    def display_new_image(self):
        self.refresh_display = True

    # TODO: Remove this function if we can do everything with lightparam
    def update_property(self):
        pass
