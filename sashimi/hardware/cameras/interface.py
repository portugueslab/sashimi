from enum import Enum


class CameraException(Exception):
    pass


class CameraWarning(Warning):
    pass


class TriggerMode(Enum):
    FREE = 1
    EXTERNAL_TRIGGER = 2


class AbstractCamera:
    def __init__(self, camera_id, max_sensor_resolution=None):
        self.camera_id = camera_id
        self.max_sensor_resolution = max_sensor_resolution

    def get_frames(self):
        """
        Returns a list of arrays, each of which corresponds to an available frame. If no frames where found returns an
        empty list.
        """
        pass

    def start_acquisition(self):
        """
        Allocate as many frames as will fit in 2GB of memory and start data acquisition.
        """
        #pass
        print ('started aqisuition')

    def stop_acquisition(self):
        """
        Stop data acquisition and release the memory allocated for frames.
        """
        #pass
        print ("stopped aqisition")

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
        """Max size of the image, **after binning** and **before** ROI cropping
        (setting binning will change it, setting a ROI won't).
        """
        return tuple([r / self.binning for r in self.max_sensor_resolution])
