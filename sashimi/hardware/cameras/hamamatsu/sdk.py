import ctypes

# DCAM4 hamamatsu.
DCAMERR_ERROR = 0
DCAMERR_NOERROR = 1

DCAMPROP_ATTR_HASVALUETEXT = int("0x10000000", 0)
DCAMPROP_ATTR_READABLE = int("0x00010000", 0)
DCAMPROP_ATTR_WRITABLE = int("0x00020000", 0)

DCAMPROP_OPTION_NEAREST = int("0x80000000", 0)
DCAMPROP_OPTION_NEXT = int("0x01000000", 0)
DCAMPROP_OPTION_SUPPORT = int("0x00000000", 0)

DCAMPROP_TYPE_MODE = int("0x00000001", 0)
DCAMPROP_TYPE_LONG = int("0x00000002", 0)
DCAMPROP_TYPE_REAL = int("0x00000003", 0)
DCAMPROP_TYPE_MASK = int("0x0000000F", 0)

DCAMCAP_STATUS_ERROR = int("0x00000000", 0)
DCAMCAP_STATUS_BUSY = int("0x00000001", 0)
DCAMCAP_STATUS_READY = int("0x00000002", 0)
DCAMCAP_STATUS_STABLE = int("0x00000003", 0)
DCAMCAP_STATUS_UNSTABLE = int("0x00000004", 0)

DCAMWAIT_CAPEVENT_FRAMEREADY = int("0x0002", 0)
DCAMWAIT_CAPEVENT_STOPPED = int("0x0010", 0)

DCAMWAIT_RECEVENT_MISSED = int("0x00000200", 0)
DCAMWAIT_RECEVENT_STOPPED = int("0x00000400", 0)
DCAMWAIT_TIMEOUT_INFINITE = int("0x80000000", 0)

DCAM_DEFAULT_ARG = 0

DCAM_IDSTR_MODEL = int("0x04000104", 0)

DCAMCAP_TRANSFERKIND_FRAME = 0

DCAMCAP_START_SEQUENCE = -1
DCAMCAP_START_SNAP = 0

DCAMBUF_ATTACHKIND_FRAME = 0


# Hamamatsu structures.

## DCAMAPI_INIT
#
# The dcam initialization structure
#
class DCAMAPI_INIT(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("iDeviceCount", ctypes.c_int32),
        ("reserved", ctypes.c_int32),
        ("initoptionbytes", ctypes.c_int32),
        ("initoption", ctypes.POINTER(ctypes.c_int32)),
        ("guid", ctypes.POINTER(ctypes.c_int32)),
    ]


## DCAMDEV_OPEN
#
# The dcam open structure
#
class DCAMDEV_OPEN(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("index", ctypes.c_int32),
        ("hdcam", ctypes.c_void_p),
    ]


## DCAMWAIT_OPEN
#
# The dcam wait open structure
#
class DCAMWAIT_OPEN(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("supportevent", ctypes.c_int32),
        ("hwait", ctypes.c_void_p),
        ("hdcam", ctypes.c_void_p),
    ]


## DCAMWAIT_START
#
# The dcam wait start structure
#
class DCAMWAIT_START(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("eventhappened", ctypes.c_int32),
        ("eventmask", ctypes.c_int32),
        ("timeout", ctypes.c_int32),
    ]


## DCAMCAP_TRANSFERINFO
#
# The dcam capture info structure
#
class DCAMCAP_TRANSFERINFO(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("iKind", ctypes.c_int32),
        ("nNewestFrameIndex", ctypes.c_int32),
        ("nFrameCount", ctypes.c_int32),
    ]


## DCAMBUF_ATTACH
#
# The dcam buffer attachment structure
#
class DCAMBUF_ATTACH(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("iKind", ctypes.c_int32),
        ("buffer", ctypes.POINTER(ctypes.c_void_p)),
        ("buffercount", ctypes.c_int32),
    ]


## DCAMBUF_FRAME
#
# The dcam buffer frame structure
#
class DCAMBUF_FRAME(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("iKind", ctypes.c_int32),
        ("option", ctypes.c_int32),
        ("iFrame", ctypes.c_int32),
        ("buf", ctypes.c_void_p),
        ("rowbytes", ctypes.c_int32),
        ("type", ctypes.c_int32),
        ("width", ctypes.c_int32),
        ("height", ctypes.c_int32),
        ("left", ctypes.c_int32),
        ("top", ctypes.c_int32),
        ("timestamp", ctypes.c_int32),
        ("framestamp", ctypes.c_int32),
        ("camerastamp", ctypes.c_int32),
    ]


## DCAMDEV_STRING
#
# The dcam device string structure
#
class DCAMDEV_STRING(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("iString", ctypes.c_int32),
        ("text", ctypes.c_char_p),
        ("textbytes", ctypes.c_int32),
    ]


## DCAMPROP_ATTR
#
# The dcam property attribute structure.
#
class DCAMPROP_ATTR(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_int32),
        ("iProp", ctypes.c_int32),
        ("option", ctypes.c_int32),
        ("iReserved1", ctypes.c_int32),
        ("attribute", ctypes.c_int32),
        ("iGroup", ctypes.c_int32),
        ("iUnit", ctypes.c_int32),
        ("attribute2", ctypes.c_int32),
        ("valuemin", ctypes.c_double),
        ("valuemax", ctypes.c_double),
        ("valuestep", ctypes.c_double),
        ("valuedefault", ctypes.c_double),
        ("nMaxChannel", ctypes.c_int32),
        ("iReserved3", ctypes.c_int32),
        ("nMaxView", ctypes.c_int32),
        ("iProp_NumberOfElement", ctypes.c_int32),
        ("iProp_ArrayBase", ctypes.c_int32),
        ("iPropStep_Element", ctypes.c_int32),
    ]


## DCAMPROP_VALUETEXT
#
# The dcam text property structure.
#
class DCAMPROP_VALUETEXT(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_int32),
        ("iProp", ctypes.c_int32),
        ("value", ctypes.c_double),
        ("text", ctypes.c_char_p),
        ("textbytes", ctypes.c_int32),
    ]


class CameraFields(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int32),
        ("iDeviceCount", ctypes.c_int32),
        ("reserved", ctypes.c_int32),
        ("initoptionbytes", ctypes.c_int32),
        ("initoption", ctypes.POINTER(ctypes.c_int32)),
        ("guid", ctypes.POINTER(ctypes.c_int32)),
    ]
