from contextlib import contextmanager
from abc import ABC, abstractmethod


class ScanningError(Exception):
    pass


class AbstractScanInterface(ABC):
    def __init__(self, sample_rate, n_samples, conf, *args, **kwargs):
        self.sample_rate = sample_rate
        self.n_samples = n_samples
        self.conf = conf

    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def write(self):
        pass

    @abstractmethod
    def read(self):
        pass

    @property
    @abstractmethod
    def z_piezo(self):
        return None

    @z_piezo.setter
    @abstractmethod
    def z_piezo(self, waveform):
        pass

    @property
    @abstractmethod
    def z_frontal(self):
        return None

    @z_frontal.setter
    @abstractmethod
    def z_frontal(self, waveform):
        pass

    @property
    @abstractmethod
    def z_lateral(self):
        return None

    @z_lateral.setter
    @abstractmethod
    def z_lateral(self, waveform):
        pass

    @property
    @abstractmethod
    def camera_trigger(self):
        return None

    @camera_trigger.setter
    @abstractmethod
    def camera_trigger(self, waveform):
        pass

    @property
    @abstractmethod
    def xy_frontal(self):
        return None

    @xy_frontal.setter
    @abstractmethod
    def xy_frontal(self, waveform):
        pass

    @property
    @abstractmethod
    def xy_lateral(self):
        return None

    @xy_lateral.setter
    @abstractmethod
    def xy_lateral(self, waveform):
        pass

    


@contextmanager
def open_abstract_interface(sample_rate, n_samples, conf) -> AbstractScanInterface:
    try:
        yield AbstractScanInterface(sample_rate, n_samples, conf)
    finally:
        pass
