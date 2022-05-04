from sashimi.hardware.cameras.interface import AbstractCamera
import numpy as np
import time
from skimage.measure import block_reduce
from scipy.ndimage.filters import gaussian_filter


class MockCamera(AbstractCamera):
    def __init__(self, camera_id=None, max_sensor_resolution=None):
        super().__init__(camera_id, max_sensor_resolution)
        self._exposure_time = 60
        self._sensor_resolution: tuple = (256, 256)
        self._roi = (0, 0, self._sensor_resolution[0], self._sensor_resolution[1])
        self._frame_rate = 1 / self._exposure_time
        self._binning = 1
        self.full_mock_image = gaussian_filter(
            np.random.randint(0, 65534, size=self._sensor_resolution, dtype=np.uint16),
            5,
        ).astype(np.uint16)
        self.current_mock_image = self.full_mock_image
        self.previous_frame_time = None
        self.current_time = time.time_ns()
        self.elapsed = 0

    @property
    def exposure_time(self):
        return self._exposure_time

    @exposure_time.setter
    def exposure_time(self, exp_val):
        self._exposure_time = exp_val
        self._frame_rate = 1 / (exp_val * 1e-3)

    @property
    def frame_rate(self):
        return self._frame_rate

    @property
    def binning(self):
        return self._binning

    @binning.setter
    def binning(self, exp_val):
        self._binning = exp_val

    @property
    def roi(self):
        """roi attributes as a tuple: (x_min, y_min, x_size, y_size)"""
        return self._roi

    @roi.setter
    def roi(self, exp_val: tuple):
        self._roi = exp_val
        self.prepare_mock_image()

    @property
    def trigger_mode(self):
        return None

    @trigger_mode.setter
    def trigger_mode(self, exp_val):
        pass

    def prepare_mock_image(self):
        self.current_mock_image = block_reduce(
            self.full_mock_image, (self._binning, self._binning), func=np.max
        )
        self.current_mock_image = self.current_mock_image[
            self._roi[0] : (self._roi[0] + self._roi[2]),
            self._roi[1] : (self._roi[1] + self._roi[3]),
        ]

    def get_frames(self):
        super().get_frames()
        self.current_time = time.time_ns()
        frames = []
        if self.previous_frame_time is not None:
            time.sleep(0.0001)
            self.elapsed = (self.current_time - self.previous_frame_time) * 1e-9
            if self.elapsed >= self._exposure_time * 1e-3:
                multiplier = np.random.randint(1, 5, 1)
                frames.append(np.uint16(self.current_mock_image * multiplier))
                self.previous_frame_time = self.current_time
        else:
            self.previous_frame_time = self.current_time
        return frames

    def start_acquisition(self):
        """
        Allocate as many frames as will fit in 2GB of memory and start data acquisition.
        """
        pass

    def stop_acquisition(self):
        """
        Stop data acquisition and release the memory allocated for frames.
        """
        pass
