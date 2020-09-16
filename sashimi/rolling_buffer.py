import numpy as np
from numba import jit


@jit(nopython=True)
def read_circular(a, i_start, n):
    output = np.zeros(n)
    n_el = len(a)
    i_read = i_start % len(a)
    for i_insert in range(n):
        output[i_insert] = a[i_read]
        i_read = (i_read + 1) % n_el
    return output


@jit(nopython=True)
def write_circular(a, i_start, data):
    # TODO remove redundant writing
    i_insert = i_start % len(a)
    n_el = len(a)
    for i_read in range(len(data)):
        a[i_insert] = data[i_read]
        i_insert = (i_insert + 1) % n_el


@jit(nopython=True)
def fill_circular(a, i_start, n_fill, val):
    # TODO remove redundant writing
    i_insert = i_start
    n_el = len(a)
    for i_read in range(n_fill):
        a[i_insert] = val
        i_insert = (i_insert + 1) % n_el


class RollingBuffer:
    def __init__(self, length):
        self.buffer = np.zeros(length)

    def read(self, start, n_samples_total):
        """Function to read from circular numpy buffer

        :param arr:
        :param start:
        :param n_samples:
        :return:
        """
        return read_circular(self.buffer, start, n_samples_total)

    def write(self, to_write, start):
        """Function to write to circular numpy buffer

        :param arr:
        :param to_write: array to fill the buffer
        :param start:
        :param n_samples:
        :return:
        """
        write_circular(self.buffer, start, to_write)


class FillingRollingBuffer(RollingBuffer):
    def __init__(self, length):
        super().__init__(length)
        self.filled = np.zeros(length, dtype=np.bool)

    def write(self, to_write, start):
        super().write(to_write, start)
        fill_circular(self.filled, start, len(to_write), True)

    def is_complete(self):
        return np.all(self.filled)
