from PyQt5.QtWidgets import QApplication
import qdarkstyle
from lightsheet.state import State
from lightsheet.gui.main_gui import ContainerWidget
from PyQt5.QtGui import QIcon


if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setApplicationName("Lightsheet control")
    app.setWindowIcon(QIcon(r"icons/main_icon.png"))
    st = State()
    wid = ContainerWidget(st)
    wid.show()
    app.exec()