from enum import Enum


class LaserState(Enum):
    ON = 1
    OFF = 2


class LaserException(Exception):
    pass


class LaserWarning(Warning):
    pass


class AbstractLaser:
    def __init__(self, port):
        self.port = port
        self._status = LaserState.OFF

    def start(self):
        pass

    def set_power(self, current):
        """Sets power of laser based on either output power, applied current or power on sample"""
        pass

    def close(self):
        pass

    @property
    def current(self):
        return None

    @current.setter
    def current(self, exp_val):
        pass

    @property
    def output_power(self):
        return None

    @output_power.setter
    def output_power(self, exp_val):
        pass

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, exp_val):
        pass
