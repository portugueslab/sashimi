import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from queue import Empty
import numpy as np

color_plane = (166, 196, 240, 100)
color_current_plane = (100, 100, 240, 100)


class WaveformWidget(QWidget):
    def __init__(self, waveform_queue, timer, state):
        super().__init__()
        self.state = state
        self.sample_rate = self.state.sample_rate
        self.timer = timer
        self.waveform_queue = waveform_queue
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
        pulse_times = np.arange(
            self.state.volume_setting.n_skip_start,
            self.state.volume_setting.n_planes - self.state.volume_setting.n_skip_end
        ) / (self.state.volume_setting.frequency * self.state.volume_setting.n_planes)

        for region in range(len(self.pulse_regions)):
            self.plot_widget.removeItem(self.pulse_regions[region])
        self.pulse_regions = [None] * len(pulse_times)
        for i_pulse, pulse in enumerate(pulse_times):
            if self.state.volume_setting.i_freeze - 1 == i_pulse:
                self.pulse_regions[i_pulse] = pg.LinearRegionItem(
                    values=(pulse, pulse + self.state.camera_settings.exposure / 1000),
                    movable=False,
                    brush=pg.mkBrush(
                        *color_current_plane
                    )
                )
            else:
                self.pulse_regions[i_pulse] = pg.LinearRegionItem(
                    values=(pulse, pulse + self.state.camera_settings.exposure / 1000),
                    movable=False,
                    brush=pg.mkBrush(
                        *color_plane
                    )
                )
            for line in self.pulse_regions[i_pulse].lines:
                line.hide()
            self.plot_widget.addItem(self.pulse_regions[i_pulse])

    def update(self):
        try:
            current_waveform = self.waveform_queue.get(timeout=0.001)
            self.plot_curve.setData(np.arange(len(current_waveform)) / self.sample_rate, current_waveform)
        except Empty:
            pass
