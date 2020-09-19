from sashimi.hardware.lasers import AbstractLaser


class MockLaser(AbstractLaser):
    def __init__(self, port=None):
        super().__init__(port)
        self._current = 0

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, exp_val):
        self._current = exp_val

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, exp_val):
        self._status = exp_val
