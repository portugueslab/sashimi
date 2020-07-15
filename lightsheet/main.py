from PyQt5.QtWidgets import QApplication
import qdarkstyle
from lightsheet.state import State
from lightsheet.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
import click


@click.command()
@click.option("--sample-rate", default=40000, help="")
def main(sample_rate):
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("Lightsheet control")
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    st = State(sample_rate=sample_rate)
    main_window = MainWindow(st)
    main_window.show()
    app.exec()