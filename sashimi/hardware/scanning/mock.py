from sashimi.hardware.scanning.interface import AbstractScanInterface
from contextlib import contextmanager


class MockBoard(AbstractScanInterface):
    pass


@contextmanager
def open_mockboard(sample_rate, n_samples, conf) -> MockBoard:
    try:
        yield MockBoard(sample_rate, n_samples, conf)
    finally:
        pass
