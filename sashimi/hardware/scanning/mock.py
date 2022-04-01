from sashimi.hardware.scanning.__init__ import AbstractScanInterface
from contextlib import contextmanager
import numpy as np
from time import sleep


class MockBoard(AbstractScanInterface):
    def __init__(self, sample_rate, n_samples, conf):
        super().__init__(sample_rate, n_samples, conf)
        self.piezo_array = np.zeros(n_samples)

    def start(self):
        pass

    def read(self):
        sleep(0.05)

    def write(self):
        sleep(0.05)
        
        
    @property
    def z_piezo(self):
        len_sampling = len(self.piezo_array)
        return np.ones(len_sampling)

    @z_piezo.setter
    def z_piezo(self, waveform):
        self.piezo_array[:] = waveform

    @property
    def z_frontal(self):
        return None

    @z_frontal.setter
    def z_frontal(self, waveform):
        pass

    @property
    def z_lateral(self):
        return None

    @z_lateral.setter
    def z_lateral(self, waveform):
        pass

    @property
    def camera_trigger(self):
        return None

    @camera_trigger.setter
    def camera_trigger(self, waveform):
        pass

    @property
    def xy_frontal(self):
        return None

    @xy_frontal.setter
    def xy_frontal(self, waveform):
        pass

    @property
    def xy_lateral(self):
        return None

    @xy_lateral.setter
    def xy_lateral(self, waveform):
        pass


@contextmanager
def open_mockboard(sample_rate, n_samples, conf) -> MockBoard:
    try:
        yield MockBoard(sample_rate, n_samples, conf)
    finally:
        pass
