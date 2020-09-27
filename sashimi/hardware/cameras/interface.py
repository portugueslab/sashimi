from enum import Enum


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
