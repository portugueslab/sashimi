import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from queue import Empty
import numpy as np


class WaveformWidget(QWidget):
    def __init__(self, waveform_queue, pulses_queue, timer):
        super().__init__()
        self.waveform_queue = waveform_queue
        self.pulses_queue = pulses_queue
        self.plot_widget = pg.PlotWidget()
        self.plot_curve = pg.PlotCurveItem()
        self.plot_bars = pg.BarGraphItem()
        self.plot_widget.addItem(self.plot_curve)
        self.plot_widget.addItem(self.plot_bars)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.plot_widget)
        timer.timeout.connect(self.update)

    def update(self):
        try:
            current_waveform = self.waveform_queue.get(timeout=0.001)
            current_pulses = self.pulses_queue.get(timeout=0.001)
            current_pulses = np.nonzero(current_pulses)
            self.plot_curve.setData(np.arange(len(current_waveform)), current_waveform)
            self.plot_bars.setData(x=current_pulses, height=1, width=1, brush='b')
        except Empty:
            pass
