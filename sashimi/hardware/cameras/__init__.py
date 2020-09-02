class BasicCamera:
    def __init__(self, camera_id=0):
        self.encoding = "utf-8"
        self.camera_id = camera_id

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
        pass
