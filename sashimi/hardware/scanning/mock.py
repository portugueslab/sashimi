from sashimi.hardware.scanning.interface import AbstractScanInterface
from contextlib import contextmanager
import numpy as np


class MockBoard(AbstractScanInterface):
    def __init__(self, sample_rate, n_samples, conf):
        super().__init__(sample_rate, n_samples, conf)
        self.piezo_array = np.zeros(n_samples)

    @property
    def z_piezo(self):
        return self.piezo_array.copy()

    @z_piezo.setter
    def z_piezo(self, waveform):
        self.piezo_array[:] = waveform


@contextmanager
def open_mockboard(sample_rate, n_samples, conf) -> MockBoard:
    try:
        yield MockBoard(sample_rate, n_samples, conf)
    finally:
        pass
