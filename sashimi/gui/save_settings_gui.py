from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QDialog,
    QTextEdit,
)
from PyQt5.QtCore import pyqtSignal, Qt
from sashimi.state import State
from pathlib import Path
from datetime import datetime
import markdown
from sashimi.config import read_config

conf = read_config()
PRESETS_PATH = Path(conf["default_paths"]["presets"])
INSTRUCTIONS_PATH = Path(conf["default_paths"]["scope_instructions"])


class SavingSettingsWidget(QWidget):
    """Widget to load and save the state of the GUI with the acquisition settings.

    Parameters
    ----------
    st : State object

    Signals
    -------
    sig_params_loaded
        Signal emitted when new parameters are loaded.

    """

    sig_params_loaded = pyqtSignal()

    def __init__(self, st: State):
        super().__init__()
        self.state = st

        self.setLayout(QVBoxLayout())
        self.btn_load = QPushButton("Load settings")
        self.btn_save = QPushButton("Save settings")

        self.layout().addWidget(self.btn_load)
        self.layout().addWidget(self.btn_save)

        self.btn_load.clicked.connect(self.load)
        self.btn_save.clicked.connect(self.save)

        # Prepare scope manual window, if path for scope instructions is provided:
        if INSTRUCTIONS_PATH.exists():
            with open(INSTRUCTIONS_PATH) as f:
                instructions = f.read()

            self.html_markdown = markdown.markdown(instructions)
            self.instructions = QTextEdit(self.html_markdown)
            self.instructions.setReadOnly(True)
            self.layout().addWidget(self.btn_instructions)
            self.popup_window.setLayout(QVBoxLayout())
            self.popup_window.layout().addWidget(self.instructions)

            self.popup_window = QDialog(
                None,
                Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
            )

            self.btn_instructions = QPushButton("User guide")
            self.btn_instructions.clicked.connect(self.popup_window.show)

    def load(self):
        file, _ = QFileDialog.getOpenFileName(
            None, "Open settings file", str(PRESETS_PATH), "*.json"
        )

        if Path(file).is_file():
            self.state.restore_tree(file)
            self.sig_params_loaded.emit()  # TODO this should maybe be exposed through the main window widget

    def save(self):
        filename = datetime.now().strftime("%y%m%d %H%M%S.json")
        file, _ = QFileDialog.getSaveFileName(parent=self, caption="Save settings file",
                                              directory=str(PRESETS_PATH / filename), filter="*.json")

        if Path(file).is_file():
            self.state.save_tree(file)
