from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QFileDialog
)
from lightparam.gui import ParameterGui
from pathlib import Path


class SaveWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.state = state
        self.timer = timer
        self.setLayout(QVBoxLayout())

        self.current_camera_settings = None

        self.wid_save_options = ParameterGui(state.save_settings)
        self.n_frames_auto_button = QPushButton()
        self.save_location_button = QPushButton()
        self.auto_button_label = QLabel("")

        self.layout().addWidget(self.wid_save_options)
        self.layout().addWidget(self.n_frames_auto_button)
        self.layout().addWidget(self.auto_button_label)
        self.layout().addWidget(self.save_location_button)

        self.set_locationbutton()
        self.n_frames_auto_button.setText("Auto calculate number of frames")

        self.save_location_button.clicked.connect(self.set_save_location)
        self.n_frames_auto_button.clicked.connect(self.auto_calculate_required_n_frames)

    def set_save_location(self):
        save_dir = QFileDialog.getExistingDirectory()
        self.state.save_settings.save_dir = save_dir
        self.set_locationbutton()

    def set_locationbutton(self):
        pathtext = self.state.save_settings.save_dir
        # check if there is a stack in this location
        if (Path(pathtext) / "original" / "stack_metadata.json").is_file():
            self.save_location_button.setText("Overwrite " + pathtext)
            self.save_location_button.setStyleSheet(
                "background-color:#b5880d; border-color:#fcc203"
            )
        else:
            self.save_location_button.setText("Save in " + pathtext)
            self.save_location_button.setStyleSheet("")

    def auto_calculate_required_n_frames(self):
        if self.state.save_settings.experiment_duration != 0 and (
                self.state.status.scanning_state == "Planar" or
                self.state.status.scanning_state == "Volume"
        ):
            self.current_camera_settings = self.state.get_camera_settings()
            self.state.save_settings.n_frames = self.current_camera_settings.n_frames_duration
            self.auto_button_label.setText("")
        else:
            self.auto_button_label.setText(
                "\n".join(
                    [
                        "Unable to calculate number of frames for the experiment.",
                        "This feature will only work in Planar or Volume modes.",
                        "Check that Stytra is running"
                     ]
                )
            )
