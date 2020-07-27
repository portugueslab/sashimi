from PyQt5.QtWidgets import QApplication
import qdarkstyle
from lightsheet.state import State
from lightsheet.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click
from lightsheet.config import _cli_modify_config


@click.command()
@click.option("--sample-rate", default=40000, help="")
@click.option("--debug", is_flag=True, help="")
def main(sample_rate, debug):
    if debug:
        _cli_modify_config("edit", "debug", True)
    else:
        _cli_modify_config("edit", "debug", False)
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("Sashimi")
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    st = State(sample_rate=sample_rate)
    main_window = MainWindow(st)
    main_window.show()
    app.exec()

