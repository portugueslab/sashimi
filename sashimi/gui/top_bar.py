from PyQt5.QtWidgets import QToolBar, QHBoxLayout, QLabel, QProgressBar, QMessageBox

from sashimi.gui.buttons import ToggleIconButton
from sashimi.state import State, GlobalState


class TopWidget(QToolBar):
    def __init__(self, st: State, timer):
        super().__init__()
        self.state = st
        self.timer = timer
        self.setLayout(QHBoxLayout())

        # TODO: This was in Stytra figure out what it does, whether it has to be intercalated between widgets
        self.addSeparator()

        self.experiment_toggle_btn = ToggleIconButton(
            icon_off="play", icon_on="stop", action_on="play", on=False
        )
        self.experiment_toggle_btn.clicked.connect(self.change_experiment_state)
        self.experiment_progress = QProgressBar()
        self.experiment_progress.setFormat("Volume %v of %m")
        self.lbl_experiment_progress = QLabel()
        self.experiment_progress.hide()
        self.lbl_experiment_progress.hide()

        self.overwrite_dialog = QMessageBox()
        self.btn_overwrite_ok = self.overwrite_dialog.addButton(
            self.overwrite_dialog.Ok
        )
        self.btn_overwrite_abort = self.overwrite_dialog.addButton(
            self.overwrite_dialog.Abort
        )

        self.layout().addWidget(self.experiment_progress)
        self.layout().addWidget(self.lbl_experiment_progress)
        self.layout().addWidget(self.experiment_toggle_btn)

        self.timer.timeout.connect(self.refresh_progress_bar)
        self.timer.timeout.connect(self.show_hide_toggle_btn)
        self.btn_overwrite_ok.clicked.connect(self.state.start_experiment)

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

    # TODO: Rethink logic here to ensure button and state are coordinated
    def change_experiment_state(self):
        if self.state.is_saving_event.is_set():
            # Here what happens if experiment is aborted
            self.state.end_experiment()
        else:
            if self.state.save_settings.overwrite_save_folder == 1:
                self.overwrite_alert_popup()
            else:
                self.state.start_experiment()

    def overwrite_alert_popup(self):
        self.overwrite_dialog.setIcon(QMessageBox.Warning)
        self.overwrite_dialog.setWindowTitle("Overwrite alert!")
        self.overwrite_dialog.setText(
            "You are overwriting an existing folder with data. \n\n "
            "Press ok to start the experiment anyway or abort to change saving location."
        )
        self.overwrite_dialog.show()

    def show_hide_toggle_btn(self):
        if self.state.global_state == GlobalState.VOLUME_PREVIEW or\
                GlobalState.EXPERIMENT_RUNNING or\
                GlobalState.PLANAR_PREVIEW:
            self.experiment_toggle_btn.show()
        else:
            self.experiment_toggle_btn.hide()
