from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
)
from lightparam.gui import ParameterGui
from lightparam.gui.collapsible_widget import CollapsibleWidget
from sashimi.gui.waveform_gui import WaveformWidget


class PlanarScanningWidget(QWidget):
    def __init__(self, scanning_manager):
        super().__init__()
        self.scanning_manager = scanning_manager
        self.setLayout(QVBoxLayout())
        self.wid_planar = ParameterGui(self.scanning_manager.planar_setting)
        self.layout().addWidget(self.wid_planar)


class SinglePlaneScanningWidget(QWidget):
    def __init__(self, scanning_manager):
        super().__init__()
        self.scanning_manager = scanning_manager
        self.setLayout(QVBoxLayout())
        self.wid_singleplane = ParameterGui(self.scanning_manager.single_plane_settings)
        self.layout().addWidget(self.wid_singleplane)


class VolumeScanningWidget(QWidget):
    def __init__(self, state, timer):
        super().__init__()
        self.timer = timer
        self.state = state

        self.setLayout(QVBoxLayout())
        self.wid_volume = ParameterGui(state.scanning_manager.volume_setting)
        self.chk_pause = QCheckBox("Pause after experiment")

        self.wid_wave = WaveformWidget(state=self.state, timer=self.timer)
        self.wid_collapsible_wave = CollapsibleWidget(
            child=self.wid_wave, name="Piezo impulse-response waveform"
        )
        self.wid_collapsible_wave.toggle_collapse()

        self.layout().addWidget(self.wid_volume)
        self.layout().addWidget(self.chk_pause)
        self.layout().addWidget(self.wid_collapsible_wave)

        self.chk_pause.clicked.connect(self.change_pause_status)

        self.chk_pause.click()

    def change_pause_status(self):
        self.state.pause_after = self.chk_pause.isChecked()
