from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QDialog,
    QTextEdit
)
from PyQt5.QtCore import pyqtSignal, Qt
from lightsheet.state import State
from pathlib import Path
from datetime import datetime
import markdown

DEFAULT_SETTINGS_PATH = "C:/Users/portugueslab/lightsheet_settings"


class SavingSettingsWidget(QWidget):
    sig_params_loaded = pyqtSignal()

    def __init__(self, st: State):
        super().__init__()
        self.state = st
        self.setLayout(QVBoxLayout())
        self.btn_load = QPushButton("Load settings")
        self.btn_save = QPushButton("Save settings")
        self.btn_instructions = QPushButton("User guide")
        f = open(r"../lightsheet_procedure.md")
        self.html_markdown = markdown.markdown(f.read())
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
        file, _ = QFileDialog.getOpenFileName(None, "Open settings file", DEFAULT_SETTINGS_PATH, "*.json")
        if Path(file).is_file():
            self.state.restore_tree(file)
            self.sig_params_loaded.emit()

    def save(self):
        pth = Path(DEFAULT_SETTINGS_PATH)
        filename = datetime.now().strftime("%y%m%d %H%M%S.json")
        self.state.save_tree(pth/filename)
