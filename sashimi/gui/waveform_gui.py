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
        self.highlighted_plane = 0

        self.pulse_regions = []
        self.pulse_times = []

        self.plot_widget = pg.PlotWidget()
        self.plot_curve = pg.PlotCurveItem()
        self.plot_widget.addItem(self.plot_curve)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.plot_widget)

        self.timer.timeout.connect(self.update)
        self.state.volume_setting.sig_param_changed.connect(self.update_pulses)
        self.state.camera_settings.sig_param_changed.connect(self.update_pulses)

    @property
    def camera_exposure(self):
        return self.state.camera_settings.exposure_time / 1000

    def update_pulses(self):
        self.pulse_times = self.state.calculate_pulse_times()

        for region in range(len(self.pulse_regions)):
            self.plot_widget.removeItem(self.pulse_regions[region])

        self.pulse_regions = [self.create_hspan((pulse, pulse + self.camera_exposure), color_plane)
                              for pulse in self.pulse_times]

        # The last region is overlaid and marks the current plane:
        current_pulse = self.pulse_times[self.state.current_plane]
        self.pulse_regions.append(self.create_hspan((current_pulse, current_pulse + self.camera_exposure),
                                                    color_current_plane))
        for r in self.pulse_regions:
            self.plot_widget.addItem(r)

    def update(self):
        current_waveform = self.state.get_waveform()
        if current_waveform is not None:
            self.plot_curve.setData(
                np.arange(len(current_waveform)) / self.sample_rate,
                current_waveform,
            )

        if len(self.pulse_times) > 0:
            current_pulse = self.pulse_times[self.state.current_plane]
            self.pulse_regions[-1].setRegion((current_pulse, current_pulse + self.camera_exposure))

    @staticmethod
    def create_hspan(lims, color):
        region = pg.LinearRegionItem(values=(lims[0], lims[1]), movable=False, brush=pg.mkBrush(*color))

        for line in region.lines:
            line.hide()

        return region
