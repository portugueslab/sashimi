from sashimi.gui.main_gui import MainWindow
from sashimi.state import State, TriggerSettings
import qdarkstyle
from PyQt5.QtCore import Qt
from split_dataset import SplitDataset


class MockEvt:
    def accept(self):
        pass


def test_main(qtbot, temp_path):

    st = State()
    style = qdarkstyle.load_stylesheet_pyqt5()
    main_window = MainWindow(st, style)
    # icon_dir = (Path(__file__).parents[0]).resolve() / "icons/main_icon.png"
    main_window.show()
    qtbot.wait(300)
    # for i in [1, 2, 3, 1, 0]:
    main_window.wid_status.setCurrentIndex(3)

    st.save_settings.save_dir = str(temp_path)
    main_window.wid_save_options.set_locationbutton()
    st.send_scansave_settings()
    # Wait to send and receive parameters:
    qtbot.wait(10000)
    qtbot.mouseClick(main_window.toolbar.experiment_toggle_btn, Qt.LeftButton, delay=1)
    # wait end of the experiment:
    qtbot.wait(TriggerSettings().experiment_duration + 5000)

    # try opening the result:
    SplitDataset(temp_path / "original")

    main_window.closeEvent(MockEvt())
    qtbot.wait(1000)
