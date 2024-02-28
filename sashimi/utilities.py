from math import gcd
from queue import Empty
from dataclasses import asdict, is_dataclass
from enum import Enum

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
            params = parameter_queue.get(timeout=timeout, block=False)
        except Empty:
            break
    return params


def clean_json(d):
    if isinstance(d, dict):
        cleaned = dict()
        for key, value in d.items():
            cleaned[key] = clean_json(value)
        return cleaned
    elif isinstance(d, Enum):
        return d.name
    elif is_dataclass(d):
        return clean_json(asdict(d))
    elif type(d) in [tuple, list]:
        # json seems to have issues serializing np.int32:
        if type(d[0]) is np.int32:
            d = [int(i) for i in d]
        return d
    else:
        return d


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
        self.np_array = np.ascontiguousarray(np.empty(size // 2, dtype=np.uint16))
        self.size = size

    def __getitem__(self, slice):
        return self.np_array[slice]

    def copy_data(self, address):
        """
        Uses the C memmove function to copy data from an address in memory
        into RAM allocated for the numpy array of this object.
        """
        ctypes.memmove(self.np_array.ctypes.data, address, self.size)

    def get_data(self):
        return self.np_array

    def get_data_pr(self):
        return self.np_array.ctypes.data
