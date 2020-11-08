from PyQt5.QtWidgets import QApplication
import qdarkstyle
from sashimi.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click
from sashimi.config import cli_edit_config
from sashimi.state import State
from pathlib import Path


@click.command()
@click.option("--scopeless", is_flag=True, help="Scopeless mode for simulated hardware")
@click.option("--scanning", default="mock", help="The scanning interface")
def main(scopeless, scanning, **kwargs):
    cli_edit_config("scopeless", scopeless)
    cli_edit_config("scanning", scanning)

    # TODO configure logging with CLI

    app = QApplication([])
    style = qdarkstyle.load_stylesheet_pyqt5()
    app.setStyleSheet(style)
    app.setApplicationName("Sashimi")
    st = State()
    main_window = MainWindow(st, style)
    icon_dir = (Path(__file__).parents[0]).resolve() / "icons/main_icon.png"
    app.setWindowIcon(QIcon(str(icon_dir)))  # PyQt does not accept Path
    main_window.show()
    app.exec()
