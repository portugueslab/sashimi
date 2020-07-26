from PyQt5.QtWidgets import QApplication
import qdarkstyle
from lightsheet.state import State
from lightsheet.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click


@click.command()
@click.option("--sample-rate", default=40000, help="")
@click.option("--debug", is_flag=True, help="")
def main(sample_rate, debug):
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("DSLM control")
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    st = State(sample_rate=sample_rate, dry_run=debug)
    main_window = MainWindow(st)
    main_window.show()
    app.exec()
