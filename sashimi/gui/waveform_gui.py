import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import numpy as np

color_plane = (166, 196, 240, 100)
color_current_plane = (100, 100, 240, 100)


class WaveformWidget(QWidget):
    """Widget that plots the waveform of the ongoing piezo scanning and the regions
    corresponding to camera exposure in time.

    Parameters
    ----------
    timer
    state
    """

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
    def camera_exposure_s(self):
        """Returns camera exposure in seconds."""
        return self.state.camera_settings.exposure_time / 1000

    def update_pulses(self):
        """When number of planes is changed, update the full plot by drawing new regions."""
        self.pulse_times = self.state.calculate_pulse_times()

        for region in range(len(self.pulse_regions)):
            self.plot_widget.removeItem(self.pulse_regions[region])

        self.pulse_regions = [
            self._create_hspan((pulse, pulse + self.camera_exposure_s), color_plane)
            for pulse in self.pulse_times
        ]

        # The last region is overlaid and marks the current plane:
        current_pulse = self.pulse_times[self.state.current_plane]
        self.pulse_regions.append(
            self._create_hspan(
                (current_pulse, current_pulse + self.camera_exposure_s),
                color_current_plane,
            )
        )
        for r in self.pulse_regions:
            self.plot_widget.addItem(r)

    def update(self):
        """Update the data of the piezo line and the position of the current plane displayed in the viewer."""
        current_waveform = self.state.get_waveform()
        if current_waveform is not None:
            self.plot_curve.setData(
                np.arange(len(current_waveform)) / self.sample_rate,
                current_waveform,
            )

        if len(self.pulse_times) > 0:
            current_pulse = self.pulse_times[self.state.current_plane]
            self.pulse_regions[-1].setRegion(
                (current_pulse, current_pulse + self.camera_exposure_s)
            )

    @staticmethod
    def _create_hspan(lims, color):
        """Utility to create vertical span in pyqtgraph."""
        region = pg.LinearRegionItem(
            values=(lims[0], lims[1]), movable=False, brush=pg.mkBrush(*color)
        )

        for line in region.lines:
            line.hide()

        return region
