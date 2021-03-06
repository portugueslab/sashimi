from PyQt5.QtWidgets import QLabel, QStatusBar

from sashimi.state import GlobalState, State, get_voxel_size
from sashimi.config import read_config

conf = read_config()


class StatusBarWidget(QStatusBar):
    """Lower bar of the interface with info on framerate, image size and voxel size."""

    def __init__(self, state: State, timer):
        super().__init__()
        self.state = state
        self.timer = timer

        self.framerate_lbl = QLabel("0 Hz")
        self.frame_size_lbl = QLabel()
        self.voxel_size_lbl = QLabel()
        self.interplane_lbl = QLabel()
        self.warning_lbl = QLabel()
        self.warning_lbl.setStyleSheet("color: red")

        self.addPermanentWidget(self.framerate_lbl)
        self.addPermanentWidget(self.frame_size_lbl)
        self.addPermanentWidget(self.voxel_size_lbl)
        self.addPermanentWidget(self.interplane_lbl)
        self.addPermanentWidget(self.warning_lbl)

        self.voxel_size = None

        self.timer.timeout.connect(self.update_all_labels)

    def update_all_labels(self):
        self.update_framerate_view()
        self.update_frame_size()
        self.update_voxel_size()
        self.update_warning_msg()
        if self.state.global_state == GlobalState.PAUSED:
            self.hide()
        else:
            self.show()

    def update_framerate_view(self):
        """Update the framerate and check whether it is fast enough for the current
        parameters configuration.
        """

        frame_rate = self.state.get_triggered_frame_rate()

        if frame_rate is None:
            return

        self.framerate_lbl.setText("Framerate: {} Hz".format(round(frame_rate, 2)))

        # Find the expected framerate depending on the global state
        expected_frame_rate_dict = {
            GlobalState.PAUSED: None,
            GlobalState.PREVIEW: None,
            GlobalState.VOLUME_PREVIEW: self.state.volume_setting.frequency
            * self.state.n_planes,
            GlobalState.PLANAR_PREVIEW: self.state.single_plane_settings.frequency,
        }

        expected_frame_rate = expected_frame_rate_dict[self.state.global_state]

        # Add warning if we are lagging:
        if expected_frame_rate and expected_frame_rate > (frame_rate * 1.1):
            self.showMessage("Camera lagging behind")
            self.framerate_lbl.setStyleSheet("color: red")
        else:
            self.showMessage("")
            self.framerate_lbl.setStyleSheet("color: white")

    def update_frame_size(self):
        self.frame_size_lbl.setText(
            f"Frame shape: {self.state.camera_settings.roi[2]} x {self.state.camera_settings.roi[3]} pixels"
        )

    def update_voxel_size(self):
        self.voxel_size = get_voxel_size(
            self.state.volume_setting, self.state.camera_settings
        )
        if (
            self.state.voxel_size
            and self.state.global_state == GlobalState.VOLUME_PREVIEW
        ):
            self.voxel_size_lbl.setText(
                f"Voxel size: {self.voxel_size[0]:.2f} x {self.voxel_size[1]:.2f} x {self.voxel_size[2]:.2f} um"
            )
        else:
            self.voxel_size_lbl.setText(
                f"Pixel size: {self.voxel_size[1]:.2f} x {self.voxel_size[2]:.2f} um"
            )

    def update_warning_msg(self):
        if (
            self.state.global_state == GlobalState.VOLUME_PREVIEW
            and len(self.state.calibration.calibrations_points) < 2
        ):
            self.warning_lbl.setText("Not enough calibration points")
