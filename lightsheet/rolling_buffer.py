import numpy as np


class RollingBuffer:
    def __init__(self, length):
        self.buffer = np.zeros(length)

    def read(self, start, n_samples):
        """ Function to read from circular numpy buffer

        :param arr:
        :param start:
        :param n_samples:
        :return:
        """
        if start + n_samples > len(self.buffer):
            remainder = start + n_samples - len(self.buffer)
            return np.concatenate(
                [self.buffer[start : start + n_samples], self.buffer[0:remainder]]
            )
        else:
            return self.buffer[start : start + n_samples]

    def write(self, to_write, start, n_samples):
        """ Function to write to circular numpy buffer

        :param arr:
        :param to_write: array to fill the buffer
        :param start:
        :param n_samples:
        :return:
        """
        if n_samples < 0:
            if start + n_samples < 0:
                to_zero = start + n_samples
                self.buffer[:start] = to_write[len(to_write) - start :]
                self.buffer[len(self.buffer) + to_zero :] = to_write[:-to_zero]
            else:
                self.buffer[start + n_samples : start] = to_write

        else:
            if start + n_samples > len(self.buffer):
                n_end_part = len(self.buffer) - start
                remainder = start + n_samples - len(self.buffer)

                self.buffer[start : start + n_end_part] = to_write[:n_end_part]
                self.buffer[0:remainder] = to_write[n_end_part:]
            else:
                self.buffer[start : start + n_samples] = to_write
