"Bindings for Thorlabs Benchtop Brushless Motor DLL"
# flake8: noqa
from ctypes import (
    Structure,
    cdll,
    windll,
    c_bool,
    c_short,
    c_int,
    c_uint,
    c_int16,
    c_int32,
    c_char,
    c_byte,
    c_long,
    c_float,
    c_double,
    POINTER,
    CFUNCTYPE,
    CDLL,
    CFUNCTYPE,
    c_ushort,
    c_ulong,
)

import os

from typing import (
    Any,
    List,
)

c_word = c_ushort
c_dword = c_ulong


def bind(lib: CDLL, func: str,
         argtypes: List[Any]=None, restype: Any=None) -> CFUNCTYPE:
    _func = getattr(lib, func, null_function)
    _func.argtypes = argtypes
    _func.restype = restype

    return _func


def null_function():
    pass


__all__ = [
    bind,
    null_function,
    c_word,
    c_dword,
]



#path for dlls
master_path = os.getcwd()


dll_folder = "dlls_servo"
dll_lib = "dlls_servo\Thorlabs.MotionControl.KCube.DCServo.dll"


dlls_path = os.path.join(master_path,dll_folder)
lib_path = os.path.join(master_path,dll_lib)


#specify folder for dlls
os.chdir(dlls_path)
lib = cdll.LoadLibrary(lib_path)

MOT_TravelDirection = c_short
MOT_TravelModes = c_int

CC_Open = bind(lib, "CC_Open", [POINTER(c_char)], c_short)
CC_Close = bind(lib, "CC_Close", [POINTER(c_char)])
TLI_BuildDeviceList = bind(lib, "TLI_BuildDeviceList", None, c_short)
TLI_GetDeviceListSize = bind(lib, "TLI_GetDeviceListSize", None, c_short)
CC_MoveToPosition = bind(lib, "CC_MoveToPosition", [POINTER(c_char), c_int], c_short)
CC_GetPosition = bind(lib, "CC_GetPosition", [POINTER(c_char)], c_int)
CC_CanHome = bind(lib, "CC_CanHome", [POINTER(c_char)], c_bool)
CC_Home = bind(lib, "CC_Home", [POINTER(c_char)], c_short)
CC_ClearMessageQueue = bind(lib, "CC_ClearMessageQueue", [POINTER(c_char)])
CC_RequestHomingParams = bind(lib, "CC_RequestHomingParams", [POINTER(c_char)], c_short)
CC_GetHomingVelocity = bind(lib, "CC_GetHomingVelocity", [POINTER(c_char)], c_uint)
CC_SetHomingVelocity = bind(lib, "CC_SetHomingVelocity", [POINTER(c_char), c_uint], c_short)
CC_MoveRelative = bind(lib, "CC_MoveRelative", [POINTER(c_char), c_int], c_short)
CC_RequestVelParams = bind(lib, "CC_RequestVelParams", [POINTER(c_char)], c_short)
CC_GetVelParams = bind(lib, "CC_GetVelParams", [POINTER(c_char), POINTER(c_int), POINTER(c_int)], c_short)
CC_SetVelParams = bind(lib, "CC_SetVelParams", [POINTER(c_char), c_int, c_int], c_short)
CC_MoveAtVelocity = bind(lib, "CC_MoveAtVelocity", [POINTER(c_char), MOT_TravelDirection], c_short)
CC_SetMoveAbsolutePosition = bind(lib, "CC_SetMoveAbsolutePosition", [POINTER(c_char), c_int], c_short)
CC_RequestMoveAbsolutePosition = bind(lib, "CC_RequestMoveAbsolutePosition", [POINTER(c_char)], c_short)
CC_GetMoveAbsolutePosition = bind(lib, "CC_GetMoveAbsolutePosition", [POINTER(c_char)], c_int)
CC_MoveAbsolute = bind(lib, "CC_MoveAbsolute", [POINTER(c_char)], c_short)
CC_SetMoveRelativeDistance = bind(lib, "CC_SetMoveRelativeDistance", [POINTER(c_char), c_int], c_short)
CC_RequestMoveRelativeDistance = bind(lib, "CC_RequestMoveRelativeDistance", [POINTER(c_char)], c_short)
CC_GetMoveRelativeDistance = bind(lib, "CC_GetMoveRelativeDistance", [POINTER(c_char)], c_int)
CC_MoveRelativeDistance = bind(lib, "CC_MoveRelativeDistance", [POINTER(c_char)], c_short)
CC_StartPolling = bind(lib, "CC_StartPolling", [POINTER(c_char), c_int], c_bool)
CC_PollingDuration = bind(lib, "CC_PollingDuration", [POINTER(c_char)], c_long)
CC_StopPolling = bind(lib, "CC_StopPolling", [POINTER(c_char)])
CC_GetStageAxisMinPos = bind(lib, "CC_GetStageAxisMinPos", [POINTER(c_char)], c_int)
CC_GetStageAxisMaxPos = bind(lib, "CC_GetStageAxisMaxPos", [POINTER(c_char)], c_int)
CC_SetStageAxisLimits = bind(lib, "CC_SetStageAxisLimits", [POINTER(c_char), c_int, c_int], c_short)
CC_SetMotorTravelMode = bind(lib, "CC_SetMotorTravelMode", [POINTER(c_char), MOT_TravelModes], c_short)
CC_GetMotorTravelMode = bind(lib, "CC_GetMotorTravelMode", [POINTER(c_char)], MOT_TravelModes)