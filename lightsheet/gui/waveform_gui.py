import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from queue import Empty
import numpy as np


class WaveformWidget(QWidget):
    def __init__(self, waveform_queue, pulses_queue, timer, state, sample_rate=40000):
        super().__init__()
        self.sample_rate = sample_rate
        self.state = state
        self.waveform_queue = waveform_queue
        self.pulses_queue = pulses_queue
        self.plot_widget = pg.PlotWidget()
        self.plot_curve = pg.PlotCurveItem()
        self.plot_widget.addItem(self.plot_curve)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.plot_widget)
        timer.timeout.connect(self.update)

    def update(self):
        try:
            current_waveform = self.waveform_queue.get(timeout=0.001)
            current_pulses = self.pulses_queue.get(timeout=0.001)
            pulse_timing = np.nonzero(current_pulses)[0]
            pulse_duration = self.sample_rate / 1000 * self.state.camera_settings.exposure
            self.plot_curve.setData(np.arange(len(current_waveform)), current_waveform)
            for region in range(len(self.linear_region)):
                self.plot_widget.removeItem(self.linear_region[region])
            self.linear_region = [None] * len(pulse_timing)
            for pulse in pulse_timing:
                self.linear_region[pulse_timing] = pg.LinearRegionItem(values=(pulse, pulse + pulse_duration))
                self.plot_widget.addItem(self.linear_region[pulse_timing])
                self.plot_widget.removeItem()
        except Empty:
            pass
