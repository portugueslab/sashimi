from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QDialog,
    QTextEdit,
    QPushButton,
    QLabel,
    QComboBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from sashimi.state import State
from pathlib import Path
import markdown
from sashimi.config import read_config, write_config_value
from webbrowser import open_new_tab
from typing import Optional
from warnings import warn
import re

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
        self.guide_window = QDialog(
            None,
            Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
        )
        self.guide_window.setWindowTitle("User guide")
        self.guide_window.setLayout(QVBoxLayout())
        self.guide_window.layout().addWidget(self.instructions)

        self.keys_list = self.nest_keys(conf)
        self.config_combo = QComboBox()
        self.config_combo.addItems(self.keys_list)
        self.config_key_value = QTextEdit(conf[self.config_combo.currentText()])
        self.conf_window = QDialog(
            None,
            Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
        )
        self.conf_window.setWindowTitle("Configure")
        self.conf_window.setLayout(QVBoxLayout())
        self.update_conf_btn = QPushButton("Apply changes to configuration file")
        self.restart_lbl = QLabel("Restart sashimi to apply changes")
        self.conf_window.layout().addWidget(self.config_combo)
        self.conf_window.layout().addWidget(self.config_key_value)
        self.conf_window.layout().addWidget(self.update_conf_btn)
        self.conf_window.layout().addWidget(self.restart_lbl)

        self.restart_lbl.hide()

        self.config_combo.currentTextChanged.connect(self._update_config_key_value)
        self.update_conf_btn.pressed.connect(self._apply_config)

    def show_instructions(self):
        self.guide_window.resize(1200, 800)
        self.guide_window.show()

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

    def nest_keys(self, this_dict: dict, nesting_level: Optional[list] = None, parent: Optional[dict] = None) -> list:
        keys = []
        if not nesting_level:
            nesting_level = []
        if not parent:
            parent = this_dict
        for key, value in this_dict.items():
            if type(value) is not dict:
                if len(nesting_level) > 0:
                    nesting_string = "-".join(nesting_level) + "-" + key
                else:
                    nesting_string = key
                keys.append(nesting_string)
            else:
                nesting_level.append(key)
                nested_keys = self.nest_keys(this_dict[key], nesting_level, parent)
                keys.extend(nested_keys)
                nesting_level.pop()

        return keys

    def edit_config(self):
        self.conf_window.resize(250, 100)
        self.conf_window.show()

    @staticmethod
    def retrieve_keys_from_nested(nested_string: str, separator: str):
        """
        separator is a symbol that delimits individual fields or levels within a string
        """
        keys = re.split("[" + separator + "]", nested_string)
        return keys

    @staticmethod
    def _search_nested_dict(query: list, target: dict):
        """
        Supports up to 3-level nesting. Returns None if nested key is not found in query
        """
        try:
            if len(query) == 1:
                value = target[query[0]]
            elif len(query) == 2:
                value = target[query[0]][query[1]]
            elif len(query) == 3:
                value = target[query[0]][query[1]][query[2]]
            else:
                warn("Dictionary nesting level equal or greater than 3 not supported", Warning)
                return
        except KeyError:
            return None

        return value

    def _update_config_key_value(self):
        config_key = self.retrieve_keys_from_nested(self.config_combo.currentText(), "-")
        value = self._search_nested_dict(config_key, conf)
        self.config_key_value.setText(str(value))

    def _apply_config(self):
        config_key = self.retrieve_keys_from_nested(self.config_combo.currentText(), "-")
        new_value = self.config_key_value.toPlainText()
        write_config_value(config_key, new_value)
        global conf
        conf = read_config()
        self.restart_lbl.show()
