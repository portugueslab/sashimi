from PyQt5.QtWidgets import QApplication
import qdarkstyle
from shirashi.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click
from shirashi.config import _cli_modify_config
from shirashi.state import State


@click.command()
@click.option("--sample-rate", default=40000, help="")
@click.option("--scopeless", is_flag=True, help="")
def main(sample_rate, scopeless):
    if scopeless:
        _cli_modify_config("edit", "scopeless", True)
    else:
        _cli_modify_config("edit", "scopeless", False)
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("Shirashi")
    st = State(sample_rate=sample_rate)
    main_window = MainWindow(st)
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    main_window.show()
    app.exec()
