from sashimi.utilities import SpeedyArrayBuffer
from sashimi.hardware.cameras import AbstractCamera
from sashimi.hardware.cameras.SDK.hamamatsu_sdk import *


class HamamatsuCamera(AbstractCamera):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.dcam = ctypes.windll.dcamapi
        paraminit = DCAMAPI_INIT(0, 0, 0, 0, None, None)
        paraminit.size = ctypes.sizeof(paraminit)
        error_code = self.dcam.dcamapi_init(ctypes.byref(paraminit))
        n_cameras = paraminit.iDeviceCount

        self.buffer_index = 0
        self.debug = False
        self.frame_bytes = 0
        self.frame_x = 0
        self.frame_y = 0
        self.last_frame_number = 0
        self.properties = None
        self.max_backlog = 0
        self.number_image_buffers = 0
        self.hcam_data = []
        self.hcam_ptr = False
        self.old_frame_bytes = -1

        self.acquisition_mode = "run_till_abort"
        self.number_frames = 0

        # Open the camera.
        paramopen = DCAMDEV_OPEN(0, self.camera_id, None)
        paramopen.size = ctypes.sizeof(paramopen)
        self.check_status(self.dcam.dcamdev_open(ctypes.byref(paramopen)), "dcamdev_open")
        self.camera_handle = ctypes.c_void_p(paramopen.hdcam)

        # Set up wait handle
        paramwait = DCAMWAIT_OPEN(0, 0, None, self.camera_handle)
        paramwait.size = ctypes.sizeof(paramwait)
        self.check_status(self.dcam.dcamwait_open(ctypes.byref(paramwait)), "dcamwait_open")
        self.wait_handle = ctypes.c_void_p(paramwait.hwait)

        # Get camera properties.
        self.properties = self.get_camera_properties()

        self.max_width = self.get_property_value("image_width")[0]
        self.max_height = self.get_property_value("image_height")[0]

        self.set_subarray_mode()

    def apply_parameters(self, parameters, *args, **kwargs):
        super().apply_parameters(*args, **kwargs)
        subarray = parameters.subarray
        # quantizing the ROI dims in multiples of 4
        subarray = [min((i * parameters.binning // 4) * 4, 2048) for i in subarray]
        # this can be simplified by making the API nice
        self.set_property_value("binning", parameters.binning)
        self.set_property_value(
            "exposure_time", 0.001 * parameters.exposure_time
        )
        self.set_property_value("subarray_vpos", subarray[1])
        self.set_property_value("subarray_hpos", subarray[0])
        self.set_property_value("subarray_vsize", subarray[3])
        self.set_property_value("subarray_hsize", subarray[2])
        self.set_property_value(
            "trigger_source", parameters.trigger_mode.value
        )

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

    def get_camera_properties(self):
        super().get_camera_properties()
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
                self.convert_property_name(c_buf.value.decode(self.encoding))
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
                    self.camera_handle, prop_id, c_buf, ctypes.c_int32(c_buf_len),
                ),
                "dcamprop_getname",
            )
        return properties

    def get_frames(self):
        super().get_frames()
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
                0, 0, DCAMWAIT_CAPEVENT_FRAMEREADY | DCAMWAIT_CAPEVENT_STOPPED, 100,
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
            print(">> Warning! hamamatsu camera frame buffer overrun detected!")
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

        for n in new_frames:
            frames.append(self.hcam_data[n].get_data())

        return frames

    def get_internal_parameters(self, parameters, *args, **kwargs):
        super().get_internal_parameters(*args, **kwargs)
        # subarray has to be updated with camera info directly because it must be a multiple of 4
        frame_shape = (
            self.get_property_value("subarray_vsize")[0]
            // parameters.binning,
            self.get_property_value("subarray_hsize")[0]
            // parameters.binning,
        )

        internal_frame_rate = self.get_property_value("internal_frame_rate")[0]

        return tuple([frame_shape, internal_frame_rate])

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
                text_options[prop_text.text.decode(self.encoding)] = int(v.value)

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

    def get_property_value(self, property_name, *args, **kwargs):
        super().get_property_value(*args, **kwargs)

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False
        prop_id = self.properties[property_name]

        # Get the property attributes.
        prop_attr = self.get_property_value(property_name)

        # Get the property value.
        c_value = ctypes.c_double(0)
        self.check_status(
            self.dcam.dcamprop_getvalue(
                self.camera_handle, ctypes.c_int32(prop_id), ctypes.byref(c_value),
            ),
            "dcamprop_getvalue",
        )

        # Convert type based on attribute type.
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if temp == DCAMPROP_TYPE_MODE:
            prop_type = "MODE"
            prop_value = int(c_value.value)
        elif temp == DCAMPROP_TYPE_LONG:
            prop_type = "LONG"
            prop_value = int(c_value.value)
        elif temp == DCAMPROP_TYPE_REAL:
            prop_type = "REAL"
            prop_value = c_value.value
        else:
            prop_type = "NONE"
            prop_value = False

        return [prop_value, prop_type]

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

    def set_property_value(self, property_name, property_value, *args, **kwargs):
        super().set_property_value(*args, **kwargs)
        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False

        # If the value is text, figure out what the
        # corresponding numerical property value is.
        if isinstance(property_value, str):
            text_values = self.get_property_text(property_name)
            if property_value in text_values:
                property_value = float(text_values[property_value])
            else:
                print(
                    " unknown property text value:",
                    property_value,
                    "for",
                    property_name,
                )
                return False

        # Check that the property is within range.
        [pv_min, pv_max] = self.get_property_range(property_name)
        if property_value < pv_min:
            print(
                " set property value",
                property_value,
                "is less than minimum of",
                pv_min,
                property_name,
                "setting to minimum",
            )
            property_value = pv_min
        if property_value > pv_max:
            print(
                " set property value",
                property_value,
                "is greater than maximum of",
                pv_max,
                property_name,
                "setting to maximum",
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

    def start_acquisition(self):
        super().start_acquisition()
        self.buffer_index = -1
        self.last_frame_number = 0

        # Set sub array mode.
        self.set_subarray_mode()

        # Get frame properties.
        self.frame_x = self.get_property_value("image_width")[0]
        self.frame_y = self.get_property_value("image_height")[0]
        self.frame_bytes = self.get_property_value("image_framebytes")[0]

        # Allocate new image buffers if necessary. This will allocate
        # as many frames as can fit in 2GB of memory, or 2000 frames,
        # which ever is smaller. The problem is that if the frame size
        # is small than a lot of buffers can fit in 2GB. Assuming that
        # the camera maximum speed is something like 1KHz 2000 frames
        # should be enough for 2 seconds of storage, which will hopefully
        # be long enough.
        #
        if (self.old_frame_bytes != self.frame_bytes) or (
                self.acquisition_mode == "fixed_length"
        ):

            n_buffers = min(int((2.0 * 1024 * 1024 * 1024) / self.frame_bytes), 2000)
            if self.acquisition_mode == "fixed_length":
                self.number_image_buffers = self.number_frames
            else:
                self.number_image_buffers = n_buffers

            # Allocate new image buffers.
            ptr_array = ctypes.c_void_p * self.number_image_buffers
            self.hcam_ptr = ptr_array()
            self.hcam_data = []
            for i in range(self.number_image_buffers):
                hc_data = SpeedyArrayBuffer(self.frame_bytes)
                self.hcam_ptr[i] = hc_data.get_data_pr()
                self.hcam_data.append(hc_data)

            self.old_frame_bytes = self.frame_bytes

        # Attach image buffers and start acquisition.
        #
        # We need to attach & release for each acquisition otherwise
        # we'll get an error if we try to change the ROI in any way
        # between acquisitions.

        paramattach = DCAMBUF_ATTACH(
            0, DCAMBUF_ATTACHKIND_FRAME, self.hcam_ptr, self.number_image_buffers,
        )
        paramattach.size = ctypes.sizeof(paramattach)

        if self.acquisition_mode == "run_till_abort":
            self.check_status(
                self.dcam.dcambuf_attach(self.camera_handle, paramattach),
                "dcam_attachbuffer",
            )
            self.check_status(
                self.dcam.dcamcap_start(self.camera_handle, DCAMCAP_START_SEQUENCE),
                "dcamcap_start",
            )
        if self.acquisition_mode == "fixed_length":
            paramattach.buffercount = self.number_frames
            self.check_status(
                self.dcam.dcambuf_attach(self.camera_handle, paramattach),
                "dcambuf_attach",
            )
            self.check_status(
                self.dcam.dcamcap_start(self.camera_handle, DCAMCAP_START_SNAP),
                "dcamcap_start",
            )

    def stop_acquistion(self):
        super().stop_acquistion()
        self.check_status(self.dcam.dcamcap_stop(self.camera_handle), "dcamcap_stop")

        # Free image buffers.
        if self.hcam_ptr:
            self.check_status(
                self.dcam.dcambuf_release(self.camera_handle, DCAMBUF_ATTACHKIND_FRAME),
                "dcambuf_release",
            )

    def shutdown(self):
        super().shutdown()
        self.check_status(self.dcam.dcamwait_close(self.wait_handle), "dcamwait_close")
        self.check_status(self.dcam.dcamdev_close(self.camera_handle), "dcamdev_close")
