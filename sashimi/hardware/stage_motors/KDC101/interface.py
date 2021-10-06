import KDC101.KCube_py_int as kdc
from ctypes import (
    c_short,
    c_int,
    c_char_p,
    byref,
)
import time
import numpy as np
import pandas as pd
from time import sleep
from interface import AbstractMotor
from KDC101.utils import *

#Building our functions on top of the KCube class from Thorlabs
class KC_motor(AbstractMotor):
    """
    Class to initialize and controll the stage motors (KDC101 thorlabs)

    Methods

    """

    # Default values set for each motor upon initialization, can be altered
    def __init__(self, serial_no, poll=200, pause=0.4, acc=800, vel=2e6,
                 motor_axis=str, max_range=13.0, verbose=False):
        super().__init__(serial_no, max_range)
        """

        Parameters
        ----------
        serial_no = id of the motor
        poll = polling every n ms
        pause = wait time for initializazion and command sending
        acc = acceleration
        vel = velocity
        motor_axis = axis of the motor
        max_range = maximum range of the motor
        verbose = if True prints out each step

        isOpen = is the motor active
        msg = array of messages to keep track of errors
        """
        
        self.id = c_char_p(bytes(serial_no, "utf-8"))
        self.poll = c_int(poll)
        self._pause = pause
        self.acc = kdc.c_int(acc)
        self.vel = kdc.c_int(int(vel))
        self.msg = []
        self.verbose = verbose
        self.motor_axis = motor_axis #x,y,z for logging
        self.max_range = max_range

        self.max_vel = kdc.c_int(int(2e7))  # to work on it
#         self.acc = kdc.c_int(2000)  # to work on it

        self.isOpen = False
    
    
    def clear_msg(self):
        self.msg = []

    @property
    def axis(self):
        return self.motor_axis
    
    @property
    def get_id(self):
        return self.id

    @property
    def polling(self):
        return self.poll

    @polling.setter
    def polling(self, polling_ms=200):
        self.poll = c_int(polling_ms)

        # if motor already open reset polling
        if self.isOpen:
            kdc.CC_StartPolling(self.id, self.poll)
            self.msg.append("Start - Polling at " + str(self.poll))

    @property
    def pause(self):
        return self._pause

    @pause.setter
    def pause(self, sleep_s = 0.4):
        self._pause = sleep_s

    @property
    def verbose(self):
        return self.ver

    @verbose.setter
    def verbose(self, verb=False):
        self.ver = verb
        
    @property
    def maximum_range(self):
        return self.max_range

    @maximum_range.setter
    def maximum_range(self, max_range=13.0):
        self.max_range = float(max_range)

    @property
    def position_abs(self):
        return kdc.CC_GetPosition(self.id)
    
    @property
    def position_mm(self):
        return abs_to_mm(kdc.CC_GetPosition(self.id), False)

    
    def get_vel_params(self):
        """
        Gets the velocity parameters:
        - acceleration
        - velocity
        """
        # request parameters
        if kdc.CC_RequestVelParams(self.id) == 0:
            self.msg.append("Requested vel Params.")

            # get parameters
            if kdc.CC_GetVelParams(self.id, byref(self.acc), byref(self.vel)) == 0:
                self.msg.append(f"acc = {self.acc} - max_vel = {self.vel}.")

                if self.ver:
                    return [self.acc, self.max_vel, self.msg]
                else:
                    return [self.acc, self.max_vel]
            else:
                self.msg.append("Error - Couldn't get vel params.")
                if self.ver: 
                    return self.msg
        else:
            self.msg.append("Error - Couldn't request vel params.")
            if self.ver:
                return self.msg

    
    def set_vel_params(self, acc = 800, vel = 2e6):
        """

        Gets the velocity parameters:
        - acceleration
        - velocity

        """
        # request parameters
        if kdc.CC_RequestVelParams(self.id) == 0:
            self.msg.append("Requested vel Params.")

            self.acc = kdc.c_int(int(acc))
            self.max_vel = kdc.c_int(int(vel))

            # set parameters
            kdc.CC_SetVelParams(self.id, self.acc, self.max_vel)
            self.msg.append(f"Setted - acc = {self.acc} - max_vel = {self.max_vel}.")

        else:
            self.msg.append("Error - Couldn't set vel params.")

        if self.ver:
            return self.msg

    def start(self):
        """
        Starts the motor
        """
        if kdc.TLI_BuildDeviceList() == 0:
            self.msg.append("Start - Device list builded correctly.")

            if kdc.CC_Open(self.id) == 0:
                self.msg.append(f"Start - Opening motor {self.id}.")
                self.isOpen = True

                # start polling
                kdc.CC_StartPolling(self.id, self.poll)
                self.msg.append("Start - Polling at {self.poll}.")

                # clear message queue
                kdc.CC_ClearMessageQueue(self.id)
                self.msg.append("Start - Message queue cleared.")


            else:
                self.msg.append(f"Start - Error: Can't Open {self.id}.")

        else:
            self.msg.append("Start - Error: Can't build device list.")

        if self.ver:
            return self.msg

    def stop(self):
        """
        Stops the motor (only use when finished)
        """
        kdc.CC_StopPolling(self.id)
        self.msg.append("Stop - polling stopped.")

        if kdc.CC_Close(self.id) == 0:
            self.msg.append("Stop - motor closed.")
            self.isOpen = False

        else:
            self.msg.append("Stop - Error: couldn't close the motor.")

        if self.ver: 
            return self.msg

    def home(self):
        """
        Homes the motor:
            otherwise the motor will save as zero the last position used
        """
        if kdc.CC_Home(self.id) == 0:
            self.msg.append("Homing started.")
            sleep(self._pause)

        else:
            self.msg.append("Couldn't home.")

        if self.ver:
            return self.msg

    def move_to_abs(self, position):
        """
        Parameters
        ----------
        position = absolute value of where to move the motor

        no safeguard: if the position is bigger than
                        the maximum range the motor
                        may get stucked
        """

        # set move position
        kdc.CC_SetMoveAbsolutePosition(self.id, c_int(position))

        # move to position
        kdc.CC_MoveAbsolute(self.id)
        self.msg.append(f"Moving to {position}")
        sleep(self._pause)
        
        if self.ver:
            return self.msg

    def move_to(self, position):
        """
        Parameters
        ----------
        position = value of where to move the motor in mm

        safeguard: if the position is bigger than the max range then it skips

        """
        if self.check_limits(position):
            self.move_to_abs(abs_to_mm(position, True))
        else:
            self.msg.append("Error - position is greater than max range! {} > {}".format(position,self.max_range))
            
        if self.ver:
            return self.msg

    def check_limits(self, mm_position):
        """
        Checks if a given position is within the maximum range of the motor

        Returns: True or False

        """
#         print(mm_position)
        if self.max_range >= mm_position:
            return True
        else:
            return False
