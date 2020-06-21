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


if __name__ == '__main__':
    t = np.random.randint(low=0, high=500, size=15, dtype=np.uint16)
    r = np.random.randint(low=0, high=500, size=t.shape, dtype=np.uint16)
    output = cast_unsigned_subtraction(t, r)
    np.set_printoptions(linewidth=300)
    for array in (t, r, output):
        print(array, array.dtype, type(array))
