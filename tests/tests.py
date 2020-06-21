from lightsheet.utilities import cast_unsigned_subtraction
import numpy as np


def test_noise_subtraction():
    t = np.random.randint(low=0, high=500, size=150, dtype=np.uint16)
    r = np.random.randint(low=0, high=500, size=t.shape, dtype=np.uint16)
    output = cast_unsigned_subtraction(t, r)
    overflows = np.where(t.astype(np.int32) - r.astype(np.int32) < 0)
    zeros = np.zeros_like(output[overflows])
    assert output[overflows].any() == zeros.any()
