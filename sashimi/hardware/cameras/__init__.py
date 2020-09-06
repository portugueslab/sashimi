from sashimi.config import read_config
import time
import numpy as np

conf = read_config()


class BasicCamera:
    def __init__(self):
        self.encoding = "utf-8"
        self.camera_id = conf["camera"]["id"]

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
        Gets all of the available frames.

        This will block waiting for new frames even if there new frames
        available when it is called.
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


class MockCamera(BasicCamera):
    def __init__(self):
        super().__init__()
        self.frame_shape: tuple = (1024, 1024)
        self.exposure_time = 60

    def apply_parameters(self, parameters, *args, **kwargs):
        super().apply_parameters(*args, **kwargs)
        subarray = parameters.subarray
        # quantizing the ROI dims in multiples of 4
        subarray = [min((i * parameters.binning // 4) * 4, 2048) for i in subarray]
        self.frame_shape = (subarray[2], subarray[3])
        self.exposure_time = parameters.exposure_time

    def get_frames(self):
        super().get_frames()
        time.sleep(0.001)
        frames = []
        is_there_frame = np.random.random_sample(1)
        if is_there_frame < (1 / self.exposure_time):
            frame = np.random.randint(
                0, 65534, size=self.frame_shape, dtype=np.uint16
            )
            frames.append(frame)
        return frames

    def get_internal_parameters(self, parameters, *args, **kwargs):
        super().get_internal_parameters(*args, **kwargs)
        frame_shape = parameters.subarray // parameters.binning
        internal_frame_rate = 1 / parameters.exposure_time
        return tuple([frame_shape, internal_frame_rate])
