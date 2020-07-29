from math import gcd
from queue import Empty

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


def get_last_parameters(parameter_queue, timeout=0.0001):
    params = None
    while True:
        try:
            params = parameter_queue.get(timeout=timeout)
        except Empty:
            break
    return params
