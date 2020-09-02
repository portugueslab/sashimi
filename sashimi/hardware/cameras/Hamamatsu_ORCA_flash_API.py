import ctypes
import numpy as np
from sashimi.hardware.cameras import BasicCamera
from sashimi.hardware.cameras.Hamamatsu_ORCA_flash_SDK import *


class SpeedyArrayBuffer:
    """
    Buffer for large data arrays based on numpy and using ctypes for speedy copy of data
    """

    def __init__(self, size=None, *args, **kwargs):
        """
        Create a data object of the appropriate size.
        """
        super().__init__(**kwargs)
        self.np_array = np.ascontiguousarray(
            np.empty(int(size / 2), dtype=np.uint16)
        )
        self.size = size

    def __getitem__(self, slice):
        return self.np_array[slice]

    def copyData(self, address):
        """
        Uses the C memmove function to copy data from an address in memory
        into RAM allocated for the numpy array of this object.
        """
        ctypes.memmove(self.np_array.ctypes.data, address, self.size)

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data


class HamamatsuOrcaFlashAPI:
    def __init__(self):
        #
        # Initialization
        #
        self.dcam = ctypes.windll.dcamapi

        paraminit = DCAMAPI_INIT(0, 0, 0, 0, None, None)
        paraminit.size = ctypes.sizeof(paraminit)
        error_code = self.dcam.dcamapi_init(ctypes.byref(paraminit))
        n_cameras = paraminit.iDeviceCount


class HamamatsuOrcaFlashCamera(BasicCamera):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dcam_api = HamamatsuOrcaFlashAPI()

        self.buffer_index = 0
        self.debug = False
        self.encoding = "utf-8"
        self.frame_bytes = 0
        self.frame_x = 0
        self.frame_y = 0
        self.last_frame_number = 0
        self.properties = None
        self.max_backlog = 0
        self.number_image_buffers = 0

        self.acquisition_mode = "run_till_abort"
        self.number_frames = 0

        # Get camera model.
        self.camera_model = self.getModelInfo(camera_id)

        # Open the camera.
        paramopen = DCAMDEV_OPEN(0, self.camera_id, None)
        paramopen.size = ctypes.sizeof(paramopen)
        self.checkStatus(dcam.dcamdev_open(ctypes.byref(paramopen)), "dcamdev_open")
        self.camera_handle = ctypes.c_void_p(paramopen.hdcam)

        # Set up wait handle
        paramwait = DCAMWAIT_OPEN(0, 0, None, self.camera_handle)
        paramwait.size = ctypes.sizeof(paramwait)
        self.checkStatus(dcam.dcamwait_open(ctypes.byref(paramwait)), "dcamwait_open")
        self.wait_handle = ctypes.c_void_p(paramwait.hwait)

        # Get camera properties.
        self.properties = self.getCameraProperties()

        # Get camera max width, height.

        self.max_width = self.getPropertyValue("image_width")[0]
        self.max_height = self.getPropertyValue("image_height")[0]

        self.set_acquisition_mode("run_till_abort")
        self.set_subarray_mode()

    @staticmethod
    def convert_property_name(p_name):
        """
        Regularizes a property name to lowercase names with
        the spaces replaced by underscores.
        """
        return p_name.lower().replace(" ", "_")

    def set_acquisition_mode(self, mode, number_frames=None):
        """
        Set the acquisition mode to either run until aborted or to
        stop after acquiring a set number of frames.

        mode should be either "fixed_length" or "run_till_abort"

        if mode is "fixed_length", then property number_frames indicates the number
        of frames to be acquired.
        """

        self.stop_acquistion()

        if (
                self.acquisition_mode == "fixed_length"
                or self.acquisition_mode == "run_till_abort"
        ):
            self.acquisition_mode = mode
            self.number_frames = number_frames
        else:
            raise Exception("Unrecognized acquisition mode: " + mode)

    def set_subarray_mode(self):
        """
        This sets the sub-array mode as appropriate based on the current ROI.
        """

        # Check ROI properties.
        roi_w = self.getPropertyValue("subarray_hsize")[0]
        roi_h = self.getPropertyValue("subarray_vsize")[0]

        # If the ROI is smaller than the entire frame turn on subarray mode
        if (roi_w == self.max_width) and (roi_h == self.max_height):
            self.setPropertyValue("subarray_mode", "OFF")
        else:
            self.setPropertyValue("subarray_mode", "ON")

    def get_frames(self):
        """
        Gets all of the available frames.

        This will block waiting for new frames even if there new frames
        available when it is called.
        """
        super().get_frames()

    def get_property_value(self):
        """
        Return the current value of a particular property.
        """
        super().get_property_value()

    def set_property_value(self):
        """
        Set the value of a particular property.
        """
        super().set_property_value()

    def start_acquisition(self):
        """
        Allocate as many frames as will fit in 2GB of memory and start data acquisition.
        """
        super().start_acquisition()

    def stop_acquistion(self):
        """
        Stop data acquisition and release the memory allocated for frames.
        """
        super().stop_acquistion()

    def shutdown(self):
        """
        Close down the connection to the camera.
        """
        super().shutdown()
