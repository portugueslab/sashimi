import ctypes
import numpy as np


## DCAMAPI_INIT
#
# The dcam initialization structure
#
class CameraFields(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("iDeviceCount", ctypes.c_int32),
        ("reserved", ctypes.c_int32),
        ("initoptionbytes", ctypes.c_int32),
        ("initoption", ctypes.POINTER(ctypes.c_int32)),
        ("guid", ctypes.POINTER(ctypes.c_int32))
    ]


def convertPropertyName(p_name):
    """
    "Regularizes" a property name. We are using all lowercase names with
    the spaces replaced by underscores.
    """
    return p_name.lower().replace(" ", "_")


class HamamatsuOrcaFlashAPI:
    def __init__(self):
        #
        # Initialization
        #
        self.dcam = ctypes.windll.dcamapi

        paraminit = CameraFields(0, 0, 0, 0, None, None)
        paraminit.size = ctypes.sizeof(paraminit)
        error_code = self.dcam.dcamapi_init(ctypes.byref(paraminit))
        n_cameras = paraminit.iDeviceCount


class HCamData(object):
    """
    Hamamatsu camera data object.

    Initially I tried to use create_string_buffer() to allocate storage for the
    data from the camera but this turned out to be too slow. The software
    kept falling behind the camera and create_string_buffer() seemed to be the
    bottleneck.

    Using numpy makes a lot more sense anyways..
    """

    def __init__(self, size=None, **kwds):
        """
        Create a data object of the appropriate size.
        """
        super().__init__(**kwds)
        self.np_array = np.ascontiguousarray(
            np.empty(int(size / 2), dtype=np.uint16)
        )
        self.size = size

    def __getitem__(self, slice):
        return self.np_array[slice]

    def copyData(self, address):
        """
        Uses the C memmove function to copy data from an address in memory
        into memory allocated for the numpy array of this object.
        """
        ctypes.memmove(self.np_array.ctypes.data, address, self.size)

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data
