from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QDialog,
    QTextEdit
)
from PyQt5.QtCore import pyqtSignal, Qt
from sashimi.state import State
from pathlib import Path
from datetime import datetime
import markdown
from sashimi.config import read_config

conf = read_config()
PRESETS_PATH = conf["default_paths"]["presets"]


class SavingSettingsWidget(QWidget):
    sig_params_loaded = pyqtSignal()

    def __init__(self, st: State):
        super().__init__()
        self.state = st
        self.setLayout(QVBoxLayout())
        self.btn_load = QPushButton("Load settings")
        self.btn_save = QPushButton("Save settings")
        self.btn_instructions = QPushButton("User guide")
        parent_dir = (Path(__file__).parents[2]).resolve()
        with open(parent_dir / "lightsheet_procedure.md") as f:
            instructions = f.read()
        self.html_markdown = markdown.markdown(instructions)
        self.instructions = QTextEdit(self.html_markdown)
        self.instructions.setReadOnly(True)
        self.popup_window = QDialog(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.layout().addWidget(self.btn_load)
        self.layout().addWidget(self.btn_save)
        self.layout().addWidget(self.btn_instructions)
        self.popup_window.setLayout(QVBoxLayout())
        self.popup_window.layout().addWidget(self.instructions)
        self.btn_load.clicked.connect(self.load)
        self.btn_save.clicked.connect(self.save)
        self.btn_instructions.clicked.connect(self.popup_window.show)

    def load(self):
        file, _ = QFileDialog.getOpenFileName(None, "Open settings file", PRESETS_PATH, "*.json")
        if Path(file).is_file():
            self.state.restore_tree(file)
            self.sig_params_loaded.emit()

    def save(self):
        pth = Path(PRESETS_PATH)
        filename = datetime.now().strftime("%y%m%d %H%M%S.json")
        self.state.save_tree(pth / filename)
