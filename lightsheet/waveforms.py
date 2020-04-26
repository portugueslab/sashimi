import numpy as np
from numba import jit

# Waveforms
def make_sawtooth(t, freq, offset, amp, phase):
    tf = t * freq + 0 * phase / (2 * np.pi)
    return (tf - np.floor(tf)) * amp * 2 - amp + offset


def make_triangle(t, freq, offset, amp, phase):
    tf = t * freq + 0 * phase / (2 * np.pi)
    return offset + amp * (np.abs((tf - np.floor(tf + 1 / 2))) - 0.25) * 4


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

    if len(pulse_times) == 0:
        return np.zeros_like(t)
    result = np.zeros_like(t)

    dt = t[1] - t[0]
    n_repeats = int(np.ceil(t[-1] / period))
    for pulse in pulse_times:
        for i_repeat in range(n_repeats):
            idx_set = int(np.round((i_repeat * period + pulse - t[0]) / dt))
            if 0 <= idx_set < len(t):
                result[idx_set] = high

    return result
