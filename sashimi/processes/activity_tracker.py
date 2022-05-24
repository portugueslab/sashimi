from multiprocessing import Queue
from multiprocessing import Process
from queue import Empty
import flammkuchen as fl
import numpy as np
from tkinter import *
from timeit import default_timer as timer

PATH_OUT = r"C:\Users\portugueslab\Desktop\Ema_test\result_fish0.h5"
PATH_IN = r"C:\Users\portugueslab\Desktop\scc_protocol.h5"
TH_CELL_ACTIVITY = 0.1


def create_bin_circle(arr_size, center, r):
    coords = np.ogrid[:arr_size[0], :arr_size[1]]
    distance = np.sqrt((coords[0] - center[0]) ** 2 + (coords[1] - center[1]) ** 2)
    return 1 * (distance <= r)


class ActivityTracker(Process):
    def __init__(
            self,
            stop_event: Event,
            experiment_start_event: Event,
            is_waiting_event: Event,
            roi_activity_queue: Queue,
            duration_queue: Queue,
    ):
        super().__init__(name="activity_tracker")
        self.current_settings_queue = Queue()
        self.current_settings = None
        self.current_roi_activity_queue = Queue()
        self.roi_activity_queue = roi_activity_queue
        self.current_settings = None
        self.start_comm = experiment_start_event
        self.stop_event = stop_event
        self.is_waiting_event = is_waiting_event
        self.duration_queue = duration_queue
        self.gui = None
        self.roi_state = 0
        self.tau_lowpass = 0
        self.radius_roi = 0
        self.center_roi = np.array([0, 0])
        self.first_value = True
        self.creation = False
        self.changed = False
        self.current_settings = None
        self.protocol = None
        self.elapsed_t = 0
        self.prev_t = None

        self.t_recording = []
        self.activity_recording = []
        self.led_state_recording = []

    def run(self):
        if self.creation is False:
            self.create_actuator()
            self.creation = True
        while True:
            if self.start_comm.is_set():
                while not self.stop_event.is_set():
                    if self.prev_t is None:
                        self.prev_t = timer()
                    else:
                        self.elapsed_t += (timer() - self.prev_t)
                        self.prev_t = timer()
                    while True:
                        try:
                            current_settings = self.current_settings_queue.get(
                                timeout=0.00001
                            )
                            if current_settings is not None:
                                self.current_settings = current_settings
                                self.changed = True
                        except Empty:
                            break
                    img = self.check_last_image()
                    if (img is not None) and (self.current_settings is not None):
                        if self.changed:
                            mask = create_bin_circle(img.shape,
                                                     np.array([self.current_settings["x_roi"],
                                                               self.current_settings["y_roi"]]),
                                                     self.current_settings["roi_radius"])
                            self.mask = mask
                            self.changed = False
                        if np.sum(self.mask > 0) > 0:
                            roi_value = np.nanmean(img[self.mask > 0])
                        else:
                            roi_value = 0
                        if self.first_value:
                            self.roi_state = roi_value
                            self.first_value = False
                        else:
                            prev_val = self.roi_state
                            self.roi_state = prev_val + (self.current_settings["tau_lowpass"] * (roi_value - prev_val))
                            self.actuator(self.roi_state - prev_val)
                self.finish()

    def actuator(self, activity_value):
        print(activity_value)
        cl_state = np.interp(self.elapsed_t, self.protocol["t"], self.protocol["cl"])
        if cl_state == 1:
            if activity_value >= TH_CELL_ACTIVITY:
                led_state = 1
                self.gui.configure(bg='white')
            else:
                led_state = 0
                self.gui.configure(bg='gray')
        else:
            led_state = np.interp(self.elapsed_t, self.protocol["t"], self.protocol["stim"])
            if led_state == 1:
                self.gui.configure(bg='white')
            elif led_state == -1:
                self.gui.configure(bg='black')
            else:
                self.gui.configure(bg='gray')

        self.t_recording.append(self.elapsed_t)
        self.activity_recording.append(self.roi_state)
        self.led_state_recording.append(led_state)
        self.gui.update()

    def create_actuator(self):
        # print("Creating actuator...")
        self.protocol = fl.load(PATH_IN)
        self.creation = True
        self.gui = Tk(className='Stimulus Display')
        self.gui.geometry("400x400")
        self.gui.configure(bg='gray')
        # self.gui.after(0, self.run_)
        self.gui.update()

    def check_last_image(self):
        image = None
        while True:
            try:
                image = self.roi_activity_queue.get(timeout=0.00001)
            except Empty:
                break
        return image

    def finish(self):
        dict_to_save = {"t": self.t_recording,
                        "cell_activity": self.activity_recording,
                        "stim": self.led_state_recording}
        fl.save(PATH_OUT, dict_to_save)
