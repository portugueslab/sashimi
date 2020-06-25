from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar
)
import pyqtgraph as pg
from lightparam.gui import ParameterGui
from lightparam.param_qt import ParametrizedQt
from lightparam import Param
from pyqtgraph.graphicsItems.ROI import ROI
from lightsheet.state import convert_camera_params, GlobalState

from time import time_ns

pg.setConfigOptions(imageAxisOrder="row-major")


class DisplaySettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "display_settings"
        self.display_framerate = Param(16, (1, 100))


class ViewingWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.timer = timer
        self.refresh_timer = QTimer()
        self.setLayout(QVBoxLayout())

        self.display_settings = DisplaySettings()
        self.wid_display_settings = ParameterGui(self.display_settings)

        self.image_viewer = pg.ImageView()
        self.roi = ROI(pos=[100, 100], size=500, removable=True)
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.image_viewer.view.addItem(self.roi)

        self.image_viewer.ui.roiBtn.hide()
        self.image_viewer.ui.menuBtn.hide()

        self.experiment_progress = QProgressBar()
        self.experiment_progress.setFormat("Volume %v of %m")
        self.lbl_experiment_progress = QLabel()

        self.layout().addWidget(self.image_viewer)
        self.layout().addWidget(self.wid_display_settings)
        self.layout().addWidget(self.experiment_progress)
        self.layout().addWidget(self.lbl_experiment_progress)

        self.experiment_progress.hide()
        self.lbl_experiment_progress.hide()

        self.is_first_image = True
        self.refresh_display = True

        # ms for display clock. Currently 5 fps replay
        self.last_time_updated = 0

        self.timer.timeout.connect(self.refresh)

    def refresh(self) -> None:
        current_image = self.state.get_image()
        if current_image is None:
            return

        current_time = time_ns()
        delta_t = (current_time - self.last_time_updated)/1e9
        if delta_t > 1/self.display_settings.display_framerate:
            self.image_viewer.setImage(
                current_image,
                autoLevels=self.is_first_image,
                autoRange=self.is_first_image,
                autoHistogramRange=self.is_first_image,
            )
            self.is_first_image = False
            self.last_time_updated = time_ns()

        sstatus = self.state.get_save_status()
        if sstatus is not None:
            self.experiment_progress.show()
            self.lbl_experiment_progress.show()
            self.experiment_progress.setMaximum(sstatus.target_params.n_volumes)
            self.experiment_progress.setValue(sstatus.i_volume)
            self.lbl_experiment_progress.setText("Saved chunks: {}".format(sstatus.i_chunk))


class CameraSettingsContainerWidget(QWidget):
    def __init__(self, state, roi, timer):
        super().__init__()
        self.roi = roi
        self.state = state
        self.full_size = True
        self.camera_info_timer = timer
        self.setLayout(QVBoxLayout())

        self.wid_camera_settings = ParameterGui(self.state.camera_settings)

        self.lbl_camera_info = QLabel()
        self.lbl_roi = QLabel()

        self.set_roi_button = QPushButton("set ROI")
        self.set_full_size_frame_button = QPushButton("set full size frame")

        self.layout().addWidget(self.wid_camera_settings)
        self.layout().addWidget(self.lbl_camera_info)
        self.layout().addWidget(self.set_roi_button)
        self.layout().addWidget(self.set_full_size_frame_button)
        self.layout().addWidget(self.lbl_roi)

        self.update_camera_info()
        self.camera_info_timer.start()

        self.set_roi_button.clicked.connect(self.set_roi)
        self.set_full_size_frame_button.clicked.connect(self.set_full_size_frame)
        self.camera_info_timer.timeout.connect(self.update_camera_info)

    def set_roi(self):
        roi_pos = self.roi.pos()
        roi_size = self.roi.size()
        self.state.camera_settings.subarray = tuple([roi_pos.x(), roi_pos.y(), roi_size.x(), roi_size.y()])
        self.update_roi_info(width=roi_size.x(), height=roi_size.y())

    def set_full_size_frame(self):
        self.state.camera_settings.subarray = [
            0,
            0,
            self.state.current_camera_status.image_width,
            self.state.current_camera_status.image_height
        ]
        camera_params = convert_camera_params(self.state.camera_settings)
        self.update_roi_info(
            width=self.state.current_camera_status.image_width / camera_params.binning,
            height=self.state.current_camera_status.image_height / camera_params.binning
        )

    def update_roi_info(self, width, height):
        self.lbl_roi.setText(
            "Current frame dimensions are:\nHeight: {}\nWidth: {}".format(int(height), int(width)))

    def update_camera_info(self):
        triggered_frame_rate = self.state.get_triggered_frame_rate()
        if triggered_frame_rate is not None:
            if self.state.global_state == GlobalState.PAUSED:
                self.lbl_camera_info.hide()
            else:
                self.lbl_camera_info.setStyleSheet("color: white")
                expected_frame_rate = None
                if self.state.global_state == GlobalState.PREVIEW:
                    frame_rate = self.state.current_camera_status.internal_frame_rate
                    self.lbl_camera_info.setText("Internal frame rate: {} Hz".format(round(frame_rate, 2)))
                if self.state.global_state == GlobalState.VOLUME_PREVIEW:
                    planes = self.state.volume_setting.n_planes - \
                             self.state.volume_setting.n_skip_start - self.state.volume_setting.n_skip_end
                    expected_frame_rate = self.state.volume_setting.frequency * planes
                if self.state.global_state == GlobalState.PLANAR_PREVIEW:
                    expected_frame_rate = self.state.single_plane_settings.frequency
                if expected_frame_rate:
                    self.lbl_camera_info.setText(
                        "\n".join(
                            [
                                "Camera frame rate: {} Hz".format(round(triggered_frame_rate, 2))
                            ]
                            + (
                                ["Camera is lagging behind. Decrease exposure, number of planes or frequency"]
                                if expected_frame_rate > (triggered_frame_rate * 1.1)
                                else [
                                    "Seems to follow well current speed"
                                ]
                            )
                        )
                    )

                    if expected_frame_rate > (triggered_frame_rate * 1.1):
                        self.lbl_camera_info.setStyleSheet("color: red")
                    else:
                        self.lbl_camera_info.setStyleSheet("color: green")

                self.lbl_camera_info.show()
