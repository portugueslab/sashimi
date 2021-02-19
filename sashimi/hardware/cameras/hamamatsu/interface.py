import numpy as np
from warnings import warn
import ctypes

from sashimi.utilities import SpeedyArrayBuffer
from sashimi.hardware.cameras.interface import (
    AbstractCamera,
    TriggerMode,
    CameraException,
    CameraWarning,
)
from sashimi.hardware.cameras.hamamatsu.sdk import (
    DCAMAPI_INIT,
    DCAMDEV_OPEN,
    DCAMWAIT_OPEN,
    DCAMCAP_TRANSFERKIND_FRAME,
    DCAMBUF_ATTACHKIND_FRAME,
    DCAMCAP_START_SEQUENCE,
    DCAMWAIT_CAPEVENT_FRAMEREADY,
    DCAMPROP_OPTION_NEXT,
    DCAMPROP_TYPE_MODE,
    DCAMPROP_TYPE_REAL,
    DCAMPROP_TYPE_LONG,
    DCAMPROP_OPTION_NEAREST,
    DCAMERR_ERROR,
    DCAMCAP_STATUS_BUSY,
    DCAMERR_NOERROR,
    DCAMPROP_ATTR_HASVALUETEXT,
    DCAMPROP_ATTR,
    DCAMPROP_TYPE_MASK,
    DCAMBUF_ATTACH,
    DCAM_DEFAULT_ARG,
    DCAMWAIT_START,
    DCAMWAIT_CAPEVENT_STOPPED,
    DCAMCAP_TRANSFERINFO,
    DCAMPROP_VALUETEXT,
)

from sashimi.config import read_config

conf = read_config()


class HamamatsuCamera(AbstractCamera):
    def __init__(self, camera_id, max_sensor_resolution):
        super().__init__(camera_id, max_sensor_resolution)

        # This need to be specified at the beginning, not to change with the ROI that we set.
        self.dcam = ctypes.windll.dcamapi
        paraminit = DCAMAPI_INIT(0, 0, 0, 0, None, None)
        paraminit.size = ctypes.sizeof(paraminit)
        self.error_code = self.dcam.dcamapi_init(ctypes.byref(paraminit))

        # Open the camera.
        paramopen = DCAMDEV_OPEN(0, self.camera_id, None)
        paramopen.size = ctypes.sizeof(paramopen)
        self.check_status(
            self.dcam.dcamdev_open(ctypes.byref(paramopen)), "dcamdev_open"
        )
        self.camera_handle = ctypes.c_void_p(paramopen.hdcam)

        # Set up wait handle
        paramwait = DCAMWAIT_OPEN(0, 0, None, self.camera_handle)
        paramwait.size = ctypes.sizeof(paramwait)
        self.check_status(
            self.dcam.dcamwait_open(ctypes.byref(paramwait)), "dcamwait_open"
        )
        self.wait_handle = ctypes.c_void_p(paramwait.hwait)

        self.properties = self.get_camera_properties()
        self.exposure_time = conf["camera"]["default_exposure"]

        self._roi = (0, 0) + self.max_sensor_resolution
        self._trigger_mode = TriggerMode.EXTERNAL_TRIGGER
        self._frame_bytes = 0

        self.buffer_index = 0
        self.last_frame_number = 0
        self.max_backlog = 0
        self.number_image_buffers = 0
        self.hcam_data = []
        self.hcam_ptr = False
        self.old_frame_bytes = -1

        self.number_frames = 0

    @property
    def binning(self):
        return self.get_property_value("binning")

    @binning.setter
    def binning(self, n_bin):
        self.set_property_value("binning", f"{n_bin}x{n_bin}")

    @property
    def exposure_time(self):
        return self.get_property_value("exposure_time") * 1000

    @exposure_time.setter
    def exposure_time(self, exp_val):
        self.set_property_value("exposure_time", 0.001 * exp_val)

    @property
    def frame_rate(self):
        return 1 / self.exposure_time

    @property
    def roi(self):
        return self._roi

    @roi.setter
    def roi(self, exp_val: tuple):
        """The ROI is set in "maximum resolution of the sensor units". Therefore, it should not change
        with the binning.
        """
        self._roi = [(i * self.binning // 4) * 4 for i in exp_val]
        self.set_property_value("subarray_vpos", self._roi[0])
        self.set_property_value("subarray_hpos", self._roi[1])
        self.set_property_value("subarray_vsize", self._roi[2])
        self.set_property_value("subarray_hsize", self._roi[3])

    @property
    def trigger_mode(self):
        return self._trigger_mode

    @trigger_mode.setter
    def trigger_mode(self, exp_val: TriggerMode):
        self._trigger_mode = exp_val
        self.set_property_value("trigger_source", exp_val.value)

    @property
    def frame_bytes(self):
        return self._frame_bytes

    @property
    def frame_shape(self):
        # TODO these get_property value can get cleaned up in another property
        return tuple(
            self.get_property_value(v) for v in ["image_height", "image_width"]
        )

    def get_frames(self):
        frames = []

        # Return a list of the ids of all the new frames since the last check.
        # Returns an empty list if the camera has already stopped and no frames
        # are available. This will block waiting for at least one new frame.

        capture_status = ctypes.c_int32(0)
        self.check_status(
            self.dcam.dcamcap_status(self.camera_handle, ctypes.byref(capture_status))
        )

        # Wait for a new frame if the camera is acquiring.
        if capture_status.value == DCAMCAP_STATUS_BUSY:
            param_start = DCAMWAIT_START(
                0,
                0,
                DCAMWAIT_CAPEVENT_FRAMEREADY | DCAMWAIT_CAPEVENT_STOPPED,
                100,
            )
            param_start.size = ctypes.sizeof(param_start)
            self.check_status(
                self.dcam.dcamwait_start(self.wait_handle, ctypes.byref(param_start)),
                "dcamwait_start",
            )

        # Check how many new frames there are.
        paramtransfer = DCAMCAP_TRANSFERINFO(0, DCAMCAP_TRANSFERKIND_FRAME, 0, 0)
        paramtransfer.size = ctypes.sizeof(paramtransfer)
        self.check_status(
            self.dcam.dcamcap_transferinfo(
                self.camera_handle, ctypes.byref(paramtransfer)
            ),
            "dcamcap_transferinfo",
        )
        cur_buffer_index = paramtransfer.nNewestFrameIndex
        cur_frame_number = paramtransfer.nFrameCount

        # Check that we have not acquired more frames than we can store in our buffer.
        # Keep track of the maximum backlog.
        backlog = cur_frame_number - self.last_frame_number
        if backlog > self.number_image_buffers:
            warn(
                "Camera buffer overrun detected. Some frames might have been lost",
                CameraWarning,
            )
        if backlog > self.max_backlog:
            self.max_backlog = backlog
        self.last_frame_number = cur_frame_number

        # Create a list of the new frames.
        new_frames = []
        if cur_buffer_index < self.buffer_index:
            for i in range(self.buffer_index + 1, self.number_image_buffers):
                new_frames.append(i)
            for i in range(cur_buffer_index + 1):
                new_frames.append(i)
        else:
            for i in range(self.buffer_index, cur_buffer_index):
                new_frames.append(i + 1)
        self.buffer_index = cur_buffer_index

        for i_frame in new_frames:
            frame_data = self.hcam_data[i_frame].get_data()
            frames.append(np.reshape(frame_data, self.frame_shape).copy())

        return frames

    def get_property_value(self, property_name):
        # Check if the property exists.
        if not (property_name in self.properties):
            raise CameraException(f"Unknown property name{property_name}")
        prop_id = self.properties[property_name]

        # Get the property value.
        c_value = ctypes.c_double(0)
        self.check_status(
            self.dcam.dcamprop_getvalue(
                self.camera_handle,
                ctypes.c_int32(prop_id),
                ctypes.byref(c_value),
            ),
            "dcamprop_getvalue",
        )

        prop_attr = self.get_property_attribute(property_name)

        # Convert type based on attribute type.
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if temp == DCAMPROP_TYPE_MODE:
            prop_value = int(c_value.value)
        elif temp == DCAMPROP_TYPE_LONG:
            prop_value = int(c_value.value)
        elif temp == DCAMPROP_TYPE_REAL:
            prop_value = c_value.value
        else:
            prop_value = False

        return prop_value

    def set_property_value(self, property_name, property_value, *args, **kwargs):
        # Check if the property exists.
        if not (property_name in self.properties):

            raise CameraException(f"Unknown property name {property_name}")

        # If the value is text, figure out what the
        # corresponding numerical property value is.
        if isinstance(property_value, str):
            text_values = self.get_property_text(property_name)
            if property_value in text_values:
                property_value = float(text_values[property_value])
            else:
                raise CameraException(
                    f"Invalid property value {property_value} for {property_name}"
                )

        # Check that the property is within range.
        [pv_min, pv_max] = self.get_property_range(property_name)
        if property_value < pv_min:
            warn(
                f"Value {property_value} for {property_name} is less than minimum {pv_min}. Setting to minimum.",
                CameraWarning,
            )
            property_value = pv_min
        if property_value > pv_max:
            warn(
                f"Value {property_value} for {property_name} is greater than maximum {pv_max}. Setting to maximum.",
                CameraWarning,
            )
            property_value = pv_max

        # Set the property value, return what it was set too.
        prop_id = self.properties[property_name]
        p_value = ctypes.c_double(property_value)
        self.check_status(
            self.dcam.dcamprop_setgetvalue(
                self.camera_handle,
                ctypes.c_int32(prop_id),
                ctypes.byref(p_value),
                ctypes.c_int32(DCAM_DEFAULT_ARG),
            ),
            "dcamprop_setgetvalue",
        )
        return p_value.value

    def start_acquisition(self):
        self.buffer_index = -1
        self.last_frame_number = 0

        """
        This sets the sub-array mode as appropriate based on the current ROI.
        """

        # Check ROI properties.
        roi_w = self.get_property_value("subarray_hsize")
        roi_h = self.get_property_value("subarray_vsize")

        # If the ROI is smaller than the entire frame turn on subarray mode:
        if (roi_h == self.max_sensor_resolution[0]) and (
            roi_w == self.max_sensor_resolution[1]
        ):
            self.set_property_value("subarray_mode", "OFF")
        else:
            self.set_property_value("subarray_mode", "ON")

        # Get size of frame
        self._frame_bytes = self.get_property_value("image_framebytes")

        if self.old_frame_bytes != self._frame_bytes:
            # The larger of either 2000 frames or some weird calculation for number of buffers for 2 seconds of data
            self.number_image_buffers = min(
                int((2.0 * 1024 * 1024 * 1024) / self._frame_bytes), 2000
            )
            # Allocate new image buffers.
            ptr_array = ctypes.c_void_p * self.number_image_buffers
            self.hcam_ptr = ptr_array()
            self.hcam_data = []
            for i in range(self.number_image_buffers):
                hc_data = SpeedyArrayBuffer(self._frame_bytes)
                self.hcam_ptr[i] = hc_data.get_data_pr()
                self.hcam_data.append(hc_data)

            self.old_frame_bytes = self._frame_bytes

        # Attach image buffers and start acquisition.
        # We need to attach & release for each acquisition otherwise
        # we will get an error if we try to change the ROI in any way
        # between acquisitions.

        paramattach = DCAMBUF_ATTACH(
            0,
            DCAMBUF_ATTACHKIND_FRAME,
            self.hcam_ptr,
            self.number_image_buffers,
        )
        paramattach.size = ctypes.sizeof(paramattach)
        self.check_status(
            self.dcam.dcambuf_attach(self.camera_handle, paramattach),
            "dcam_attachbuffer",
        )
        self.check_status(
            self.dcam.dcamcap_start(self.camera_handle, DCAMCAP_START_SEQUENCE),
            "dcamcap_start",
        )

    def stop_acquisition(self):
        self.check_status(self.dcam.dcamcap_stop(self.camera_handle), "dcamcap_stop")

        # Free image buffers.
        self.max_backlog = 0
        if self.hcam_ptr:
            self.check_status(
                self.dcam.dcambuf_release(self.camera_handle, DCAMBUF_ATTACHKIND_FRAME),
                "dcambuf_release",
            )

    def shutdown(self):
        super().shutdown()
        self.check_status(self.dcam.dcamwait_close(self.wait_handle), "dcamwait_close")
        self.check_status(self.dcam.dcamdev_close(self.camera_handle), "dcamdev_close")

    def get_property_attribute(self, property_name):
        """
        Return the attribute structure of a particular property.
        """
        p_attr = DCAMPROP_ATTR()
        p_attr.cbSize = ctypes.sizeof(p_attr)
        p_attr.iProp = self.properties[property_name]
        ret = self.check_status(
            self.dcam.dcamprop_getattr(self.camera_handle, ctypes.byref(p_attr)),
            "dcamprop_getattr",
        )
        if ret == 0:
            return False
        else:
            return p_attr

    def get_property_range(self, property_name):
        """
        Return the range for an attribute.
        """
        prop_attr = self.get_property_attribute(property_name)
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if temp == DCAMPROP_TYPE_REAL:
            return [float(prop_attr.valuemin), float(prop_attr.valuemax)]
        else:
            return [int(prop_attr.valuemin), int(prop_attr.valuemax)]

    def get_property_text(self, property_name):
        """
        Return the text options of a property (if any).
        """
        prop_attr = self.get_property_attribute(property_name)
        if not (prop_attr.attribute & DCAMPROP_ATTR_HASVALUETEXT):
            return {}
        else:
            # Create property text structure.
            prop_id = self.properties[property_name]
            v = ctypes.c_double(prop_attr.valuemin)

            prop_text = DCAMPROP_VALUETEXT()
            c_buf_len = 64
            c_buf = ctypes.create_string_buffer(c_buf_len)
            # prop_text.text = ctypes.c_char_p(ctypes.addressof(c_buf))
            prop_text.cbSize = ctypes.c_int32(ctypes.sizeof(prop_text))
            prop_text.iProp = ctypes.c_int32(prop_id)
            prop_text.value = v
            prop_text.text = ctypes.addressof(c_buf)
            prop_text.textbytes = c_buf_len

            # Collect text options.
            done = False
            text_options = {}
            while not done:
                # Get text of current value.
                self.check_status(
                    self.dcam.dcamprop_getvaluetext(
                        self.camera_handle, ctypes.byref(prop_text)
                    ),
                    "dcamprop_getvaluetext",
                )
                text_options[prop_text.text.decode("utf-8")] = int(v.value)

                # Get next value.
                ret = self.dcam.dcamprop_queryvalue(
                    self.camera_handle,
                    ctypes.c_int32(prop_id),
                    ctypes.byref(v),
                    ctypes.c_int32(DCAMPROP_OPTION_NEXT),
                )
                prop_text.value = v

                if ret != 1:
                    done = True

            return text_options

    def check_status(self, fn_return, fn_name="unknown"):
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

    def get_camera_properties(self):
        """
        Return the ids & names of all the properties that the camera supports. This
        is used at initialization to populate the self.properties attribute.
        """
        c_buf_len = 64
        c_buf = ctypes.create_string_buffer(c_buf_len)
        properties = {}
        prop_id = ctypes.c_int32(0)

        # Reset to the start.
        ret = self.dcam.dcamprop_getnextid(
            self.camera_handle,
            ctypes.byref(prop_id),
            ctypes.c_uint32(DCAMPROP_OPTION_NEAREST),
        )
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.check_status(ret, "dcamprop_getnextid")

        # Get the first property.
        ret = self.dcam.dcamprop_getnextid(
            self.camera_handle,
            ctypes.byref(prop_id),
            ctypes.c_int32(DCAMPROP_OPTION_NEXT),
        )
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.check_status(ret, "dcamprop_getnextid")
        self.check_status(
            self.dcam.dcamprop_getname(
                self.camera_handle, prop_id, c_buf, ctypes.c_int32(c_buf_len)
            ),
            "dcamprop_getname",
        )

        # Get the rest of the properties.
        last = -1
        while prop_id.value != last:
            last = prop_id.value
            properties[
                self.convert_property_name(c_buf.value.decode("utf-8"))
            ] = prop_id.value
            ret = self.dcam.dcamprop_getnextid(
                self.camera_handle,
                ctypes.byref(prop_id),
                ctypes.c_int32(DCAMPROP_OPTION_NEXT),
            )
            if (ret != 0) and (ret != DCAMERR_NOERROR):
                self.check_status(ret, "dcamprop_getnextid")
            self.check_status(
                self.dcam.dcamprop_getname(
                    self.camera_handle,
                    prop_id,
                    c_buf,
                    ctypes.c_int32(c_buf_len),
                ),
                "dcamprop_getname",
            )

        if properties == {"": 0}:
            raise ConnectionError("The Hamamatsu camera seems to be off!")

        return properties
