from PyQt5.QtWidgets import QApplication
import qdarkstyle
from sashimi.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click
from sashimi.config import _cli_modify_config
from sashimi.state import State
import logging


@click.command()
@click.option("--sample-rate", default=40000, help="")
@click.option("--scopeless", is_flag=True, help="")
def main(sample_rate, scopeless):
    if scopeless:
        _cli_modify_config("edit", "scopeless", True)
    else:
        _cli_modify_config("edit", "scopeless", False)

    # TODO configure logging with CLI

    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("Sashimi")
    st = State(sample_rate=sample_rate)
    main_window = MainWindow(st)
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    main_window.show()
    app.exec()
