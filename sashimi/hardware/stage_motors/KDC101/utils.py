import numpy as np
from time import sleep,time,ctime




def abs_to_mm(value, inverse):
    """

    Parameters
    ----------
    value: a int or array of positions (either in mm or absolute value)
    inverse: if False performs abs->mm
             if True performs mm->abs

    Returns
    -------
        does not return anything, but modifies the input

    """


    x1m = 1.0013
    x1a = 34350
    alpha = x1m / x1a
    beta = 1 / alpha

    if isinstance(value, int):
        if inverse:
            return int(value * beta)
        else:
            return value * alpha
    else:  # assume is array
        if inverse:
            return (np.array(value) * beta).astype(int)
        else:
            return np.array(value) * alpha
        
        
        
        

###################### MULTI-MOTOR UTILS (3 - X,Y,Z) ############################
def close_motors(motors):
    """
    Close every motor in a list
    """
    for mot in motors:
        #start the motor
        mot.stop()
        sleep(mot._pause)
        
        
def init_motors(motors, poll=200, pause=0.3, acc=800, vel=2e6,  verbose = False, home = False):
    """
    Initialize every motor in a list
    """
    
    for mot in motors:
        #polling
        mot.polling = poll
        #pause
        mot._pause = pause
        #verbose
        mot.verbose = verbose
        mot.set_vel_params(acc, vel)

        #start the motor
        mot.start()
        sleep(mot._pause)
    
    if home:
        home_motors(motors)
        
def home_motors(motors):
    """
    Home every motor in a list
    """
    
    for mot in motors:
        mot.home()
        sleep(mot._pause)
       
    
    safety_counter = 0
    pos = [round(mot.position_mm, 3) for mot in motors]
    
    while not all(np.subtract(pos,0) == 0):
        
        pos = [round(mot.position_mm, 3) for mot in motors]
        sleep(motors[0]._pause * 2)
        
        safety_counter +=1 
        
        if safety_counter > 70:
            print("Homing Failed - Timer runout!")
            break

    if all(np.subtract(pos,0) == 0):
            print("Homing Succeded")
            
##################################################
def reached_target(pos, goal,ths = int(100 - 1e-3)):
    """
    check if the motor has reached the target
    """
    if isinstance(pos, np.ndarray) or isinstance(pos, list):

        acc = np.array([ 100*(1-abs((pos[i]-goal[i])/goal[i])) for i in range(len(pos))])

        #if accuracy is negative set it to zero
        acc[acc<0] = 0

        
        if pos == goal:#safety check
            return True
        
        #return true if all of the elements are above threshold
        return all(acc>ths)
        
    elif isinstance(pos, float) or isinstance(pos, int):
        #compute percentage accuracy
        acc = 100*(1-abs((pos-goal)/goal))

        #if accuracy is negative set it to zero
        if acc < 0: 
            acc = 0

        #return true if  above threshold
        return (acc>ths)
       
    else:
        print(pos, goal)
        raise ValueError("input type cannot be handled, try using a float, int or array")



def move_to_mm(motors, end_pos, ths = 100-1e-3, verbose = False):
    """
    Move multiple motors to each location [mot1,mot2] -> [pos1, pos2]
    the positions must me in mm
    
    Returns:
        dictionary with metadata:
            -'End_x','End_y','End_z' = target position
            -'Pos x','Pos y','Pos z' = actual final position
            -'Date' 
            -'Time Stamp'
    """
    
    #get position 
    pos = [mot.position_mm for mot in motors]
    
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
                mot.move_to(end_pos[i])
                
        #feedback motor moving
        while not reached_target(pos, end_pos, ths):
            #get position 
            pos = [mot.position_mm for mot in motors]
            sleep(motors[0]._pause)
            
            if verbose:
                clear_output(wait=True)
                print("Moving motors..")
                for i, p in enumerate(pos):
                    print(f"Motor  - pos = {p} - desired pos = {end_pos[i]}")
                    
        t = time() #target reached
        
        #motor at the desired position
        if verbose:
            clear_output(wait=True)
            print("Motors position:")
            for i, p in enumerate(pos):
                    print(f"Motor  - pos = {p} - desired pos = {end_pos[i]}")
                    
        return {'End_x': end_pos[0],
                'End_y': end_pos[1],
                'End_z': end_pos[2],
                'Pos x': pos[0],
                'Pos y': pos[1],
                'Pos z': pos[2],
                'Date': ctime(t),
                'Time Stamp': t}
    
def move_to_abs(motors, end_pos, ths = 100-1e-3, verbose = False):
    
    """
    Move multiple motors to each location [mot1,mot2] -> [pos1, pos2]
    the positions must me in abs
    
    Returns:
        dictionary with metadata:
            -'End_x','End_y','End_z' = target position
            -'Pos x','Pos y','Pos z' = actual final position
            -'Date' 
            -'Time Stamp'
    """
    
    #get position 
    pos = [mot.position_abs for mot in motors]
    
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
                mot.move_to_abs(end_pos[i])
                
        #feedback motor moving
        while not reached_target(pos, end_pos, ths):
            #get position 
            pos = [mot.position_abs for mot in motors]
            sleep(motors[0]._pause)
            
            if verbose:
                clear_output(wait=True)
                print("Moving motors..")
                for i, p in enumerate(pos):
                    print(f"Motor  - pos = {p} - desired pos = {end_pos[i]}")
                    
        t = time() #target reached
        
        #motor at the desired position
        if verbose:
            clear_output(wait=True)
            print("Motors position:")
            for i, p in enumerate(pos):
                    print(f"Motor  - pos = {p} - desired pos = {end_pos[i]}")
                    
        return {'End_x': end_pos[0],
                'End_y': end_pos[1],
                'End_z': end_pos[2],
                'Pos x': pos[0],
                'Pos y': pos[1],
                'Pos z': pos[2],
                'Date': ctime(t),
                'Time Stamp': t}
    
    
    
