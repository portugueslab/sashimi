from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
)
from lightparam.gui import ParameterGui
from lightparam import Param
from lightparam.param_qt import ParametrizedQt
from sashimi.state import (
    State,
)
import napari

# TODO: In future realeases of napari remove monkey patched code. Accessing protected elements is bad practice
from napari.layers.shapes._shapes_constants import Mode
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


# TODO this should be logarithmic, temporarily setting it to smaller range for usability.
# Alternatively, it could be set by the conf file, although I don't want to have view-related stuff under "camera"
class ContrastSettings(ParametrizedQt):
    def __init__(self):
        super().__init__(self)
        self.name = "image_contrast"
        self.contrast_range = Param((0, 2000), (-50, 5000))


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

    _DELAY_REFRESH_COUNT = 10

    def __init__(self, state: State, timer: QTimer, style: str):
        super().__init__()
        self.state = state
        timer.timeout.connect(self.refresh)

        # Note: here we are assuming that the camera has a square sensor, and resolution is
        # described by only one number (most scientific camera are)
        if conf["scopeless"]:
            self.max_sensor_resolution = [256, 256]
        else:
            self.max_sensor_resolution = conf["camera"]["max_sensor_resolution"]

        self.noise_subtraction_set = False
        self.count_from_change = None
        self.refresh_display = True
        self.is_first_frame = True
        self.auto_contrast = True

        s = self.get_fullframe_size()
        self.image_shape = (1, s, s)

        self.viewer = napari.Viewer(show=False)
        # setting napari style to sashimi's
        self.viewer.window.qt_viewer.setStyleSheet(style)

        # Add image layer that will be used to show frames/volumes:
        self.frame_layer = self.viewer.add_image(
            np.zeros(
                [
                    1,
                ]
                + self.max_sensor_resolution
            ),
            blending="translucent",
            name="frame_layer",
        )

        # Add square ROI of size max image size:
        self.roi = self.viewer.add_shapes(
            [np.array([[0, 0], [s[0], 0], [s[0], s[1]], [0, s[1]]])],
            blending="translucent",
            face_color="transparent",
            face_contrast_limits=(0, 0),
            opacity=1,
            visible=False,
            name="roi_layer",
        )

        self.main_layout = QVBoxLayout()
        self.bottom_layout = QHBoxLayout()

        self.viewer.window.qt_viewer.viewerButtons.consoleButton.hide()
        self.viewer.window.qt_viewer.viewerButtons.rollDimsButton.hide()
        self.viewer.window.qt_viewer.viewerButtons.gridViewButton.hide()
        self.viewer.window.qt_viewer.viewerButtons.transposeDimsButton.hide()
        self.viewer.window.qt_viewer.viewerButtons.resetViewButton.setText("Reset view")

        self.ndisplay_button = self.viewer.window.qt_viewer.viewerButtons.ndisplayButton
        self.ndisplay_button.setText("3D mode")
        self.ndisplay_button.clicked.connect(self.toggle_ndims)

        self.viewer.dims.events.connect(self.update_current_plane)

        self.bottom_layout.addWidget(self.viewer.window.qt_viewer.viewerButtons)

        self.auto_contrast_chk = QCheckBox("Autoadjust contrast")

        self.contrast_range = ContrastSettings()
        self.wid_contrast_range = ParameterGui(self.contrast_range)

        self.bottom_layout.addWidget(self.auto_contrast_chk)
        self.bottom_layout.addWidget(self.wid_contrast_range)

        self.bottom_layout.addStretch()

        self.main_layout.addWidget(self.viewer.window.qt_viewer)
        self.main_layout.addLayout(self.bottom_layout)
        self.setLayout(self.main_layout)

        # Connect changes of camera and laser to contrast reset:
        self.auto_contrast_chk.stateChanged.connect(self.update_auto_contrast)
        self.contrast_range.sig_param_changed.connect(self.set_manual_contrast)

        self.auto_contrast_chk.setChecked(True)

        self.state.camera_settings.sig_param_changed.connect(
            self.launch_delayed_contrast_reset
        )
        self.state.light_source_settings.sig_param_changed.connect(
            self.launch_delayed_contrast_reset
        )
        self.viewer.window.qt_viewer.viewerButtons.resetViewButton.pressed.connect(
            self.reset_contrast
        )

    def get_fullframe_size(self):
        """Maximum size of the image at current binning. As stated above, we assume square sensors."""
        binning = int(self.state.camera_settings.binning)
        return [r // binning for r in self.max_sensor_resolution]

    def refresh(self) -> None:
        """Main refresh loop called by timeout of the main timer."""
        self.refresh_image()

        self.check_noise_subtraction_state()

        # This pattern with the counting is required to update the image range with some delay,
        # as the first received afterwards might still be the wrong one when changing exposure or noise subtraction
        if self.count_from_change is not None:
            self.count_from_change += 1
            if self.count_from_change == self._DELAY_REFRESH_COUNT:
                self.reset_contrast()
                self.count_from_change = None

    def check_noise_subtraction_state(self):
        """If we toggled noise subtraction, reset contrast."""
        noise_subtraction_set = self.state.noise_subtraction_active.is_set()
        if noise_subtraction_set != self.noise_subtraction_set:
            self.noise_subtraction_set = noise_subtraction_set
            self.launch_delayed_contrast_reset()

    def launch_delayed_contrast_reset(self):
        """By setting this from None to 0, we schedule a delayed contrast reset.
        The actual counting happens in the main refresh, connected to the timer.
        """
        self.count_from_change = 0

    def refresh_image(self):
        current_image = self.state.get_volume()
        if current_image is None:
            return

        # If not volumetric or out of range, reset indexes:
        if current_image.shape[0] == 1:
            self.viewer.dims.reset()
        self.frame_layer.data = current_image
        # self.frame_layer.scale = [self.voxel_size[0] / self.voxel_size[1], 1.0, 1.0]

        # Check if anything changed in the image shape, which would mean that changes of the contrast
        # are required (in case a parameter update was missed).
        if self.is_first_frame or self.image_shape != current_image.shape:
            self.reset_contrast()
            self.viewer.reset_view()

        self.image_shape = current_image.shape
        self.is_first_frame = False

        # Keep current plane in synch when the number of planes changes
        self.viewer.dims.set_current_step(0, self.state.current_plane)

    def toggle_ndims(self):
        """We set the scale only if we are in 3D mode, otherwise there can be funny problems with
        the image slider in the 2D view.
        Hopefully all of this will be improved in newer versions of Napari
        """
        if self.ndisplay_button.isChecked():
            self.frame_layer.scale = [self.state.voxel_size[0] / self.state.voxel_size[1], 1.0, 1.0]
        else:
            self.frame_layer.scale = [1.0, 1.0, 1.0]

    def update_current_plane(self, _):
        self.state.current_plane = self.viewer.dims.current_step[0]

    def reset_contrast(self):
        if self.auto_contrast:
            self.frame_layer.reset_contrast_limits()
        else:
            self.set_manual_contrast()

    def update_auto_contrast(self, is_checked):
        if is_checked:
            self.wid_contrast_range.setEnabled(False)
            self.auto_contrast = True
            self.reset_contrast()
        else:
            self.wid_contrast_range.setEnabled(True)
            self.auto_contrast = False
            self.set_manual_contrast()

    def set_manual_contrast(self):
        self.frame_layer.contrast_limits = self.contrast_range.contrast_range


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

        self.sensor_resolution = self.wid_display.max_sensor_resolution

        self.full_size = True
        self.current_binning = conf["camera"]["default_binning"]

        self.wid_camera_settings = ParameterGui(self.state.camera_settings)

        self.setLayout(QVBoxLayout())

        self.btn_roi = QPushButton(ROI_TEXTS[self.roi_state])
        self.btn_cancel_roi = QPushButton("Cancel")
        self.btn_cancel_roi.hide()

        self.layout().addWidget(self.wid_camera_settings)
        self.layout().addWidget(self.btn_roi)
        self.layout().addWidget(self.btn_cancel_roi)

        self.btn_roi.clicked.connect(self.iterate_roi_state)
        self.btn_cancel_roi.clicked.connect(self.cancel_roi_selection)

    def iterate_roi_state(self):
        """Called whenever we press the set ROI button, go to state of the ROI.

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
            self.wid_display.viewer.layers["roi_layer"].mode = Mode.SELECT

            # Disable binning option if an ROI is set:
            self.wid_camera_settings.param_widgets["binning"].setEnabled(False)
        elif self.roi_state == RoiState.SET:
            self._hide_roi()
            self.set_roi()
            self.btn_cancel_roi.hide()

        self.btn_roi.setText(ROI_TEXTS[self.roi_state])

    def _hide_roi(self):
        self.wid_display.roi.visible = False

    def _show_roi(self):
        self.wid_display.roi.visible = True

    def cancel_roi_selection(self):
        self.roi_state = RoiState(3)
        self.iterate_roi_state()

    def update_on_bin_change(self, changed_params):
        """Update ROI coordinates when changing the binning."""
        # TODO check if possible to trigger only on change of the binning parameter instead of checking
        if "binning" in changed_params.keys():
            b = int(changed_params["binning"][0])
            self.roi.data = [self.roi.data[0] / (b / self.current_binning)]
            self.current_binning = b
            self.state.camera_settings.block_signal = True
            self.set_roi()
            self.state.camera_settings.block_signal = False

        # Camera settings are sent through the state here to avoid out of synch call of this and
        # the state.send_camera_setting() methods when updating and keep everything together.
        self.state.send_camera_settings()

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
        max_image_dimension = self.wid_display.get_fullframe_size()
        # Make sure that the coordinates of the cropped ROI are within the image by cropping at o and max size
        cropped_coords = [
            max(min(i, max_image_dimension[n % 2]), 0)
            for n, i in enumerate(self.roi_coords)
        ]

        # Calculate dimensions of the image:
        height = cropped_coords[2] - cropped_coords[0]
        width = cropped_coords[3] - cropped_coords[1]
        if height == 0 or width == 0:
            warn("Trying to set ROI outside FOV", CameraWarning)
            self.cancel_roi_selection()
            return

        self.state.camera_settings.roi = [
            cropped_coords[0],
            cropped_coords[1],
            height,
            width,
        ]

    def set_full_frame(self):
        s = self.wid_display.get_fullframe_size()
        self.roi.data = [np.array([[0, 0], [s[0], 0], [s[0], s[1]], [0, s[1]]])]

        self.state.camera_settings.roi = [0, 0, s[0], s[1]]
