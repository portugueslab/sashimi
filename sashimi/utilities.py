from math import gcd
from queue import Empty
import ctypes
import numpy as np
from numba import vectorize, uint16


@vectorize([uint16(uint16, uint16)])
def neg_dif(x, y):
    """
    Parameters
    ----------
    x :
    y :
    Returns
    -------
    """
    if y < x:
        return x - y
    else:
        return 0


def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)


# TODO: This goes into ScopeCuisine
def get_last_parameters(parameter_queue, timeout=0.0001):
    params = None
    while True:
        try:
            params = parameter_queue.get(timeout=timeout)
        except Empty:
            break
    return params

# TODO: Consider this for ScopeCuisine
class SpeedyArrayBuffer:
    """
    Buffer for large data arrays based on numpy and using ctypes for speedy copy of data
    """

    def __init__(self, size=None, *args, **kwargs):
        """
        Create a data object of the appropriate size.
        """
        super().__init__(**kwargs)
        self.np_array = np.ascontiguousarray(
            np.empty(int(size / 2), dtype=np.uint16)
        )
        self.size = size

    def __getitem__(self, slice):
        return self.np_array[slice]

    def copyData(self, address):
        """
        Uses the C memmove function to copy data from an address in memory
        into RAM allocated for the numpy array of this object.
        """
        ctypes.memmove(self.np_array.ctypes.data, address, self.size)

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data
