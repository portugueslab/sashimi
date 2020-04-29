import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from queue import Empty
import numpy as np


class WaveformWidget(QWidget):
    def __init__(self, waveform_queue, timer):
        super().__init__()
        self.waveform_queue = waveform_queue
        self.plot_widget = pg.PlotWidget()
        self.plot_curve = pg.PlotCurveItem()
        self.plot_widget.addItem(self.plot_curve)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.plot_widget)
        timer.timeout.connect(self.update)

    def update(self):
        try:
            current_waveform = self.waveform_queue.get(timeout=0.001)
            self.plot_curve.setData(np.arange(len(current_waveform)), current_waveform)
        except Empty:
            pass
