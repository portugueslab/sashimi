from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
QFileDialog
)
from PyQt5.QtCore import pyqtSignal
from lightsheet.state import State
from pathlib import Path
from datetime import datetime

DEFAULT_SETTIGNS_PATH = "C:/Users/portugueslab/lightsheet_settings"


class SavingWidget(QWidget):
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

    def load(self):
        file, _ = QFileDialog.getOpenFileName(None, "Open settings file", DEFAULT_SETTIGNS_PATH, "*.json")
        if Path(file).is_file():
            self.state.restore_tree(file)
            self.sig_params_loaded.emit()

    def save(self):
        pth = Path(DEFAULT_SETTIGNS_PATH)
        filename = datetime.now().strftime("%y%m%d %H%M%S.json")
        self.state.save_tree(pth/filename)
