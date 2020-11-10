from PyQt5.QtWidgets import QApplication
import qdarkstyle
from sashimi.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon
from sashimi.state import State
from pathlib import Path


def test_main(qtbot):
    app = QApplication([])
    style = qdarkstyle.load_stylesheet_pyqt5()
    app.setStyleSheet(style)
    st = State()
    main_window = MainWindow(st, style)
    icon_dir = (Path(__file__).parents[0]).resolve() / "icons/main_icon.png"
    app.setWindowIcon(QIcon(str(icon_dir)))  # PyQt does not accept Path
    main_window.show()
    qtbot.wait(1000)
    # exp.end_protocol(save=False)
    main_window.closeEvent(None)
    qtbot.wait(1000)
