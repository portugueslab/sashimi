from sashimi.config import read_config
import time
import numpy as np
from skimage.measure import block_reduce
from enum import Enum

conf = read_config()


class CameraException(Exception):
    pass


class CameraWarning(Warning):
    pass


class TriggerMode(Enum):
    FREE = 1
    EXTERNAL_TRIGGER = 2


class AbstractCamera:
    def __init__(self, camera_id, sensor_resolution=None):
        self.camera_id = camera_id
        self._sensor_resolution = sensor_resolution

    def get_frames(self):
        """
        Returns a list of arrays, each of which corresponds to an available frame. If no frames where found returns an
        empty list.
        """
        pass

    def get_property_value(self, property_name):
        """
        Returns the current value of a particular property from internal memory of the hardware.
        """
        pass

    def set_property_value(self, property_name, property_value):
        """
        Configures the value of a particular property in the hardware.
        """
        pass

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

    def shutdown(self):
        """
        Close down the connection to the camera.
        """
        self.stop_acquisition()

    @property
    def exposure_time(self):
        return None

    @exposure_time.setter
    def exposure_time(self, exp_val):
        pass

    @property
    def binning(self):
        return None

    @binning.setter
    def binning(self, exp_val):
        pass

    @property
    def roi(self):
        return None

    @roi.setter
    def roi(self, exp_val: tuple):
        pass

    @property
    def trigger_mode(self):
        return None

    @trigger_mode.setter
    def trigger_mode(self, exp_val):
        pass

    @property
    def frame_rate(self):
        return None

    @property
    def sensor_resolution(self):
        return self._sensor_resolution

    @property
    def frame_shape(self):
        return tuple([None, None])


class MockCamera(AbstractCamera):
    def __init__(self, camera_id=None, sensor_resolution=None):
        super().__init__(camera_id, sensor_resolution)
        self._exposure_time = 60
        self._sensor_resolution: tuple = (2048, 2048)
        self._frame_shape = self._sensor_resolution
        self._roi = (0, 0, self._sensor_resolution[0], self._sensor_resolution[1])
        self._frame_rate = 1 / self._exposure_time
        self._binning = 1
        self.full_mock_image = np.random.randint(0, 65534, size=self._frame_shape, dtype=np.uint16)
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
    def frame_shape(self):
        return self._frame_shape

    @property
    def frame_rate(self):
        return self._frame_rate

    @property
    def binning(self):
        return self._binning

    @binning.setter
    def binning(self, exp_val):
        self._binning = exp_val
        self._frame_shape = (
            self._sensor_resolution[0] // exp_val,
            self._sensor_resolution[1] // exp_val
        )
        self.prepare_mock_image()

    @property
    def roi(self):
        return self._roi

    @roi.setter
    def roi(self, exp_val: tuple):
        self._roi = exp_val
        self.prepare_mock_image()

    def prepare_mock_image(self):
        self.current_mock_image = block_reduce(
            self.full_mock_image[
            self._roi[0]:self._roi[2],
            self._roi[1]:self._roi[3]
            ],
            (self._binning, self._binning),
            func=np.max
        )

    def get_frames(self):
        super().get_frames()
        self.current_time = time.time_ns()
        frames = []
        if self.previous_frame_time is not None:
            time.sleep(0.0001)
            self.elapsed = (self.current_time - self.previous_frame_time) * 1e-9
            if self.elapsed >= self._exposure_time * 1e-3:
                multiplier = np.random.randint(1, 5, 1)
                frames.append(self.current_mock_image * multiplier)
                self.previous_frame_time = self.current_time
        else:
            self.previous_frame_time = self.current_time
        return frames
