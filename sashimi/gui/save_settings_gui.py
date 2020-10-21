from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QDialog,
    QTextEdit,
    QLineEdit,
    QLabel,
    QComboBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from sashimi.state import State
from pathlib import Path
import markdown
from sashimi.config import read_config
from webbrowser import open_new_tab
from typing import Optional
from warnings import warn

conf = read_config()
PRESETS_PATH = conf["default_paths"]["presets"]
docs_url = "https://portugueslab.github.io/sashimi/"


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
        self.popup_window.setWindowTitle("User guide")
        self.popup_window.setLayout(QVBoxLayout())
        self.popup_window.layout().addWidget(self.instructions)

        self.keys_list, self.inverse_key_dict = self._get_nested_keys(conf)
        self.config_combo = QComboBox()
        self.config_combo.addItems(self.keys_list)
        self.config_key_value = QTextEdit(conf[self.config_combo.currentText()])
        self.conf_window = QDialog(
            None,
            Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
        )
        self.conf_window.setWindowTitle("Configure")
        self.conf_window.setLayout(QVBoxLayout())
        self.conf_window.layout().addWidget(self.config_combo)
        self.conf_window.layout().addWidget(self.config_key_value)

        self.config_combo.currentTextChanged.connect(self._update_config_key_value)

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

    @staticmethod
    def open_docs():
        open_new_tab(docs_url)

    # TODO: Text editor for markdown
    # TODO: Should be a 2-column structure w/ raw modifiable text left and markdown live display right
    def edit_guide(self):
        pass

    def _get_nested_keys(self, this_dict: dict, nesting_level: Optional[list] = None) -> {list, dict}:
        keys = []
        inverse_keys = {}
        if not nesting_level:
            nesting_level = []
        for key, value in this_dict.items():
            if type(value) is not dict:
                if len(nesting_level) == 0:
                    keys.append(key)
                    inverse_keys[key] = key
                else:
                    nesting_string = " / ".join(nesting_level) + " / " + key
                    keys.append(nesting_string)
                    inverse_keys[nesting_string] = key
            else:
                nesting_level.append(key)
                nested_keys, nested_inverse_keys = self._get_nested_keys(this_dict[key], nesting_level)
                keys.extend(nested_keys)
                nested_inverse_keys = {**inverse_keys,**nested_inverse_keys}
                nesting_level = nesting_level[:-1]

        return keys, inverse_keys

    def edit_config(self):
        self.conf_window.resize(250, 100)
        self.conf_window.show()

    def _update_config_key_value(self):
        """
        Supports up to 2-level nesting
        """
        address = self.inverse_key_dict[self.config_combo.currentText()]
        print(address)
        if len(address) == 1:
            self.config_key_value.setText(conf[address][0])
        elif len(address) == 2:
            self.config_key_value.setText(conf[address][0][1][2])
        elif len(address) == 3:
            self.config_key_value.setText(conf[address][0][1][2][3])
        else:
            warn("Dictionary nesting level equal or greater than 3 not supported", Warning)
