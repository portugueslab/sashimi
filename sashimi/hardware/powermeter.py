# import instruments as ik
import pyvisa
import time

rm = pyvisa.ResourceManager()


class Powermeter:
    def __init__(self, address="USB0::0x1313::0x80B0::P3002230::INSTR"):
        self.inst = rm.open_resource(address)

    @property
    def wavelength(self):
        return float(self.inst.query("SENS:CORR:WAV?"))

    def measure(self):
        power = float(self.inst.query("MEAS:POW?"))
        if power > 100:  # reading inf
            raise pyvisa.errors.VisaIOError
        return power

    def __repr__(self):
        return self.inst.query("*IDN?")


if __name__ == "__main__":
    rm = pyvisa.ResourceManager()
    res = rm.list_resources()
    print(res)
    inst = rm.open_resource('USB0::0x1313::0x80B0::P3002230::INSTR')
    print(inst.query("*IDN?"))  # inst name
    # inst = ik.thorlabs.PM100USB(res[0])
    # print(dir(inst))

    # inst.write("SENS:CORR:WAV 920")
    t0 = time.time()
    wavelength = float(inst.query("SENS:CORR:WAV?"))
    power = float(inst.query("MEAS:POW?"))
    print("{:.6f} mW at {:.0f}nm".format(power * 1e3, wavelength))
    print(time.time() - t0)
    inst.close()
