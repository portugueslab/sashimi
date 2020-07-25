from PyQt5.QtWidgets import QApplication
import qdarkstyle
from lightsheet.state import State
from lightsheet.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click


@click.command()
@click.option("--sample-rate", default=40000, help="")
@click.option(
    "--debug",
    default="",
    help="Pass --debug on to launch Sashimi with simulated hardware"
)
def main(sample_rate, debug):
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("DSLM control")
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    if debug == "on" or debug == "On" or debug == "ON":
        dry_run = True
    else:
        dry_run = False
    st = State(sample_rate=sample_rate, dry_run=dry_run)
    main_window = MainWindow(st)
    main_window.show()
    app.exec()
