from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar
)
import pyqtgraph
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

        self.image_viewer = pyqtgraph.ImageView()
        self.roi = self.image_viewer.getRoiPlot()
        # self.roi = pyqtgraph.ROI(pos=(50, 50), size=(10, 10))
        self.image_viewer.ui.roiBtn.hide()
        self.image_viewer.ui.menuBtn.hide()

        self.display_settings = DisplaySettings()

        self.wid_camera_properties = ParameterGui(self.state.camera_properties)
        self.wid_display_settings = ParameterGui(self.display_settings)

        self.lbl_camera_info = QLabel()

        #TODO: Add to layout
        self.stack_progress = QProgressBar()
        self.chunk_progress = QProgressBar()
        self.chunk_progress.setFormat("Chunk %v of %m")
        self.stack_progress.setFormat("Frame %v of %m")

        self.set_roi_button = QPushButton("set ROI")

        self.layout().addWidget(self.image_viewer)
        self.layout().addWidget(self.roi)
        self.layout().addWidget(self.wid_display_settings)
        self.layout().addWidget(self.wid_camera_properties)
        self.layout().addWidget(self.lbl_camera_info)
        self.layout().addWidget(self.set_roi_button)
        self.layout().addWidget(self.chunk_progress)
        self.layout().addWidget(self.stack_progress)

        self.chunk_progress.hide()
        self.stack_progress.hide()

        self.is_first_image = True
        self.refresh_display = True

        self.update_camera_info()

        # ms for display clock. Currently 5 fps replay
        self.refresh_timer.start(int(1000 / self.display_settings.replay_rate))

        self.timer.timeout.connect(self.refresh)
        self.refresh_timer.timeout.connect(self.display_new_image)
        self.set_roi_button.clicked.connect(self.set_roi)
        self.display_settings.sig_param_changed.connect(self.update_replay_rate)
        self.state.camera_properties.sig_param_changed.connect(self.update_camera_info)
        # FIXME: Display frame rate correctly in volumetric scan
        self.state.volume_setting.sig_param_changed.connect(self.update_camera_info)

    def update_replay_rate(self):
        self.refresh_timer.setInterval(int(1000 / self.display_settings.replay_rate))

    # TODO: Give functionality to ROI selection i.e extract position and size, pass to Camera process/thread bia Queue
    def set_roi(self):
        pass

    def refresh(self) -> None:
        current_image = self.state.get_image()
        if current_image is None:
            return

        if self.refresh_display:
            self.image_viewer.setImage(
                current_image,
                autoLevels=self.is_first_image,
                autoRange=self.is_first_image,
                autoHistogramRange=self.is_first_image,
            )
            self.is_first_image = False
            self.refresh_display = False

        sstatus = self.state.get_save_status()
        if sstatus is not None:
            self.chunk_progress.show()
            self.stack_progress.show()
            num_chunks = int(sstatus.target_params.n_t / sstatus.target_params.chunk_size)
            self.chunk_progress.setMaximum(num_chunks)
            self.chunk_progress.setValue(sstatus.i_chunk)
            self.stack_progress.setMaximum(int(sstatus.target_params.n_t / num_chunks))
            self.stack_progress.setValue(sstatus.i_t)

    def display_new_image(self):
        self.refresh_display = True

    def update_camera_info(self):
        current_camera_settings = self.state.get_camera_settings()
        frame_rate = current_camera_settings.image_params.internal_frame_rate
        self.lbl_camera_info.setText("Internal frame rate: " + str(round(frame_rate, 2)))
