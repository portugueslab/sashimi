# from sashimi.gui.main_gui import MainWindow
# from sashimi.state import State
# import qdarkstyle
#
#
# class MockEvt:
#     def accept(self):
#         pass
#
#
# def test_main(qtbot):
#     st = State()
#     style = qdarkstyle.load_stylesheet_pyqt5()
#     main_window = MainWindow(st, style)
#     # icon_dir = (Path(__file__).parents[0]).resolve() / "icons/main_icon.png"
#     main_window.show()
#     qtbot.wait(1000)
#     # b = main_window.wid_status.findChild("Calibration")
#     for i in [1, 2, 3, 1, 0]:
#         main_window.wid_status.setCurrentIndex(i)
#         # qtbot.mouseClick(b,
#         #                  Qt.LeftButton,
#         #                  delay=1)
#         # exp.end_protocol(save=False)
#         qtbot.wait(1000)
#     main_window.closeEvent(MockEvt())
#     qtbot.wait(1000)
