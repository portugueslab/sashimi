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
from sashimi.state import (
    convert_camera_params,
    GlobalState,
    State,
    get_voxel_size,
)

from time import time_ns
import napari
import numpy as np


IMAGE_SIZE = (1024, 1024)  #TODO this should probably be configurable

class DisplaySettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "display_settings"
        self.display_framerate = Param(30, (1, 100))


class ViewingWidget(QWidget):
    """Central widget that displays the images/volumes streamed from the camera, and progress bar.
    Internally, the display is powered via a Napari viewer.

    Parameters
    ----------
    state : State object
        Main state.
    timer : QTimer
        Timer from the main GUI.
    """
    def __init__(self, state: State, timer):
        super().__init__()
        self.state = state

        timer.timeout.connect(self.refresh)

        self.main_layout = QVBoxLayout()

        self.display_settings = DisplaySettings()
        self.wid_display_settings = ParameterGui(self.display_settings)

        self.viewer = napari.Viewer(show=False)
        self.frame_layer = self.viewer.add_image(
            np.zeros((1, ) + IMAGE_SIZE), blending="translucent", name="frame_layer",
        )

        self.roi = self.viewer.add_shapes(
            [np.array([[0, 0], [IMAGE_SIZE[0], 0], [IMAGE_SIZE[0], IMAGE_SIZE[1]], [0, IMAGE_SIZE[1]]])],
            blending="translucent",
            opacity=0.1,
            face_color="yellow",
        )
        self.toggle_roi_display()
        self.btn_display_roi = QPushButton("Show/Hide ROI")
        self.btn_reset_contrast = QPushButton("Reset contrast limits")

        self.experiment_progress = QProgressBar()
        self.experiment_progress.setFormat("Volume %v of %m")
        self.lbl_experiment_progress = QLabel()

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addWidget(self.wid_display_settings)
        self.bottom_layout.addWidget(self.btn_display_roi)
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

        self.btn_display_roi.clicked.connect(self.toggle_roi_display)
        self.btn_reset_contrast.clicked.connect(self.update_contrast_limits)

    @property
    def voxel_size(self):
        return get_voxel_size(
                self.state.volume_setting,
                self.state.camera_settings,
                self.state.scope_alignment_info,
            )

    def refresh(self) -> None:
        """Main refresh loop called by timeout of the main timer.
        """
        self.refresh_image()
        self.refresh_progress_bar()

    def refresh_image(self):
        current_image = self.state.get_volume()
        if current_image is None:
            return

        delta_t = (time_ns() - self.last_time_updated) / 1e9

        if delta_t > 1 / self.display_settings.display_framerate:
            # If not volumetric or out of range, reset indexes:
            if current_image.shape[0] == 1:
                self.frame_layer.dims.reset()
            self.frame_layer.data = current_image
            self.frame_layer.scale = [self.voxel_size[0] / self.voxel_size[1], 1.0, 1.0]
            self.last_time_updated = time_ns()

    def refresh_progress_bar(self):
        sstatus = self.state.get_save_status()
        if self.state.get_save_status() is not None:
            self.experiment_progress.show()
            self.lbl_experiment_progress.show()
            self.experiment_progress.setMaximum(sstatus.target_params.n_volumes)
            self.experiment_progress.setValue(sstatus.i_volume)
            self.lbl_experiment_progress.setText(
                "Saved chunks: {}".format(sstatus.i_chunk)
            )

    def update_contrast_limits(self):
        self.frame_layer.reset_contrast_limits()

    def toggle_roi_display(self):
        if self.roi.visible:
            # TODO: Block rotating roi
            self.roi.visible = False
        else:
            self.roi.visible = True
            self.viewer.press_key(
                "s"
            )  # this allows moving the whole roi and scaling but no individual handles

    def update_roi(self):
        pass


class CameraSettingsContainerWidget(QWidget):
    """Widget to modify parameters for the camera.

    Parameters
    ----------
    state : State object
    roi : default ROI size
    timer : QTimer
    """
    def __init__(self, state, roi, timer):

        super().__init__()
        self.roi = roi
        self.state = state
        timer.timeout.connect(self.update_camera_info)

        self.full_size = True

        self.wid_camera_settings = ParameterGui(self.state.camera_settings)

        self.setLayout(QVBoxLayout())

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
        self.set_full_size_frame()

        self.set_roi_button.clicked.connect(self.set_roi)
        self.set_full_size_frame_button.clicked.connect(self.set_full_size_frame)

    @property
    def roi_pos(self):
        return int(self.roi.data[0][0][1]), int(self.roi.data[0][0][0])

    @property
    def roi_size(self):
        return int(self.roi.data[0][3][1] - self.roi.data[0][0][1]), \
               int(self.roi.data[0][1][0] - self.roi.data[0][0][0])

    def set_roi(self):
        """Set ROI size from loaded params.
        """
        self.state.camera_settings.subarray = tuple(
            [self.roi_pos[0], self.roi_pos[1], self.roi_size[0], self.roi_size[1]]
        )
        self.update_roi_info()

    def set_full_size_frame(self):
        self.state.camera_settings.subarray = [
            0,
            0,
            self.state.current_camera_status.image_width,
            self.state.current_camera_status.image_height,
        ]

        self.update_roi_info()

    def update_roi_info(self):
        dims = self.state.camera_settings.subarray
        binning = convert_camera_params(self.state.camera_settings).binning
        self.lbl_roi.setText(
            f"Current frame dimensions are:\nHeight: {int(dims[0] /binning)}\nWidth: {int(dims[1]/binning)}"
        )

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
                if self.state.global_state == GlobalState.VOLUME_PREVIEW:
                    planes = (
                        self.state.volume_setting.n_planes
                        - self.state.volume_setting.n_skip_start
                        - self.state.volume_setting.n_skip_end
                    )
                    expected_frame_rate = self.state.volume_setting.frequency * planes
                if self.state.global_state == GlobalState.PLANAR_PREVIEW:
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
