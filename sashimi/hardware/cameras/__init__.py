from sashimi.config import read_config
import time
import numpy as np
from skimage.measure import block_reduce

conf = read_config()


class AbstractCamera:
    def __init__(self):
        super().__init__()
        self.camera_id = conf["camera"]["id"]
        self._sensor_resolution = conf["camera"]["sensor_resolution"]

    def apply_parameters(self, parameters):
        """
        Selects which parameters are sent to the camera. This is accomplished
        through self.set_property_value(foo, foo)
        """
        pass

    def get_camera_properties(self):
        """
        Return the ids & names of all the properties that the camera supports. This
        is used at initialization to populate the self.properties attribute.
        """
        pass

    def get_frames(self):
        """
        Returns a list of arrays, each of which corresponds to an available frame. If no frames where found returns an
        empty list.
        """
        pass

    def get_internal_parameters(self, parameters):
        """
        Gets those parameters that cannot be calculated otherwise and have to
        be informed directly by the hardware. Returns frame shape and internal frame
        rate from the camera as a tuple: ([frame_shape, internal_frame_rate])
        """
        pass

    def get_property_value(self, property_name):
        """
        Return the current value of a particular property.
        """
        pass

    def set_property_value(self, property_name, property_value):
        """
        Set the value of a particular property.
        """
        pass

    def start_acquisition(self):
        """
        Allocate as many frames as will fit in 2GB of memory and start data acquisition.
        """
        pass

    def stop_acquistion(self):
        """
        Stop data acquisition and release the memory allocated for frames.
        """
        pass

    def shutdown(self):
        """
        Close down the connection to the camera.
        """
        self.stop_acquistion()

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
    def subarray(self):
        return None

    @subarray.setter
    def subarray(self, exp_val: tuple):
        pass

    @property
    def internal_frame_rate(self):
        return None

    @property
    def trigger_mode(self):
        return None

    @trigger_mode.setter
    def trigger_mode(self, exp_val):
        pass

    @property
    def camera_mode(self):
        return None

    @camera_mode.setter
    def camera_mode(self, exp_val):
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


class AbstractCameraConfigurator:
    def __init__(self):
        pass

    def __enter__(self):
        return AbstractCamera()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockCamera(AbstractCamera):
    def __init__(self):
        super().__init__()
        self._exposure_time = 60
        self._sensor_resolution: tuple = (2048, 2048)
        self._frame_shape = self._sensor_resolution
        self._subarray = (0, 0, self._sensor_resolution[0], self._sensor_resolution[1])
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
        self._frame_rate = 1 / exp_val

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
        self._frame_shape = (self._sensor_resolution[0] // exp_val, self._sensor_resolution[1] // exp_val)
        self.prepare_mock_image()

    @property
    def subarray(self):
        return self._subarray

    @subarray.setter
    def subarray(self, exp_val: tuple):
        self._subarray = exp_val
        self.prepare_mock_image()

    def prepare_mock_image(self):
        self.current_mock_image = block_reduce(
            self.full_mock_image[
                self._subarray[0]:self._subarray[2],
                self._subarray[1]:self._subarray[3]
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
            if self.elapsed >= 1 / self._frame_rate:
                multiplier = np.random.randint(1, 5, 1)
                frames.append(self.current_mock_image * multiplier)
                self.previous_frame_time = self.current_time
        else:
            self.previous_frame_time = self.current_time
        return frames
