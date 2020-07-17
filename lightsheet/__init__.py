from PyQt5.QtWidgets import QApplication
import qdarkstyle
from lightsheet.state import State
from lightsheet.gui.main_gui import MainWindow
from PyQt5.QtGui import QIcon

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("Lightsheet control")
    st = State(sample_rate=40000)
    main_window = MainWindow(st)
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    main_window.show()
    app.exec()
