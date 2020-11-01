from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from lightparam.gui import ParameterGui
from sashimi.state import (
    convert_camera_params,
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
    The get_stuff methods replace properties, which seem to be an issue for children of QWidget when
    used in the __init__.

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

        # Note: here we are assuming that the camera has a square sensor, and resolution is
        # described by only one number (most scientific camera are)
        if conf["scopeless"]:
            self.sensor_resolution = 256
        else:
            self.sensor_resolution = conf["camera"]["sensor_resolution"][0]

        self.main_layout = QVBoxLayout()

        self.viewer = napari.Viewer(show=False)
        self.viewer.theme = "dark_sashimi"

        # Add image layer that will be used to show frames/volumes:
        self.frame_layer = self.viewer.add_image(
            np.zeros([1, self.sensor_resolution, self.sensor_resolution]),
            blending="translucent",
            name="frame_layer",
        )

        # Add square ROI of size max image size:
        s = self.get_fullframe_size()
        self.roi = self.viewer.add_shapes(
            [np.array([[0, 0], [s, 0], [s, s], [0, s]])],
            blending="translucent",
            face_color="yellow",
            face_contrast_limits=(0, 0),
            opacity=0.7,
            visible=False,
        )

        self.bottom_layout = QHBoxLayout()

        self.viewer.window.qt_viewer.viewerButtons.consoleButton.hide()
        self.viewer.window.qt_viewer.viewerButtons.rollDimsButton.hide()
        self.viewer.window.qt_viewer.viewerButtons.transposeDimsButton.setText("Rotate view")
        self.viewer.window.qt_viewer.viewerButtons.resetViewButton.setText("Reset view")
        self.viewer.window.qt_viewer.viewerButtons.gridViewButton.setText("Grid mode")
        self.viewer.window.qt_viewer.viewerButtons.ndisplayButton.setText("3D mode")

        self.bottom_layout.addWidget(self.viewer.window.qt_viewer.viewerButtons)
        self.bottom_layout.addStretch()

        self.main_layout.addWidget(self.viewer.window.qt_viewer)
        self.main_layout.addLayout(self.bottom_layout)
        self.setLayout(self.main_layout)

        # Connect changes of camera and laser to contrast reset:
        self.state.camera_settings.sig_param_changed.connect(self.reset_contrast)
        self.state.light_source_settings.sig_param_changed.connect(self.reset_contrast)

        self.refresh_display = True
        self.is_first_frame = True
        self.image_shape = (1, s, s)

    # @property
    def get_camera_binning(self):
        return convert_camera_params(self.state.camera_settings).binning

    # @property
    def get_fullframe_size(self):
        """Maximum size of the image at current binning. As stated above, we assume square sensors.
        """
        return self.sensor_resolution // self.get_camera_binning()

    @property
    def voxel_size(self):
        return get_voxel_size(
            self.state.volume_setting,
            self.state.camera_settings,
        )

    def refresh(self) -> None:
        """Main refresh loop called by timeout of the main timer."""
        self.refresh_image()

    def refresh_image(self):
        current_image = self.state.get_volume()
        if current_image is None:
            return

        # If not volumetric or out of range, reset indexes:
        if current_image.shape[0] == 1:
            self.frame_layer.dims.reset()
        self.frame_layer.data = current_image
        self.frame_layer.scale = [self.voxel_size[0] / self.voxel_size[1], 1.0, 1.0]

        # Check if anything changed in the image shape, which would mean that changes of the contrast
        # are required (in case the parameter update was missed).
        if self.is_first_frame or self.image_shape != current_image.shape:
            self.reset_contrast()

        self.image_shape = current_image.shape
        self.is_first_frame = False

    def reset_contrast(self):
        self.frame_layer.reset_contrast_limits()


class CameraSettingsWidget(QWidget):
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
        self.state.camera_settings.sig_param_changed.connect(self.update_on_bin_change)
        self.timer = timer

        self.camera_msg_queue = Queue()

        if conf["scopeless"]:
            self.sensor_resolution = 256
        else:
            self.sensor_resolution = conf["camera"]["sensor_resolution"][0]

        self.full_size = True
        self.current_binning = 1  #TODO avoid hardcoding for first assignation

        self.wid_camera_settings = ParameterGui(self.state.camera_settings)

        self.setLayout(QVBoxLayout())

        self.btn_roi = QPushButton(ROI_TEXTS[self.roi_state])
        self.btn_cancel_roi = QPushButton("Cancel")
        self.btn_cancel_roi.hide()

        self.layout().addWidget(self.wid_camera_settings)
        self.layout().addWidget(self.btn_roi)
        self.layout().addWidget(self.btn_cancel_roi)

        self.btn_roi.clicked.connect(self.roi_action)
        self.btn_cancel_roi.clicked.connect(self.cancel_roi_selection)

    def roi_action(self):
        """Roi action is called whenever we press the set ROI button.
        The napari ROI has three states, each of them with buttons and properties etc. The code is executed depending
        on the status the ROI is, and changes the status for the next button press call.
        """
        try:
            self.roi_state = RoiState(self.roi_state.value + 1)
        except ValueError:
            self.roi_state = RoiState(1)

        if self.roi_state == RoiState.FULL:
            self.set_full_frame()
            self._hide_roi()
            self.btn_cancel_roi.hide()
            self.wid_camera_settings.param_widgets["binning"].setEnabled(True)
        elif self.roi_state == RoiState.DISPLAYED:
            self._show_roi()
            self.btn_cancel_roi.show()
            # TODO: Select shape layer without napari key bindings
            self.wid_display.viewer.press_key("s")
        elif self.roi_state == RoiState.SET:
            self._hide_roi()
            self.set_roi()
            self.btn_cancel_roi.hide()
            # Disable binning option if an ROI is set:
            self.wid_camera_settings.param_widgets["binning"].setEnabled(False)

    def _hide_roi(self):
        self.wid_display.roi.visible = False

    def _show_roi(self):
        self.wid_display.roi.visible = True

    def cancel_roi_selection(self):
        self.roi_state = RoiState(3)
        self.roi_action()

    def update_on_bin_change(self, changed_params):
        """Update ROI coordinates when changing the binning.
        #TODO check if possible to trigger only on change of the binning parameter instead of checking
        """
        if "binning" in changed_params.keys():
            b = int(changed_params["binning"][0])
            self.roi.data = self.roi.data[0] / (b / self.current_binning)
            self.current_binning = b

    @property
    def roi_coords(self):
        """ROI coordinates are expressed with respect to the displayed napari image.
        Therefore, an ROI in the same position of the camera image will have different
        coordinates depending on the binning.
        Returns tuple (vpos_orig, hpos_orig, vpos_max, hpos_max)
        """
        coords = self.roi.data[0].astype(int)
        return coords[0, 0], coords[0, 1], coords[1, 0], coords[3, 1]

    def set_roi(self):
        """Set the ROI by passing ROI coordinates to the camera settings.
        A bunch of controls need to happen before we can safely send the ROI to the camera.
        """
        max_image_dimension = self.sensor_resolution // self.current_binning
        # Make sure that the coordinates of the cropped ROI are within the image by cropping at o and max size
        cropped_coords = [max(min(i, max_image_dimension), 0) for i in self.roi_coords]

        # Calculate dimensions of the image:
        height = cropped_coords[2] - cropped_coords[0]
        width = cropped_coords[3] - cropped_coords[1]
        if height == 0 or width == 0:
            warn("Trying to set ROI outside FOV", CameraWarning)
            self.cancel_roi_selection()
            return

        self.state.camera_settings.roi = [cropped_coords[0], cropped_coords[1], height, width]

    def set_full_frame(self):
        self.state.camera_settings.roi = [
            0,
            0,
            self.sensor_resolution // self.current_binning,
            self.sensor_resolution // self.current_binning,
        ]
