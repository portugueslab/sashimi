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


class ImpulseWaveform(Waveform):
    def __init__(self, *args, low=0, high=1, pulse_times, period, **kwargs):
        super().__init__(*args, **kwargs)
        self.low = low
        self.high = high
        self.pulse_times = pulse_times
        self.period = period

    def values(self, t):
        return make_impulses(t, self.low, self.high, self.pulse_times, self.period)


@jit(nopython=True, cache=True)
def make_impulses(t, low, high, pulse_times, period):
    """ Make the camera trigger timing. Posibillity of unequal timing, to
    skip blurry/unequally spaced frames

    :param t:
    :param low:
    :param high:
    :param pulse_times:
    :param period:
    :return:
    """

    result = np.full_like(t, low)
    if len(pulse_times) == 0:
        return result

    dt = t[1] - t[0]
    n_repeats = int(np.ceil((t[-1] - t[0]) / period))
    for pulse in pulse_times:
        for i_repeat in range(n_repeats):
            idx_set = int(np.round((i_repeat * period + pulse - t[0]) / dt))
            if 0 <= idx_set < len(t):
                result[idx_set] = high

    return result
