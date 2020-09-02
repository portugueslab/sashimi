from sashimi.config import read_config

conf = read_config()


class BasicCamera:
    def __init__(self):
        self.encoding = "utf-8"
        self.camera_id = conf["camera"]["id"]

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
