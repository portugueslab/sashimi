from enum import Enum


class LaserState(Enum):
    ON = 1
    OFF = 2


class LaserException(Exception):
    pass


class LaserWarning(Warning):
    pass


class AbstractLightSource:
    def __init__(self, port):
        self.port = port
        self._status = LaserState.OFF

    def start(self):
        pass

    def set_power(self, current):
        """Sets power of laser based on self.intensity and self.intensity_units"""
        pass

    def close(self):
        pass

    @property
    def intensity(self):
        return None

    @intensity.setter
    def intensity(self, exp_val):
        pass

    @property
    def intensity_units(self):
        return None

    @intensity_units.setter
    def intensity_units(self, exp_val):
        pass

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, exp_val):
        pass
