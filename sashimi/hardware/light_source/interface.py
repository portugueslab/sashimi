from enum import Enum
from abc import ABC, abstractmethod


class LaserState(Enum):
    ON = 1
    OFF = 2


class LaserException(Exception):
    pass


class LaserWarning(Warning):
    pass


class AbstractLightSource(ABC):
    def __init__(self, port):
        self.port = port
        self._status = LaserState.OFF
        self.intensity_units = None

    def start(self):
        pass

    @abstractmethod
    def set_power(self, current):
        """Sets power of laser based on self.intensity and self.intensity_units"""
        pass

    @abstractmethod
    def close(self):
        pass

    @property
    @abstractmethod
    def intensity(self):
        return None

    # @intensity.setter
    # @abstractmethod
    # def intensity(self, exp_val):
    #     pass

    @property
    @abstractmethod
    def status(self):
        return self._status

    @status.setter
    @abstractmethod
    def status(self, exp_val):
        pass
