import numpy as np
from numba import jit


def cast_unsigned_subtraction(target: np.ndarray, reference: np.ndarray, dtype_target=np.uint16, dtype_cast=np.int32):
    """Both image and reference should have the same dtype. dtype_cast should be a signed integer type with twice the
    number of bytes for the unsigned dtype_target"""
    target = target.astype(dtype=dtype_cast)
    reference = reference.astype(dtype=dtype_cast)
    result = unsafe_subtraction(target, reference)
    result = result.astype(dtype=dtype_target)
    return result


@jit(nopython=True)
def unsafe_subtraction(target: np.ndarray, reference: np.ndarray):
    result = target - reference
    result[result < 0] = 0
    return result
