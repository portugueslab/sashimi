from PyQt5.QtWidgets import (
    QLabel,
    QStatusBar,
    QProgressBar
)

from sashimi.state import GlobalState, State, get_voxel_size
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
        self.interplane_lbl = QLabel()
        self.experiment_progress = QProgressBar()
        self.experiment_progress.setFormat("Volume %v of %m")
        self.lbl_experiment_progress = QLabel()
        self.experiment_progress.hide()
        self.lbl_experiment_progress.hide()

        self.addPermanentWidget(self.framerate_lbl)
        self.addPermanentWidget(self.frame_size_lbl)
        self.addPermanentWidget(self.voxel_size_lbl)
        self.addPermanentWidget(self.interplane_lbl)
        self.addPermanentWidget(self.experiment_progress)
        self.addPermanentWidget(self.lbl_experiment_progress)

        self.voxel_size = None

        self.timer.timeout.connect(self.update_all_labels)

    def update_all_labels(self):
        self.update_framerate_view()
        self.update_frame_size()
        self.update_voxel_size()
        self.refresh_progress_bar()
        if self.state.global_state == GlobalState.PAUSED:
            self.hide()
        else:
            self.show()

    def update_framerate_view(self):
        """Update the framerate and check whether it is fast enough for the current
        parameters configuration.
        """

        frame_rate = self.state.get_triggered_frame_rate()
        if frame_rate is not None:
            self.framerate_lbl.setText(
                "Framerate: {} Hz".format(round(frame_rate, 2))
            )

            # Find the expected framerate depending on the global state
            if self.state.global_state == GlobalState.PREVIEW:
                expected_frame_rate = None
            if self.state.global_state == GlobalState.VOLUME_PREVIEW:
                expected_frame_rate = self.state.volume_setting.frequency * self.state.n_planes
            if self.state.global_state == GlobalState.PLANAR_PREVIEW:
                expected_frame_rate = self.state.single_plane_settings.frequency

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
        self.voxel_size = get_voxel_size(self.state.volume_setting, self.state.camera_settings)
        if self.state.voxel_size and self.state.global_state == GlobalState.VOLUME_PREVIEW:
            self.voxel_size_lbl.setText(
                f"Voxel size: {self.voxel_size[0]} x {self.voxel_size[1]} x {self.voxel_size[2]} um"
            )
            #TODO format to approximate at 2 numbers
        else:
            self.voxel_size_lbl.setText(
                f"Pixel size: {self.voxel_size[1]} x {self.voxel_size[2]} um"
            )

    def refresh_progress_bar(self):
        sstatus = self.state.get_save_status()
        if sstatus is not None:
            self.experiment_progress.show()
            self.lbl_experiment_progress.show()
            self.experiment_progress.setMaximum(sstatus.target_params.n_volumes)
            self.experiment_progress.setValue(sstatus.i_volume)
            self.lbl_experiment_progress.setText(
                "Saved files: {}".format(sstatus.i_chunk)
            )
