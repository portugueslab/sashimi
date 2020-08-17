from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QCheckBox,
    QMessageBox,
)
from PyQt5.QtCore import QTimer
from shirashi.scanning import ExperimentPrepareState


STATE_TEXTS = {
    ExperimentPrepareState.NO_TRIGGER: "Start recording",
    ExperimentPrepareState.PREVIEW: "Start recording",
    ExperimentPrepareState.EXPERIMENT_STARTED: "Recording started. Press to abort",
}


class TBDWidget(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state

    def refresh_widgets(self):
        pass


class ExperimentWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.timer = timer
        self.setLayout(QVBoxLayout())
        self.timer_scope_info = QTimer()
        self.timer_scope_info.setInterval(500)
        self.btn_start = QPushButton()
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.change_experiment_state)
        self.chk_pause = QCheckBox("Pause after experiment")

        self.dialog_box = QMessageBox()
        self.dialog_ok_button = self.dialog_box.addButton(self.dialog_box.Ok)
        self.dialog_abort_button = self.dialog_box.addButton(self.dialog_box.Abort)
        self.override_overwrite = False

        self.layout().addWidget(self.btn_start)
        self.layout().addWidget(self.chk_pause)

        self.timer_scope_info.start()

        self.updateBtnText()
        self.timer.timeout.connect(self.updateBtnText)

        self.chk_pause.clicked.connect(self.change_pause_status)
        self.dialog_ok_button.clicked.connect(self.overwrite_anyway)

        self.chk_pause.click()

    def updateBtnText(self):
        self.btn_start.setText(STATE_TEXTS[self.state.experiment_state])
        if self.state.experiment_state == ExperimentPrepareState.PREVIEW:
            self.btn_start.setChecked(False)
        if (
            self.state.experiment_state == ExperimentPrepareState.NO_TRIGGER
            or self.state.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED
        ):
            self.btn_start.setChecked(True)


    def change_pause_status(self):
        self.state.pause_after = self.chk_pause.isChecked()

    def change_experiment_state(self):
        if self.state.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED:
            # Here what happens if experiment is aborted
            self.state.saver.saving_signal.clear()
        elif (
            self.state.save_settings.overwrite_save_folder == 1
            and not self.override_overwrite
        ):
            self.overwrite_alert_popup()
            self.override_overwrite = False
        else:
            self.state.toggle_experiment_state()

    def overwrite_alert_popup(self):
        self.dialog_box.setIcon(QMessageBox.Warning)
        self.dialog_box.setWindowTitle("Overwrite alert!")
        self.dialog_box.setText(
            "You are overwriting an existing folder with data. \n\n "
            "Press ok to start the experiment anyway or abort to change saving folder."
        )
        self.dialog_box.show()

    def overwrite_anyway(self):
        self.override_overwrite = True
        self.change_experiment_state()
