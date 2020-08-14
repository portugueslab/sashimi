from warnings import warn

try:
    # import visa
    import pyvisa as visa

    rm = visa.ResourceManager()
except (ImportError, ValueError):
    warn("PyVisa not installed, no laser control available")


class CoboltLaser:
    def __init__(self, port="COM4"):
        self.port = port
        self.cobolt = rm.open_resource(
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

    def set_current(self, current):
        try:
            if current > 0:
                self.cobolt.query("ci")
                self.cobolt.query("slc {:.1f}".format(current))
            else:
                self.cobolt.query("em")
        except visa.VisaIOError:
            pass

    def get_status(self):
        status_string = "\n".join(
            [
                "laser is {status}".format(
                    status="OFF" if self.cobolt.query("l?") == "\n0" else "ON"
                ),
                "drive current: {} mA".format(self.cobolt.query("i?")),
                "output power: {} W".format(self.cobolt.query("pa?")),
            ]
        )
        return status_string

    def close(self):
        self.cobolt.close()


class MockCoboltLaser:
    def __init__(self, port=None):
        self.port = port

    def set_current(self, current):
        pass

    def get_status(self):
        pass

    def close(self):
        pass
