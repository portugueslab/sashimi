import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import numpy as np

color_plane = (166, 196, 240, 100)
color_current_plane = (100, 100, 240, 100)


class WaveformWidget(QWidget):
    def __init__(self, timer, state):
        super().__init__()
        self.state = state
        self.sample_rate = self.state.sample_rate
        self.timer = timer
        self.pulse_regions = []

        self.plot_widget = pg.PlotWidget()
        self.plot_curve = pg.PlotCurveItem()
        self.plot_widget.addItem(self.plot_curve)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.plot_widget)

        self.timer.timeout.connect(self.update)
        self.state.volume_setting.sig_param_changed.connect(self.update_pulses)
        self.state.camera_settings.sig_param_changed.connect(self.update_pulses)

    def update_pulses(self):
        pulse_times = self.state.calculate_pulse_times()

        for region in range(len(self.pulse_regions)):
            self.plot_widget.removeItem(self.pulse_regions[region])
        self.pulse_regions = [None] * len(pulse_times)
        for i_pulse, pulse in enumerate(pulse_times):
            current_pulse = (
                -1
            )  # TODO get currently displayed plane from Napari viewer (if in single-plane mode)
            if i_pulse == current_pulse:
                self.pulse_regions[i_pulse] = pg.LinearRegionItem(
                    values=(
                        pulse,
                        pulse + self.state.camera_settings.exposure / 1000,
                    ),
                    movable=False,
                    brush=pg.mkBrush(*color_current_plane),
                )
            else:
                self.pulse_regions[i_pulse] = pg.LinearRegionItem(
                    values=(
                        pulse,
                        pulse + self.state.camera_settings.exposure_time / 1000,
                    ),
                    movable=False,
                    brush=pg.mkBrush(*color_plane),
                )
            for line in self.pulse_regions[i_pulse].lines:
                line.hide()
            self.plot_widget.addItem(self.pulse_regions[i_pulse])

    def update(self):
        current_waveform = self.state.get_waveform()
        if current_waveform is not None:
            self.plot_curve.setData(
                np.arange(len(current_waveform)) / self.sample_rate,
                current_waveform,
            )
