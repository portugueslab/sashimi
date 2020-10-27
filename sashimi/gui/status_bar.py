from PyQt5.QtWidgets import (
    QLabel,
    QStatusBar
)

from sashimi.state import GlobalState, convert_camera_params, State, get_voxel_size
from sashimi.config import read_config

conf = read_config()


class StatusBarWidget(QStatusBar):
    def __init__(self, state: State, timer):
        super().__init__()
        self.state = state
        self.timer = timer

        self.framerate_lbl = QLabel("0 Hz")
        self.frame_size_lbl = QLabel()
        self.voxel_size_lbl = QLabel()

        self.addPermanentWidget(self.framerate_lbl)
        self.addPermanentWidget(self.frame_size_lbl)
        self.addPermanentWidget(self.voxel_size_lbl)

        self.timer.timeout.connect(self.update_all_labels)

    def update_all_labels(self):
        self.update_framerate()
        self.update_frame_size()
        self.update_voxel_size()

    def update_framerate(self):
        frame_rate = self.state.get_triggered_frame_rate()
        if frame_rate is not None:
            self.framerate_lbl.setStyleSheet("color: white")
            expected_frame_rate = None
            if self.state.global_state == GlobalState.PREVIEW:
                self.framerate_lbl.setText(
                    "Framerate: {} Hz".format(round(frame_rate, 2))
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

            if expected_frame_rate and expected_frame_rate > (frame_rate * 1.1):
                self.showMessage("Camera lagging behind")
                self.framerate_lbl.setStyleSheet("color: red")
            else:
                self.framerate_lbl.setStyleSheet("color: white")

    def update_frame_size(self):
        dims = self.state.get_frame_size()
        binning = convert_camera_params(self.state.camera_settings).binning

        self.frame_size_lbl.setText(
            f"Frame shape: {int(dims[0] / binning)} x {int(dims[1] / binning)} pixels"
        )

    def update_voxel_size(self):
        voxel_size = get_voxel_size(self.state.volume_setting, self.state.camera_settings)
        if self.state.voxel_size and self.state.global_state == GlobalState.VOLUME_PREVIEW:
            self.voxel_size_lbl.setText(
                f"Voxel size: {voxel_size[0]} x {voxel_size[1]} x {voxel_size[2]} um"
            )
        else:
            self.voxel_size_lbl.setText(
                f"Voxel size: {voxel_size[1]} x {voxel_size[2]} um"
            )

    # TODO: Fix this function copy-pasted from original place, add self.update_alignment() to self.update_all_labels()
    def update_alignment(self):
        scan_width = (
            self.state.volume_setting.scan_range[1]
            - self.state.volume_setting.scan_range[0]
        )
        num_planes = (
            self.state.volume_setting.n_planes
            - self.state.volume_setting.n_skip_start
            - self.state.volume_setting.n_skip_end
        )
        plane_distance = (
            scan_width / num_planes - self.state.scope_alignment_info.waist_width
        )
        if plane_distance > 0:
            self.lbl_interplane_distance.setText(
                "With the current configuration, distance between planes is {:0.2f} um".format(
                    plane_distance
                )
            )
        if plane_distance <= 0:
            self.lbl_interplane_distance.setText(
                "The current configuration covers the whole volume. Plane overlap is {:0.2f} um".format(
                    -plane_distance
                )
            )
