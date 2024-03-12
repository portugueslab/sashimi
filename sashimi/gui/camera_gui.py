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
    get_voxel_size,
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

from numba import njit

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
        self.is_exp_started = False
        self.is_exp_ended = False
        self.is_drift_active = False

        s = self.get_fullframe_size()
        self.image_shape = (1, s, s)

        # Collect pixels to draw on.
        self.draw_pixels = np.empty((0, 2), np.int16)

        self.viewer = napari.Viewer(show=False)
        # setting napari style to sashimi's
        self.viewer.window.qt_viewer.setStyleSheet(style)

        # Add image layer that will be used to show frames/volumes:
        self.frame_layer = self.viewer.add_image(
            np.zeros([1,] + self.max_sensor_resolution),
            blending="translucent",
            name="frame_layer",
            visible=True,
        )

        # create drift layer and set it as not visible
        self.drift_layer = self.viewer.add_image(
            np.zeros([1, 5, 5,]),
            blending="additive",
            name="drift_layer",
            colormap="red",
            visible=False,
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

        self.active_drift_chk = QCheckBox("Activate Drift Reference")
        self.display_drift_chk = QCheckBox("Visualize/Hide Drift Reference")
        self.display_frame_chk = QCheckBox("Visualize/Hide Live View")

        self.bottom_layout.addWidget(self.auto_contrast_chk)
        self.bottom_layout.addWidget(self.wid_contrast_range)
        self.bottom_layout.addWidget(self.active_drift_chk)
        self.bottom_layout.addWidget(self.display_drift_chk)
        self.bottom_layout.addWidget(self.display_frame_chk)

        self.bottom_layout.addStretch()

        self.main_layout.addWidget(self.viewer.window.qt_viewer)
        self.main_layout.addLayout(self.bottom_layout)
        self.setLayout(self.main_layout)

        # Connect changes of camera and laser to contrast reset:
        self.auto_contrast_chk.stateChanged.connect(self.update_auto_contrast)
        self.contrast_range.sig_param_changed.connect(self.set_manual_contrast)

        # connect drift widget
        self.active_drift_chk.clicked.connect(self.activate_drift_reference)
        self.display_drift_chk.clicked.connect(self.display_drift_reference)
        self.display_frame_chk.clicked.connect(self.display_frame_reference)

        self.display_frame_chk.setChecked(True)
        self.display_frame_chk.setEnabled(False)
        self.display_drift_chk.setEnabled(
            False
        )  # only enabled if drift reference is activated

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

    @property
    def voxel_size(self):
        return get_voxel_size(self.state.volume_setting, self.state.camera_settings,)

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

    @staticmethod
    @njit(parallel=True)
    def get_circle_indices(img_shape, diameter):
        # We can narrowly define the area to check
        # by removing the indices of the smallest
        # square that confines the circle and the
        # bigger square inside the circle.
        # Furthermore, we only need to get one
        # quadrant, everything else can be done
        # with simple operations on the indices.
        indices = np.empty((0, 2), np.int16)  # Max value: 32768
        middle = [
            x // 2 for x in img_shape
        ]  # Ignore that there might not be an exact middle.
        radius = diameter // 2

        upper_x = radius + 1
        upper_y = radius + 1

        lower_x = int(np.floor((radius * np.sqrt(2) / 2)))
        lower_y = int(np.floor((radius * np.sqrt(2) / 2)))

        lower_x_range = np.arange(lower_x)
        lower_y_range = np.arange(lower_y)
        upper_x_range = np.arange(lower_x, upper_x)
        upper_y_range = np.arange(lower_y, upper_y)

        # Now we use three combinations to get the three
        # rectangles containing the circle.
        # Corner square:
        for x in upper_x_range:
            for y in upper_y_range:
                if np.round(np.sqrt((x ** 2) + (y ** 2))) == radius:
                    i = middle[0] + x
                    j = middle[1] + y
                    new_ind = np.array([[i, j], [-i, j], [i, -j], [-i, -j]], np.int16)
                    indices = np.concatenate((indices, new_ind), axis=0)

        # X rectangle:
        for x in lower_x_range:
            for y in upper_y_range:
                if np.round(np.sqrt((x ** 2) + (y ** 2))) == radius:
                    i = middle[0] + x
                    j = middle[1] + y
                    new_ind = np.array([[i, j], [-i, j], [i, -j], [-i, -j]], np.int16)
                    indices = np.concatenate((indices, new_ind), axis=0)

        # Y rectangle:
        for x in upper_x_range:
            for y in lower_y_range:
                if np.round(np.sqrt((x ** 2) + (y ** 2))) == radius:
                    i = middle[0] + x
                    j = middle[1] + y
                    new_ind = np.array([[i, j], [-i, j], [i, -j], [-i, -j]], np.int16)
                    indices = np.concatenate((indices, new_ind), axis=0)

        return indices

    def refresh_image(self):
        current_image = self.state.get_volume()
        if current_image is None:
            return

        # Dirty place to add an alignment cross, but it's not going to be merged anyway.
        # What is added here does not get included in the recording.
        # Image is: (1, x, y).
        cross_grey_value = 65535  # it's 16 bit.
        if current_image.shape[1] % 2 == 0:
            middle = int(np.floor(current_image.shape[1] / 2))
            current_image[:, middle : middle + 1, :] = cross_grey_value
        else:
            current_image[:, int(current_image.shape[1] / 2), :] = cross_grey_value

        if current_image.shape[2] % 2 == 0:
            middle = int(np.floor(current_image.shape[2] / 2))
            current_image[:, :, middle : middle + 1] = cross_grey_value

        else:
            current_image[:, :, int(current_image.shape[2] / 2)] = cross_grey_value

        # Add small stripes to indicate steps as well.
        middle = [
            x // 2 for x in current_image.shape[1:]
        ]  # Ignore that there might not be an exact middle.
        distances = [np.array(range(0, x, 10)) for x in middle]
        big_distances = [np.array(range(0, x, 100)).astype(np.uint16) for x in middle]

        # Put a stripe in all directions.
        half_len = 25
        current_image[
            :, middle[0] + distances[0], middle[1] - half_len : middle[1] + half_len
        ] = cross_grey_value
        current_image[
            :, middle[0] - distances[0], middle[1] - half_len : middle[1] + half_len
        ] = cross_grey_value
        current_image[
            :, middle[0] - half_len : middle[0] + half_len, middle[1] + distances[1]
        ] = cross_grey_value
        current_image[
            :, middle[0] - half_len : middle[0] + half_len, middle[1] - distances[1]
        ] = cross_grey_value

        # Put a *big* stripe in all directions.
        half_len = 50
        current_image[
            :, middle[0] + big_distances[0], middle[1] - half_len : middle[1] + half_len
        ] = cross_grey_value
        current_image[
            :, middle[0] - big_distances[0], middle[1] - half_len : middle[1] + half_len
        ] = cross_grey_value
        current_image[
            :, middle[0] - half_len : middle[0] + half_len, middle[1] + big_distances[1]
        ] = cross_grey_value
        current_image[
            :, middle[0] - half_len : middle[0] + half_len, middle[1] - big_distances[1]
        ] = cross_grey_value

        # Add the vertical bar that blocks zero-order light.
        current_image[:, :, middle[1] - 110]
        current_image[:, :, middle[1] + 110]

        # Only do the computations once.
        if self.draw_pixels.shape[0] == 0:
            # Add stimulation circle to the image.
            indices = self.get_circle_indices(
                current_image.shape[1:], 1003
            )  # 1003 was manually calculated.
            self.draw_pixels = np.concatenate((self.draw_pixels, indices), axis=0)

            # Add the two halve-circles which are part of the zero-order block.
            halve_indices = self.get_circle_indices(current_image.shape[1:], 221)
            is_left_halve = (
                halve_indices[:, 1] > middle[1]
            )  # Allows us to negate for right_halve.
            left_halve = halve_indices[is_left_halve]
            right_halve = halve_indices[~is_left_halve]

            # Move the circles to the edge of the bar.
            left_halve[:, 1] += 110
            right_halve[:, 1] -= 110

            self.draw_pixels = np.concatenate((self.draw_pixels, left_halve), axis=0)
            self.draw_pixels = np.concatenate((self.draw_pixels, right_halve), axis=0)

        # Draw circle based on pixels.
        current_image[
            :, self.draw_pixels[:, 0], self.draw_pixels[:, 1]
        ] = cross_grey_value

        # If not volumetric or out of range, reset indexes:
        if current_image.shape[0] == 1:
            self.viewer.dims.reset()
        self.frame_layer.data = current_image
        # self.frame_layer.scale = [self.voxel_size[0] / self.voxel_size[1], 1.0, 1.0]

        # If experiment is started/ended call the display drift function
        if self.is_exp_started:
            self.display_drift(frame=current_image, is_exp_running=True)
            self.is_exp_started = False
        elif self.is_exp_ended:
            self.display_drift(is_exp_running=False)
            self.is_exp_ended = False

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
            self.frame_layer.scale = [self.voxel_size[0] / self.voxel_size[1], 1.0, 1.0]
            self.drift_layer.scale = [self.voxel_size[0] / self.voxel_size[1], 1.0, 1.0]
        else:
            self.frame_layer.scale = [1.0, 1.0, 1.0]
            self.drift_layer.scale = [1.0, 1.0, 1.0]

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

    def activate_drift_reference(self) -> None:
        """
        If active the first volume during the experiment
        will be saved and overlayed to the viewer
        """
        self.is_drift_active = not self.is_drift_active

    def display_drift_reference(self) -> None:
        """
        Toggles the visualization of the drift layer on/off
        """
        # if not None or empty
        if self.drift_layer.data is not None or np.any(self.drift_layer.data):
            self.drift_layer.visible = not self.drift_layer.visible

    def display_frame_reference(self) -> None:
        """
        Toggles the visualization of the main layer on/off
        """
        self.frame_layer.visible = not self.frame_layer.visible

    def display_drift(self, frame=None, is_exp_running=False) -> None:
        """
        If the conditions are right displays the drift layer,
        else it will disable the buttons and reset the drift layer

        Args:
            frame (np.ndarray): current image used to refresh the viewer after the experiment started.
                                Defaults to None.
            is_exp_running (bool): check to discriminate between start and end of the experiment.
                                            Defaults to False.
        """
        # if experiment started, button is selected and frame has been generated
        if is_exp_running and self.is_drift_active and frame is not None:
            # set layer data
            self.drift_layer.data = frame
            self.drift_layer.contrast_limits = self.frame_layer.contrast_limits
            # set buttons
            # -> drift is active -> all buttons on
            self.display_drift_chk.setEnabled(True)
            self.display_drift_chk.setChecked(True)
            self.display_frame_chk.setChecked(True)
            self.display_frame_chk.setEnabled(True)
            # set layer visibility
            self.drift_layer.visible = True
        else:
            # set buttons
            # -> drift inactive all buttons off
            self.display_drift_chk.setEnabled(False)
            self.display_drift_chk.setChecked(False)
            self.display_frame_chk.setChecked(True)  # live view on
            self.display_frame_chk.setEnabled(False)
            # set layer visibility
            self.drift_layer.visible = False
            self.frame_layer.visible = True  # live view on
            # reset drift image
            self.drift_layer.data = self.frame_layer.data * 0


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
