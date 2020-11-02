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
        self.update_framerate()
        self.update_frame_size()
        self.update_voxel_size()
        self.refresh_progress_bar()

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
        binning = int(self.state.camera_settings.binning)
        self.frame_size_lbl.setText(
            f"Frame shape: {int(dims[0] / binning)} x {int(dims[1] / binning)} pixels"
        )

    def update_voxel_size(self):
        self.voxel_size = get_voxel_size(self.state.volume_setting, self.state.camera_settings)
        if self.state.voxel_size and self.state.global_state == GlobalState.VOLUME_PREVIEW:
            self.voxel_size_lbl.setText(
                f"Voxel size: {self.voxel_size[0]} x {self.voxel_size[1]} x {self.voxel_size[2]} um"
            )
        else:
            self.voxel_size_lbl.setText(
                f"Voxel size: {self.voxel_size[1]} x {self.voxel_size[2]} um"
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
