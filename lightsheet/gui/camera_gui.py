from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
)
import pyqtgraph as pg
import qdarkstyle
from lightsheet.state import State


class ViewingWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setLayout(QVBoxLayout())
        self.image_viewer = pg.ImageView()
        self.image_viewer.ui.roiBtn.hide()
        self.image_viewer.ui.menuBtn.hide()
        self.layout().addWidget(self.image_viewer)
        self.first_image = True

    def update(self) -> None:
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


# TODO: Delete this part in the bottom, it is just for testing

class LightsheetViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.state = State()
        self.image_display = ViewingWidget(self.state)
        self.setCentralWidget(self.image_display)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def update(self):
        self.image_display.update()
        self.experiment_widget.update()

    def closeEvent(self, event) -> None:
        self.state.wrap_up()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    viewer = LightsheetViewer()
    viewer.show()
    app.exec_()
