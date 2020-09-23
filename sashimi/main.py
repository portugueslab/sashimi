from PyQt5.QtWidgets import QApplication
import qdarkstyle
from sashimi.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click
from sashimi.config import cli_edit_config
from sashimi.state import State


@click.command()
@click.option("--scanning", default="mock", help="The scanning interface")
def main(scanning, **kwargs):
    cli_edit_config("scanning", scanning)

    # TODO configure logging with CLI

    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("Sashimi")
    st = State()
    main_window = MainWindow(st)
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    main_window.show()
    app.exec()
