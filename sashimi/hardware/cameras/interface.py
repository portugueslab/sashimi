class AbstractCameraInterface:
    def __init__(self):
        self.image_height = 2048
        self.image_width = 2048
        self.frame_shape: tuple = (1024, 1024)

    @property
    def exposure_time(self):
        return None

    @exposure_time.setter
    def exposure_time(self, parameters):
        pass

    @property
    def binning(self):
        return None

    @binning.setter
    def binning(self, parameters):
        pass

    @property
    def subarray(self):
        return None

    @subarray.setter
    def subarray(self, parameters):
        pass

    @property
    def internal_frame_rate(self):
        return None

    @property
    def trigger_mode(self):
        return None

    @trigger_mode.setter
    def trigger_mode(self, parameters):
        pass

    @property
    def camera_mode(self):
        return None

    @camera_mode.setter
    def camera_mode(self, parameters):
        pass


class AbstractCameraConfigurator:
    def __init__(self):
        pass

    def __enter__(self):
        return AbstractCameraInterface()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
