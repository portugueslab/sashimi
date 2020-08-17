from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
)
from lightparam.gui import ParameterGui
from lightparam.param_qt import ParametrizedQt
from lightparam import Param
from shirashi.state import (
    convert_camera_params,
    GlobalState,
    State,
    get_voxel_size,
)

from time import time_ns
import napari
import numpy as np


class DisplaySettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "display_settings"
        self.display_framerate = Param(30, (1, 100))


class ViewingWidget(QWidget):
    def __init__(self, state: State, timer):
        super().__init__()
        self.state = state
        self.timer = timer
        self.refresh_timer = QTimer()
        self.main_layout = QVBoxLayout()

        self.display_settings = DisplaySettings()
        self.wid_display_settings = ParameterGui(self.display_settings)

        self.viewer = napari.Viewer(show=False)
        self.frame_layer = self.viewer.add_image(
            np.zeros([1, 1024, 1024]), blending="translucent", name="frame_layer",
        )

        self.btn_reset_contrast = QPushButton("Reset contrast limits")

        self.experiment_progress = QProgressBar()
        self.experiment_progress.setFormat("Frame %v of %m")
        self.lbl_experiment_progress = QLabel()

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addWidget(self.wid_display_settings)
        self.bottom_layout.addWidget(self.btn_reset_contrast)
        self.bottom_layout.addWidget(self.viewer.window.qt_viewer.viewerButtons)
        self.bottom_layout.addStretch()

        self.main_layout.addWidget(self.viewer.window.qt_viewer)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.addWidget(self.experiment_progress)
        self.main_layout.addWidget(self.lbl_experiment_progress)

        self.experiment_progress.hide()
        self.lbl_experiment_progress.hide()

        self.refresh_display = True

        self.last_time_updated = 0

        self.setLayout(self.main_layout)

        self.timer.timeout.connect(self.refresh)
        self.btn_reset_contrast.clicked.connect(self.update_contrast_limits)

    def refresh(self) -> None:
        current_image = self.state.get_volume()

        if current_image is None:
            return

        current_time = time_ns()
        delta_t = (current_time - self.last_time_updated) / 1e9
        if delta_t > 1 / self.display_settings.display_framerate:
            # If not volumetric or out of range, reset indexes
            if current_image.shape[0] == 1:
                self.frame_layer.dims.reset()
            self.frame_layer.data = current_image
            voxel_size = get_voxel_size(
                self.state.volume_setting,
                self.state.camera_settings,
                self.state.scope_alignment_info,
            )
            self.frame_layer.scale = [voxel_size[0] / voxel_size[1], 1.0, 1.0]
            self.last_time_updated = time_ns()

        sstatus = self.state.get_save_status()
        if sstatus is not None:
            self.experiment_progress.show()
            self.lbl_experiment_progress.show()
            self.experiment_progress.setMaximum(sstatus.target_params.n_volumes)
            self.experiment_progress.setValue(sstatus.i_volume)
            self.lbl_experiment_progress.setText(
                "Saved chunks: {}".format(sstatus.i_chunk)
            )

    def update_contrast_limits(self):
        self.frame_layer.reset_contrast_limits()


class CameraSettingsContainerWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.full_size = True
        self.camera_info_timer = timer
        self.setLayout(QVBoxLayout())

        self.wid_camera_settings = ParameterGui(self.state.camera_settings)
        self.lbl_camera_info = QLabel()

        self.set_full_size_frame_button = QPushButton("set full size frame")

        self.layout().addWidget(self.wid_camera_settings)
        self.layout().addWidget(self.lbl_camera_info)
        self.layout().addWidget(self.set_full_size_frame_button)

        self.update_camera_info()
        self.set_full_size_frame()
        self.camera_info_timer.start()

        self.set_full_size_frame_button.clicked.connect(self.set_full_size_frame)
        self.camera_info_timer.timeout.connect(self.update_camera_info)


    def set_full_size_frame(self):
        self.state.camera_settings.subarray = [
            0,
            0,
            self.state.current_camera_status.image_width,
            self.state.current_camera_status.image_height,
        ]
        camera_params = convert_camera_params(self.state.camera_settings)

    def update_camera_info(self):
        frame_rate = self.state.get_triggered_frame_rate()
        if frame_rate is not None:
            if self.state.global_state == GlobalState.PAUSED:
                self.lbl_camera_info.hide()
            else:
                self.lbl_camera_info.setStyleSheet("color: white")
                expected_frame_rate = None
                if self.state.global_state == GlobalState.PREVIEW:
                    self.lbl_camera_info.setText(
                        "Camera frame rate: {} Hz".format(round(frame_rate, 2))
                    )
                if self.state.global_state == GlobalState.EXP_PREVIEW:
                    planes = (
                        self.state.volume_setting.n_planes
                        - self.state.volume_setting.n_skip_start
                        - self.state.volume_setting.n_skip_end
                    )
                    expected_frame_rate = self.state.volume_setting.frequency * planes
                if self.state.global_state == GlobalState.TBD_PREVIEW:
                    expected_frame_rate = self.state.single_plane_settings.frequency
                if expected_frame_rate:
                    self.lbl_camera_info.setText(
                        "\n".join(
                            ["Camera frame rate: {} Hz".format(round(frame_rate, 2))]
                            + (
                                [
                                    "Camera is lagging behind. Decrease exposure, number of planes or frequency"
                                ]
                                if expected_frame_rate > (frame_rate * 1.1)
                                else ["Seems to follow well current speed"]
                            )
                        )
                    )

                    if expected_frame_rate > (frame_rate * 1.1):
                        self.lbl_camera_info.setStyleSheet("color: red")
                    else:
                        self.lbl_camera_info.setStyleSheet("color: green")

                self.lbl_camera_info.show()
