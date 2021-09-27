import numpy as np


def abs_to_mm(value, inverse):
    """

    Parameters
    ----------
    value: a int or array of positions (either in mm or absolute value)
    inverse: if False performs abs->mm
             if True performs mm->abs

    Returns
    -------
        does not return anything, but modifies the input

    """


    x1m = 1.0013
    x1a = 34350
    alpha = x1m / x1a
    beta = 1 / alpha

    if isinstance(value, int):
        if inverse:
            return int(value * beta)
        else:
            return value * alpha
    else:  # assume is array
        if inverse:
            return (np.array(value) * beta).astype(int)
        else:
            return np.array(value) * alpha

