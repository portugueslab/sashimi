import KCube_py_int as kdc
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
# from tqdm import tqdm
from sashimi.hardware.stage_motors.interface import AbstractMotor


##################################################

def check_pos(pos, goal, ths = int(100 - 1e-3)):
    acc = accuracy(pos,goal)
    #return true if all of the elements are above threshold
    return all(acc>ths)

##################################################

def check_move(pos, goal, ths= int(100 - 1e-3)):
    acc = accuracy(pos,goal)
    #return true if all of the elements are above threshold
    return all(acc>ths)

##################################################
def reached_target(pos, goal,ths = int(100 - 1e-3)):
    #compute percentage accuracy
    acc = 100*(1-abs((pos-goal)/goal))
    #if accuracy is negative set it to zero
    if acc < 0: acc = 0
    
    #return true if  above threshold
    return (acc>ths)

##################################################

def accuracy(pos,goal):
    #compute percentage accuracy for each motor
    acc = np.array([ 100*(1-abs((pos[i]-goal[i])/goal[i])) for i in range(len(pos))])
    #if accuracy is negative set it to zero
    acc[acc<0] = 0
    return acc

##################################################
#     max = 12mm min -0.3 mm
def check_val(ranges,start_pos):
    max_val = to_mm(12, False)
    min_val = to_mm(0, False)      #-0.3
    
    #check if start is inside range starting from top left corner
    print("start pos", start_pos)
    print("max", max_val)
    print("min", min_val)
    if  all(np.array(start_pos)>min_val) and all(np.array(start_pos)<max_val):
        print("ok1")
        if ((max_val - start_pos[1] - min_val) >ranges[1]) and (max_val - start_pos[0] - min_val>ranges[0]) and (max_val - start_pos[2] - min_val>ranges[2]):
            print("ok2")
            return True
        else:
            return False
    else:
        return False
    
    
##################################################
    
def to_mm(array, inverse):
    x1m = 1.0013
    x1a = 34350
    alpha = x1m/x1a
    beta = 1/alpha
    
    if isinstance(array, int):
        if not inverse:
            return int(array*beta)
        else:
            return array*alpha
    else: #assume is array
        if not inverse:
            return (np.array(array)*beta).astype(int)
        else:
            return np.array(array)*alpha
    

##################################################

def setVal_Motors(motors, poll=200, pause=0.4, acc=800, vel=2e6,  verbose = False, home = False):
    #set parameters
    for mot in motors:
        #polling
        mot.set_Polling(poll)
        #pause
        mot.set_Pause(pause)
        #verbose
        mot.set_Verbose(verbose)
        mot.set_velParams(acc, vel)

        #start the motor
        mot.start()
        sleep(pause)
    
    if home:
        homing(motors, pause)   
    
    
##################################################
    
def homing(motors, pause):
    for mot in motors:
        mot.homing()
        sleep(pause)
        
    while True:
        pos = [mot.get_pos() for mot in motors]
        if all(np.subtract(pos,0) == 0):
            print("Homing Succeded")
            break
            
            
##################################################
def close_Motors(motors):
    for mot in motors:
        #start the motor
        mot.stop()
        sleep(mot.pause)

        
##################################################
def moveTo(motors, end_pos, ths, verbose):
    
    #get position 
    pos = [mot.get_pos() for mot in motors]
    
    #check if end pos elements equal pos
    check =  abs(np.subtract(pos,end_pos)) > abs(ths -100)
    
    if len(motors) != len(pos):
        print("Error - motors and end_pos should have the same length")
        return
    else:
        #Moning the motors
        for i, mot in enumerate(motors):
            #if i am not already there, move
            if check[i]:
#                 print("moving mot ", i)
                mot.moveTo_abs(end_pos[i])
                
        #feedback motor moving
        while not check_move(pos, end_pos, ths):
            #get position 
            pos = [mot.get_pos() for mot in motors]
            
            if verbose:
                # clear_output(wait=True)
                print("Moving motors..")
                for i, p in enumerate(pos):
                    print(f"Motor  - pos = {p} - desired pos = {end_pos[i]}")
        
        #motor at the desired position
        if verbose:
            # clear_output(wait=True)
            print("Motors position:")
            for i, p in enumerate(pos):
                    print(f"Motor  - pos = {p} - desired pos = {end_pos[i]}")
                    
        return {'End_x': end_pos[0],
                'End_y': end_pos[1],
                'End_z': end_pos[2],
                'Pos x': pos[0],
                'Pos y': pos[1],
                'Pos z': pos[2],
                'Accuracy': accuracy(pos, end_pos),
                'Mean Accuracy': np.mean(accuracy(pos, end_pos)),
                'Time Stamp': time.time()}
    
    
    
##################################################
def stage_cycle(motors, start_pos, end_pos, n_steps, delay, ths,f_n,note, verbose):
    
    #step for each axes
    x_steps = n_steps[0]
    y_steps = n_steps[1]
    z_steps = n_steps[2]
    
    #ranges for each axis
    x_range = np.linspace(start_pos[0],end_pos[0], x_steps).astype(int)
    y_range = np.linspace(start_pos[1],end_pos[1], y_steps).astype(int)
    z_range = np.linspace(start_pos[2],end_pos[2], z_steps).astype(int)
    
    x_bool = True
    arra = []
    
    #get ids
    ids = [mot.get_id() for mot in motors]
    
    meta = {'Ids': ids,
                'steps': n_steps,
                'ranges': [x_range,y_range,z_range],
                'start_pos': start_pos,
                'start_time': time.time(),
                'delay': delay,
                'fish_n': f_n,
                'note': note}
    
    
    #cycle
    # pbar2 = tqdm(total=(x_steps*y_steps*(z_steps-1)), desc="Moving..",mininterval=0.5, maxinterval =15, position=0, leave=True)
    for z in  range(z_steps-1):
        if z%2==0:
            for y in range(0, y_steps, 1):
                if x_bool:
                    for x in range(0, x_steps, 1):
                        
                        #move to position
                        arra.append(moveTo(motors, [x_range[x], y_range[y], z_range[z]], ths, verbose))
                        # pbar2.update(1)
                        sleep(delay)

                    x_bool = False
                else:
                    for x in range(x_steps-1, -1, -1):
                        
                        #move to position
                        arra.append(moveTo(motors, [x_range[x], y_range[y], z_range[z]], ths, verbose))
                        # pbar2.update(1)
                        sleep(delay)
                        
                    x_bool = True

        else:
            for y in range(y_steps-1, -1, -1):
                if x_bool:
                    for x in range(0, x_steps, 1):
                        
                        #move to position
                        arra.append(moveTo(motors, [x_range[x], y_range[y], z_range[z]], ths, verbose))
                        # pbar2.update(1)
                        sleep(delay)
                        
                    x_bool = False
                else:
                    for x in range(x_steps-1, -1, -1):
                        
                        #move to position
                        arra.append(moveTo(motors, [x_range[x], y_range[y], z_range[z]], ths, verbose))
                        # pbar2.update(1)
                        sleep(delay)
                        
                    x_bool = True
            
    # pbar2.close()
    return pd.DataFrame(arra),pd.DataFrame(meta)
##################################################
# def saveData(data,meta):
#     save_p = save_name + "_data.csv"
#     save_m = save_name + "_metadata.csv"
#
#     data.to_csv(save_p)
#     meta.to_csv(save_m)
##################################################


class KC_motor(AbstractMotor):
    '''Building our functions on top of the KCube class from Thorlabs'''
    # Attention: this is all for one motor. The loop will do the for motor in motors
    # Default values set for each motor upon initialization, can be altered
    def __init__(self, serial_no, poll=200, pause=0.4, acc=800, vel=2e6, 
                 motor_axis=str, max_range=13.0, verbose=False):

        self.id = c_char_p(bytes(serial_no, "utf-8"))
        self.poll = poll
        self.pause = pause
        self.acc = acc
        self.vel = vel
        self.msg = []
        self.verbose = verbose
        self.motor_axis = motor_axis #x,y,z for logging
        self.max_range = max_range

        self.max_vel = kdc.c_int()  # to work on it
        self.acc = kdc.c_int()  # to work on it

        self.isOpen = False

        KC_motor.set_Polling(self, self.poll) #polling
        KC_motor.set_Pause(self, self.pause) #pause
        KC_motor.set_Verbose(self, self.verbose) #verbose
        KC_motor.set_velParams(self)

    def get_id(self):
        return self.id

    def set_Polling(self, polling_ms = 200):
        
        self.poll = c_int(polling_ms)
        
        #if motor already open reset polling
        if self.isOpen:
            kdc.CC_StartPolling(self.id, self.poll)
            self.msg.append("Start - Polling at " + str(self.poll))
    
    def set_Pause(self, sleep_s = 0.4):
        self.pause = sleep_s
        
    def set_Verbose(self, verb = False):
        self.ver = verb
        
    def start(self):
        if kdc.TLI_BuildDeviceList() == 0:
            self.msg.append("Start - Device list builded correctly.")
            
            if kdc.CC_Open(self.id) == 0:
                self.msg.append(f"Start - Opening motor {self.id}.")
                self.isOpen = True
                
                #start polling
                kdc.CC_StartPolling(self.id, self.poll)
                self.msg.append("Start - Polling at {self.poll}.")
                
                #clear message queue
                kdc.CC_ClearMessageQueue(self.id)
                self.msg.append("Start - Message queue cleared.")
                
                
            else:
                self.msg.append(f"Start - Error: Can't Open {self.id}.")

        else:
            self.msg.append("Start - Error: Can't build device list.")
    
        
        if self.ver: return self.msg
        

    def stop(self):
        
        kdc.CC_StopPolling(self.id)
        self.msg.append("Stop - polling stopped.")
        
        if kdc.CC_Close(self.id) == 0:
            self.msg.append("Stop - motor closed.")
            self.isOpen = False
            
        else:
            self.msg.append("Stop - Error: couldn't close the motor.")

        if self.ver: return self.msg
        
        
    def homing(self):
        
        if kdc.CC_Home(self.id) == 0:
            self.msg.append("Homing started.")
            sleep(self.pause)
            
        else:
            self.msg.append("Couldn't home.")

        if self.ver: return self.msg
        

    def get_pos(self):
        return kdc.CC_GetPosition(self.id)
    

    def get_velParams(self):
        
        #request parameters
        if kdc.CC_RequestVelParams(self.id) == 0:
            self.msg.append("Requested vel Params.")
            
            #get parameters
            if kdc.CC_GetVelParams(self.id, byref(self.acc), byref(self.max_vel)) == 0:
                self.msg.append(f"acc = {self.acc} - max_vel = {self.max_vel}.")
                
                if self.ver:
                    return [self.acc, self.max_vel, self.msg]
                else: 
                    return [self.acc, self.max_vel]
            else:
                self.msg.append("Error - Couldn't get vel params.")
                if self.ver: return self.msg
        else:
            self.msg.append("Error - Couldn't request vel params.")
            if self.ver: return self.msg
            
    
    def set_velParams(self, acc = 800, vel = 2e6):
        
        #request parameters
        if kdc.CC_RequestVelParams(self.id) == 0:
            self.msg.append("Requested vel Params.")
            
            self.acc = kdc.c_int(int(acc))
            self.max_vel = kdc.c_int(int(vel))
            
            #set parameters
            kdc.CC_SetVelParams(self.id, self.acc, self.max_vel)
            self.msg.append(f"Setted - acc = {self.acc} - max_vel = {self.max_vel}.")
                
        else:
            self.msg.append("Error - Couldn't request vel params.")
    
        if self.ver: return self.msg
    
    
    def moveTo_abs(self, position):
        #set move position 
        kdc.CC_SetMoveAbsolutePosition(self.id, c_int(position))
        
        #move to position
        kdc.CC_MoveAbsolute(self.id)
        self.msg.append(f"Moving to {position}")
        sleep(self.pause)


        
        

        