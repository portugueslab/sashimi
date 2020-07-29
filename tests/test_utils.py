import numpy as np
from sashimi.utilities import neg_dif


def test_noise_subtraction():
    t = np.array([10000, 5, 200], dtype=np.uint16)
    r = np.array([265, 20, 200], dtype=np.uint16)
    output = neg_dif(t, r)
    overflows = np.where(t.astype(np.int32) - r.astype(np.int32) < 0)
    zeros = np.zeros_like(output[overflows])
    assert output[overflows].any() == zeros.any()
