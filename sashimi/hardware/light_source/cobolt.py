from warnings import warn
from sashimi.hardware.light_source.interface import AbstractLightSource, LaserWarning
from sashimi.config import read_config

try:
    import pyvisa as visa

    manager = visa.ResourceManager()
except (ImportError, ValueError):
    manager = None


conf = read_config()


class CoboltLaser(AbstractLightSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if manager is None:
            raise ImportError("PyVisa not installed, no laser control available")

        self.socket = manager.open_resource(
            self.port,
            **{
                "write_termination": "\r",
                "read_termination": "\r",
                "baud_rate": 115200,
                "parity": visa.constants.Parity.none,
                "stop_bits": visa.constants.StopBits.one,
                "encoding": "ascii",
            },
        )
        self._current = 0
        self.intensity_units = conf["light_source"]["intensity_units"]

    def set_current(self):
        try:
            if self._current > 0:
                self.socket.query("ci")
                self.socket.query("slc {:.1f}".format(self._current))
            else:
                self.socket.query("em")
        except visa.VisaIOError:
            warn("Current not set. Laser was unreachable", LaserWarning)

    def get_info(self):
        status_string = "\n".join(
            [
                "laser is {status}".format(
                    status="OFF" if self.socket.query("l?") == "\n0" else "ON"
                ),
                "drive current: {} mA".format(self.socket.query("i?")),
                "output power: {} W".format(self.socket.query("pa?")),
            ]
        )
        return status_string

    def close(self):
        self.socket.close()

    @property
    def intensity(self):
        return self._current

    @intensity.setter
    def intensity(self, exp_val):
        self._current = exp_val
        self.set_current()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, exp_val):
        self._status = exp_val
