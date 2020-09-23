from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QCheckBox, QMessageBox, QLabel
from sashimi.hardware.scanning.scanloops import ExperimentPrepareState
from sashimi.gui.scanning_gui import STATE_TEXTS
from sashimi.gui.calibration_gui import NoiseSubtractionSettings
from lightparam.gui import ParameterGui


class ScanlessWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.timer = timer
        self.setLayout(QVBoxLayout())
        self.btn_start = QPushButton()
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.change_experiment_state)
        self.chk_pause = QCheckBox("Pause after experiment")

        self.overwrite_dialog = QMessageBox()
        self.btn_overwrite_ok = self.overwrite_dialog.addButton(
            self.overwrite_dialog.Ok
        )
        self.btn_overwrite_abort = self.overwrite_dialog.addButton(
            self.overwrite_dialog.Abort
        )

        self.layout().addWidget(self.btn_start)
        self.layout().addWidget(self.chk_pause)

        self.updateBtnText()
        self.timer.timeout.connect(self.updateBtnText)

        self.chk_pause.clicked.connect(self.change_pause_status)
        self.btn_overwrite_ok.clicked.connect(self.state.start_experiment)

        self.chk_pause.click()

        self.lbl_calibration = QLabel("")
        self.chk_noise_subtraction = QCheckBox()
        self.chk_noise_subtraction.setText("Enable noise subtraction")
        self.param_n_noise_subtraction = NoiseSubtractionSettings()
        self.wid_n_noise_subtraction = ParameterGui(self.param_n_noise_subtraction)

        self.layout().addWidget(self.chk_noise_subtraction)
        self.layout().addWidget(self.wid_n_noise_subtraction)

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
            "Press ok to start the experiment anyway or abort to change saving folder."
        )
        self.overwrite_dialog.show()

    def set_noise_subtraction_mode(self):
        # check by the status of the check box
        if self.state.calibration_ref is None:
            self.show_dialog_box(finished=False)
        else:
            self.state.reset_noise_subtraction()

    def show_dialog_box(self, finished=True, deactivated=False):
        # TODO split into two functions
        self.dialog_box.setIcon(QMessageBox.Information)
        self.dialog_box.setWindowTitle("Noise subtraction mode")
        self.dialog_box.setText(
            "Turn off the lights. \n\n You will have to perform noise subtraction again if camera settings change "
        )
        if deactivated:
            self.dialog_box.setText("Noise subtraction has been deactivated")
        elif not finished:
            self.dialog_button.clicked.connect(self.perform_noise_subtraction)
        else:
            self.dialog_button.clicked.disconnect(self.perform_noise_subtraction)
            self.dialog_box.setText("Noise subtraction completed")
        self.dialog_box.show()

    def perform_noise_subtraction(self):
        self.state.obtain_noise_average(
            n_images=self.param_n_noise_subtraction.average_n_frames
        )
        self.show_dialog_box(finished=True)
