import numpy as np
from numba import jit


class Waveform:
    def __init__(self, *args, **kwargs):
        pass

    def values(self, t):
        return np.zeros(len(self.t))


class ConstantWaveform(Waveform):
    def __init__(self, *args, constant_value=0, **kwargs):
        super().__init__()
        self.constant_value = constant_value

    def values(self, t):
        return np.full(len(t), self.constant_value)


class SawtoothWaveform(Waveform):
    def __init__(self, *args, frequency=1, vmin=0, vmax=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.vmin = vmin
        self.vmax = vmax
        self.frequency = frequency

    def values(self, t):
        tf = t * self.frequency
        return (tf - np.floor(tf)) * (self.vmax - self.vmin) + self.vmin


class RecordedWaveform(Waveform):
    def __init__(self, *args, recording, **kwargs):
        super().__init__(*args, **kwargs)
        self.recording = recording
        self.i_sample = 0

    def values(self, t):
        out = self.recording[self.i_sample : self.i_sample + len(t)]
        self.i_sample = (self.i_sample + len(t)) % self.recording.shape[0]
        return out


class TriangleWaveform(Waveform):
    def __init__(self, *args, frequency=1, vmin=0, vmax=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.vmin = vmin
        self.vmax = vmax
        self.frequency = frequency

    def values(self, t):
        tf = t * self.frequency
        return (
            self.vmin
            + (self.vmax - self.vmin) / 2
            + +(self.vmax - self.vmin)
            * (np.abs((tf - np.floor(tf + 1 / 2))) - 0.25)
            * 2
        )


@jit(nopython=True)
def set_impulses(buffer, n_planes, n_skip_start, n_skip_end, high=5):
    buffer[:] = 0
    n_between_planes = int(round(len(buffer) / n_planes))
    for i in range(n_skip_start, n_planes - n_skip_end):
        buffer[i * n_between_planes] = high
