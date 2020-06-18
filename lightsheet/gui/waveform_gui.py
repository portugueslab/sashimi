import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from queue import Empty
import numpy as np


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
        self.state.volume_setting.n_planes.changed.connect(self.update_pulses)
        self.state.volume_setting.frequency.changed.connect(self.update_pulses)
        self.state.camera_settings.exposure.changed.connect(self.update_pulses)

    def update_pulses(self):
        pulse_times = np.arange(
            self.state.volume_setting.n_skip_start,
            self.state.volume_setting.n_planes - self.state.volume_setting.n_skip_end
        ) / (self.state.volume_setting.frequency * self.state.volume_setting.n_planes)

        for region in range(len(self.pulse_regions)):
            self.plot_widget.removeItem(self.pulse_regions[region])
        self.pulse_regions = [None] * len(pulse_times)
        for pulse in pulse_times:
            self.pulse_regions[pulse_times] = pg.LinearRegionItem(
                values=(pulse, pulse + self.state.camera_settings.exposure)
            )
            self.plot_widget.addItem(self.pulse_regions[pulse_times])

    def update(self):
        try:
            current_waveform = self.waveform_queue.get(timeout=0.001)
            n_samples = self.sample_rate / self.state.volume_setting.frequency
            self.plot_curve.setData(np.arange(len(current_waveform)) / n_samples, current_waveform)
        except Empty:
            pass
