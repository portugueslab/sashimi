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
PRESETS_PATH = conf["default_paths"]["presets"]


class SavingSettingsWidget(QWidget):
    sig_params_loaded = pyqtSignal()

    def __init__(self, st: State):
        super().__init__()
        self.state = st
        self.setLayout(QVBoxLayout())
        parent_dir = (Path(__file__).parents[2]).resolve()
        with open(parent_dir / "lightsheet_procedure.md") as f:
            instructions = f.read()
        self.html_markdown = markdown.markdown(instructions)
        self.instructions = QTextEdit(self.html_markdown)
        self.instructions.setReadOnly(True)
        self.popup_window = QDialog(
            None,
            Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
        )
        self.popup_window.setLayout(QVBoxLayout())
        self.popup_window.layout().addWidget(self.instructions)

    def show_instructions(self):
        self.popup_window.resize(1200, 800)
        self.popup_window.show()

    def load(self):
        file, _ = QFileDialog.getOpenFileName(
            None, "Open settings file", PRESETS_PATH, "*.json"
        )
        if Path(file).is_file():
            self.state.restore_tree(file)
            self.sig_params_loaded.emit()

    def save(self):
        file, _ = QFileDialog.getSaveFileName(
            None, "Open settings file", PRESETS_PATH, "*.json"
        )
        self.state.save_tree(file)
