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
import time
import numpy as np


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

        self.wid_camera_properties = ParameterGui(self.state.camera_properties)

        # TODO: This button is only for debugging purposes. It will be triggered with start of adquisition
        self.save_button = QPushButton("Start saving")

        self.layout().addWidget(self.image_viewer)
        self.layout().addWidget(self.wid_camera_properties)
        self.layout().addWidget(self.save_button)
        self.first_image = True
        self.refresh_display = True

        # ms for display clock. Currently 5 fps replay
        self.refresh_timer.start(200)

        self.timer.timeout.connect(self.refresh)
        self.refresh_timer.timeout.connect(self.display_new_image)
        self.save_button.clicked.connect(self.toggle)

    def toggle(self):
        self.state.saver.saving_signal.set()

    def refresh(self) -> None:
        current_image = self.state.get_image()
        if current_image is None:
            return

        if self.refresh_display:
            # print(current_image.shape)
            self.image_viewer.setImage(
                current_image,
                autoLevels=self.first_image,
                autoRange=self.first_image,
                autoHistogramRange=self.first_image,
            )
            self.first_image = False
            self.refresh_display = False

    def display_new_image(self):
        self.refresh_display = True


    # TODO: Remove this function if we can do everything with lightparam
    def update_property(self):
        pass



