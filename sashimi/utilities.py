from math import gcd
from queue import Empty
from dataclasses import asdict, is_dataclass
from enum import Enum

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
    else:
        return d
