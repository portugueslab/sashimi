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
from lightsheet.state import State


class ViewingWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()

        self.state = state
        self.setLayout(QVBoxLayout())
        self.image_viewer = pg.ImageView()
        self.image_viewer.ui.roiBtn.hide()
        self.image_viewer.ui.menuBtn.hide()

        self.start_button = QPushButton("ON")
        self.start_button.clicked.connect(self.toggle)

        self.layout().addWidget(self.image_viewer)
        self.layout().addWidget(self.start_button)
        self.first_image = True

        timer.timeout.connect(self.refresh)

    def toggle(self):
        self.state.camera.run()

    def refresh(self) -> None:
        current_image = self.state.get_image()
        if current_image is None:
            return

        self.image_viewer.setImage(
            current_image,
            autoLevels=self.first_image,
            autoRange=self.first_image,
            autoHistogramRange=self.first_image,
        )
        self.first_image = False


