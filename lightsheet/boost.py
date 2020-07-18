from multiprocessing import Process, Queue, Event
from queue import Empty, Full
from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.utilities import neg_dif
import numpy as np
import time


class VolumeDispatcher(Process):
    def __init__(
            self,
            stop_event: Event,
            saving_signal: Event,
            wait_signal: Event,
            camera_queue: ArrayQueue,
            saver_queue: ArrayQueue,
            max_queue_size=500
    ):
        super().__init__()
        self.stop_event = stop_event
        self.saving_signal = saving_signal
        self.wait_signal = wait_signal
        self.camera_queue = camera_queue
        self.saver_queue = saver_queue
        self.n_planes_queue = Queue()
        self.viewer_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.calibration_ref_queue = ArrayQueue()
        self.volume_buffer = None
        self.current_frame = None
        self.calibration_ref = None
        self.n_planes = 1
        self.i_plane = 0
        self.first_volume = True
        self.experiment_started = False

    def run(self):
        while not self.stop_event.is_set():
            self.send_receive()
            if self.saving_signal.is_set() and not self.experiment_started:
                self.check_experiment_start()
            self.get_frame()
            self.loop()

    def loop(self):
        if self.current_frame is not None:
            if self.calibration_ref is not None:
                self.current_frame = neg_dif(self.current_frame, self.calibration_ref)
            if self.first_volume:
                self.volume_buffer = np.empty(self.n_planes, *self.current_frame)
                self.first_volume = False
            self.volume_buffer[self.i_plane, :, :] = self.current_frame
            self.i_plane += 1
            if self.i_plane == self.n_planes - 1:
                self.fill_queues()

    def fill_queues(self):
        if self.viewer_queue.queue.qsize() < 3:
            self.viewer_queue.put(self.volume_buffer)
        else:
            pass  # volume has been dropped from the viewer
        if self.saving_signal.is_set():
            self.saver_queue.put(self.volume_buffer)
        else:
            self.experiment_started = False

    def check_experiment_start(self):
        self.saver_queue.clear()
        self.current_frame = 0
        while self.wait_signal.is_set():
            self.camera_queue.clear()
            time.sleep(0.001)
        self.experiment_started = True
        self.wait_signal.set()

    def get_frame(self):
        try:
            self.current_frame = self.camera_queue.get(timeout=0.001)
        except Empty:
            pass

    def send_receive(self):
        try:
            self.n_planes = self.n_planes_queue.get(timeout=0.001)
            self.first_volume = True
        except Empty:
            pass
        try:
            self.calibration_ref = self.calibration_ref_queue.get(timeout=0.001)
        except Empty:
            pass
