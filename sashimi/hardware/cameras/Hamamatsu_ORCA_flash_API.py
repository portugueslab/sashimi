import ctypes
import numpy as np
from sashimi.utilities import SpeedyArrayBuffer
from sashimi.hardware.cameras import BasicCamera
from sashimi.hardware.cameras.Hamamatsu_ORCA_flash_SDK import *


class HamamatsuOrcaFlashCamera(BasicCamera):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dcam = ctypes.windll.dcamapi
        paraminit = DCAMAPI_INIT(0, 0, 0, 0, None, None)
        paraminit.size = ctypes.sizeof(paraminit)
        error_code = self.dcam.dcamapi_init(ctypes.byref(paraminit))
        n_cameras = paraminit.iDeviceCount

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

        # Open the camera.
        paramopen = DCAMDEV_OPEN(0, self.camera_id, None)
        paramopen.size = ctypes.sizeof(paramopen)
        self.check_status(dcam.dcamdev_open(ctypes.byref(paramopen)), "dcamdev_open")
        self.camera_handle = ctypes.c_void_p(paramopen.hdcam)

        # Set up wait handle
        paramwait = DCAMWAIT_OPEN(0, 0, None, self.camera_handle)
        paramwait.size = ctypes.sizeof(paramwait)
        self.check_status(dcam.dcamwait_open(ctypes.byref(paramwait)), "dcamwait_open")
        self.wait_handle = ctypes.c_void_p(paramwait.hwait)

        # Get camera properties.
        self.properties = self.getCameraProperties()

        # Get camera max width, height.

        self.max_width = self.getPropertyValue("image_width")[0]
        self.max_height = self.getPropertyValue("image_height")[0]

        self.set_subarray_mode()

    @staticmethod
    def check_status(fn_return, fn_name="unknown"):
        if fn_return == DCAMERR_ERROR:
            c_buf_len = 80
            c_buf = ctypes.create_string_buffer(c_buf_len)
            raise Exception("dcam error " + str(fn_name) + " " + str(c_buf.value))
        return fn_return

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

        if mode == ("fixed_length" or "run_till_abort"):
            self.acquisition_mode = mode
            self.number_frames = number_frames
        else:
            raise Exception("Unrecognized acquisition mode: " + mode)

    def set_subarray_mode(self):
        """
        This sets the sub-array mode as appropriate based on the current ROI.
        """

        # Check ROI properties.
        roi_w = self.get_property_value("subarray_hsize")[0]
        roi_h = self.get_property_value("subarray_vsize")[0]

        # If the ROI is smaller than the entire frame tu
        # rn on subarray mode
        if (roi_w == self.max_width) and (roi_h == self.max_height):
            self.set_property_value("subarray_mode", "OFF")
        else:
            self.set_property_value("subarray_mode", "ON")

    def get_frames(self):
        super().get_frames()
        frames = []
        for n in self.newFrames():
            paramlock = DCAMBUF_FRAME(0, 0, 0, n, None, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            paramlock.size = ctypes.sizeof(paramlock)

            # Lock the frame in the camera buffer & get address.
            self.check_status(
                self.dcam.dcambuf_lockframe(
                    self.camera_handle, ctypes.byref(paramlock)
                ),
                "dcambuf_lockframe",
            )

            # Create storage for the frame & copy into this storage.
            hc_data = HCamData(self.frame_bytes)
            hc_data.copyData(paramlock.buf)

            frames.append(hc_data)

        return [frames, [self.frame_x, self.frame_y]]

    def get_property_value(self, *args, **kwargs):
        super().get_property_value(*args, **kwargs)

    def set_property_value(self, *args, **kwargs):
        super().set_property_value(*args, **kwargs)

    def start_acquisition(self):
        super().start_acquisition()

    def stop_acquistion(self):
        super().stop_acquistion()

    def shutdown(self):
        super().shutdown()
