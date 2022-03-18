import abc
from contextlib import contextmanager
from abc import ABC, abstractmethod


class ScanningError(Exception):
    pass


class AbstractScanInterface(ABC):
    def __init__(self, sample_rate, n_samples, conf, *args, **kwargs):
        self.sample_rate = sample_rate
        self.n_samples = n_samples
        self.conf = conf

    def start(self):
        pass

    @property
    def z_piezo(self):
        return None

    @z_piezo.setter
    def z_piezo(self, waveform):
        pass

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

    def write(self):
        pass

    def read(self):
        pass


@contextmanager
def open_abstract_interface(sample_rate, n_samples, conf) -> AbstractScanInterface:
    try:
        yield AbstractScanInterface(sample_rate, n_samples, conf)
    finally:
        pass
