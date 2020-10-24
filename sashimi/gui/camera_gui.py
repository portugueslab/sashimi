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
from sashimi.state import (
    convert_camera_params,
    GlobalState,
    State,
    get_voxel_size,
)
import napari
import numpy as np
from warnings import warn
from sashimi.hardware.cameras.interface import CameraWarning
from sashimi.config import read_config
from enum import Enum
from multiprocessing import Queue


conf = read_config()


class RoiState(Enum):
    FULL = 1
    DISPLAYED = 2
    SET = 3


ROI_TEXTS = {
    RoiState.FULL: "Select ROI",
    RoiState.DISPLAYED: "Set ROI",
    RoiState.SET: "Reset full frame",
}


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

    def __init__(self, state: State, timer: QTimer):
        super().__init__()
        self.state = state

        timer.timeout.connect(self.refresh)

        self.main_layout = QVBoxLayout()

        if conf["scopeless"]:
            self.sensor_resolution = 256
        else:
            self.sensor_resolution = conf["camera"]["sensor_resolution"][0]

        self.viewer = napari.Viewer(show=False)
        self.frame_layer = self.viewer.add_image(
            np.zeros([1, self.sensor_resolution, self.sensor_resolution]),
            blending="translucent",
            name="frame_layer",
        )
        binning = convert_camera_params(self.state.camera_settings).binning

        roi_init_shape = (
            np.array(
                [
                    self.sensor_resolution // binning,
                    self.sensor_resolution // binning,
                ]
            )
            // 2
        )
        self.roi = self.viewer.add_shapes(
            [
                np.array(
                    [
                        [0, 0],
                        [roi_init_shape[0], 0],
                        [roi_init_shape[0], roi_init_shape[1]],
                        [0, roi_init_shape[1]],
                    ]
                )
            ],
            blending="translucent",
            face_color="yellow",
            face_contrast_limits=(0, 0),
            opacity=0.7,
            visible=False,
        )

        self.experiment_progress = QProgressBar()
        self.experiment_progress.setFormat("Volume %v of %m")
        self.lbl_experiment_progress = QLabel()

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addWidget(self.viewer.window.qt_viewer.viewerButtons)
        self.bottom_layout.addStretch()

        self.main_layout.addWidget(self.viewer.window.qt_viewer)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.addWidget(self.experiment_progress)
        self.main_layout.addWidget(self.lbl_experiment_progress)

        self.experiment_progress.hide()
        self.lbl_experiment_progress.hide()

        self.refresh_display = True

        self.is_first_frame = True

        self.setLayout(self.main_layout)

        self.state.camera_settings.sig_param_changed.connect(self.reset_contrast)
        self.state.light_source_settings.sig_param_changed.connect(self.reset_contrast)

    @property
    def voxel_size(self):
        return get_voxel_size(
            self.state.volume_setting,
            self.state.camera_settings,
            self.state.scope_alignment_info,
        )

    def refresh(self) -> None:
        """Main refresh loop called by timeout of the main timer."""
        self.refresh_image()
        self.refresh_progress_bar()

    def refresh_image(self):
        current_image = self.state.get_volume()
        if current_image is None:
            return

        # If not volumetric or out of range, reset indexes:
        if current_image.shape[0] == 1:
            self.frame_layer.dims.reset()
        self.frame_layer.data = current_image
        self.frame_layer.scale = [self.voxel_size[0] / self.voxel_size[1], 1.0, 1.0]
        if self.is_first_frame:
            self.reset_contrast()
            self.is_first_frame = False

    def reset_contrast(self):
        self.frame_layer.reset_contrast_limits()

    def refresh_progress_bar(self):
        sstatus = self.state.get_save_status()
        if sstatus is not None:
            self.experiment_progress.show()
            self.lbl_experiment_progress.show()
            self.experiment_progress.setMaximum(sstatus.target_params.n_volumes)
            self.experiment_progress.setValue(sstatus.i_volume)
            self.lbl_experiment_progress.setText(
                "Saved chunks: {}".format(sstatus.i_chunk)
            )


class CameraSettingsContainerWidget(QWidget):
    """Widget to modify parameters for the camera.

    Parameters
    ----------
    state : State object
    wid_display : ViewingWidget
    timer : QTimer
    """

    def __init__(self, state, wid_display, timer):

        super().__init__()
        self.wid_display = wid_display
        self.roi = wid_display.roi
        self.roi_state = RoiState.FULL
        self.state = state

        self.camera_msg_queue = Queue()

        timer.timeout.connect(self.update_camera_info)

        if conf["scopeless"]:
            self.sensor_resolution = 256
        else:
            self.sensor_resolution = conf["camera"]["sensor_resolution"][0]

        self.full_size = True

        self.wid_camera_settings = ParameterGui(self.state.camera_settings)

        self.setLayout(QVBoxLayout())

        self.lbl_camera_info = QLabel()
        self.lbl_roi = QLabel()

        self.btn_roi = QPushButton(ROI_TEXTS[self.roi_state])
        self.btn_cancel_roi = QPushButton("Cancel")
        self.btn_cancel_roi.hide()

        self.layout().addWidget(self.wid_camera_settings)
        self.layout().addWidget(self.lbl_camera_info)
        self.layout().addWidget(self.btn_roi)
        self.layout().addWidget(self.btn_cancel_roi)
        self.layout().addWidget(self.lbl_roi)

        self.update_camera_info()

        self.btn_roi.clicked.connect(self.roi_action)
        self.btn_cancel_roi.clicked.connect(self.cancel_roi_selection)

    def roi_action(self):
        try:
            self.roi_state = RoiState(self.roi_state.value + 1)
        except ValueError:
            self.roi_state = RoiState(1)

        if self.roi_state == RoiState.FULL:
            self.set_full_frame()
            self._hide_roi()
            self.btn_cancel_roi.hide()
        elif self.roi_state == RoiState.DISPLAYED:
            self._show_roi()
            self.btn_cancel_roi.show()
            # TODO: Select shape layer without napari key bindings
            self.wid_display.viewer.press_key("s")
        elif self.roi_state == RoiState.SET:
            self._hide_roi()
            self.set_roi()
            self.btn_cancel_roi.hide()

        self.update_roi_txt()

    def update_roi_txt(self):
        self.btn_roi.setText(ROI_TEXTS[self.roi_state])

    def _hide_roi(self):
        self.wid_display.roi.visible = False

    def _show_roi(self):
        self.wid_display.roi.visible = True

    def cancel_roi_selection(self):
        self.roi_state = RoiState(3)
        self.roi_action()

    @property
    def roi_coords(self):
        return tuple(
            (
                int(self.roi.data[0][0][1]),
                int(self.roi.data[0][0][0]),
                int(self.roi.data[0][3][1]),
                int(self.roi.data[0][1][0]),
            )
        )

    def set_roi(self):
        """Set ROI size from loaded params."""
        binning = convert_camera_params(self.state.camera_settings).binning
        max_res = self.sensor_resolution // binning
        cropped_coords = [max(min(i // binning, max_res), 0) for i in self.roi_coords]
        dx = cropped_coords[2] - cropped_coords[0]
        dy = cropped_coords[3] - cropped_coords[1]
        if dx == 0 or dy == 0:
            warn("Trying to set ROI outside FOV", CameraWarning)
            self.cancel_roi_selection()
        else:
            binned_roi = [
                cropped_coords[0],
                cropped_coords[1],
                dx,
                dy,
            ]
            self.state.camera_settings.roi = [i * binning for i in binned_roi]
            self.update_roi_info()

    def set_full_frame(self):
        self.state.camera_settings.roi = [
            0,
            0,
            self.sensor_resolution,
            self.sensor_resolution,
        ]

        self.update_roi_info()

    def update_roi_info(self):
        dims = self.state.camera_settings.roi
        binning = convert_camera_params(self.state.camera_settings).binning
        self.lbl_roi.setText(
            f"Current frame dimensions are:\nHeight: {int(dims[0] / binning)}\nWidth: {int(dims[1] / binning)}"
        )

    # TODO: Move this to status bar, e.g. as a Queue()
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
