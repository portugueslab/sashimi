from sashimi.hardware.scanning.__init__ import AbstractScanInterface
from contextlib import contextmanager
import numpy as np
from time import sleep


class MockBoard(AbstractScanInterface):
    def __init__(self, sample_rate, n_samples, conf):
        super().__init__(sample_rate, n_samples, conf)
        self.piezo_array = np.zeros(n_samples)

    @property
    def z_piezo(self):
        len_sampling = len(self.piezo_array)
        return np.ones(len_sampling)

    @z_piezo.setter
    def z_piezo(self, waveform):
        self.piezo_array[:] = waveform

    def read(self):
        sleep(0.05)

    def write(self):
        sleep(0.05)



@contextmanager
def open_mockboard(sample_rate, n_samples, conf) -> MockBoard:
    try:
        yield MockBoard(sample_rate, n_samples, conf)
    finally:
        pass
