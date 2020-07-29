from multiprocessing import Process, Queue, Event
from queue import Empty
from arrayqueues.shared_arrays import ArrayQueue
from sashimi.utilities import neg_dif
import numpy as np


class VolumeDispatcher(Process):
    def __init__(
        self,
        stop_event: Event,
        saving_signal: Event,
        wait_signal: Event,
        camera_queue: ArrayQueue,
        saver_queue: ArrayQueue,
        max_queue_size=1200,
    ):
        super().__init__()
        self.stop_event = stop_event
        self.saving_signal = saving_signal
        self.wait_signal = wait_signal
        self.noise_subtraction_active = Event()

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

    def run(self):
        while not self.stop_event.is_set():
            self.send_receive()
            self.get_frame()

    def process_frame(self):
        if self.current_frame is not None:
            if (
                self.calibration_ref is not None
                and self.noise_subtraction_active.is_set()
            ):
                self.current_frame = neg_dif(
                    self.current_frame, self.calibration_ref
                )
            if (
                self.first_volume
                or self.volume_buffer.shape[1:3] != self.current_frame.shape
            ):
                self.volume_buffer = np.empty(
                    (self.n_planes, *self.current_frame.shape), dtype=np.uint16
                )
                self.first_volume = False
            self.volume_buffer[self.i_plane, :, :] = self.current_frame
            self.i_plane += 1
            if self.i_plane == self.n_planes:
                self.fill_queues()
                self.i_plane = 0

    def fill_queues(self):
        if self.viewer_queue.queue.qsize() < 3:
            self.viewer_queue.put(self.volume_buffer)
        else:
            pass  # volume has been dropped from the viewer
        if self.saving_signal.is_set():
            self.saver_queue.put(self.volume_buffer)

    def get_frame(self):
        if self.wait_signal.is_set():
            self.saver_queue.clear()
            while self.wait_signal.is_set():
                try:
                    _ = self.camera_queue.get(timeout=0.001)
                except Empty:
                    pass
            self.i_plane = 0
        try:
            self.current_frame = self.camera_queue.get(timeout=0.001)
            self.process_frame()
        except Empty:
            pass

    def send_receive(self):
        try:
            self.n_planes = self.n_planes_queue.get(timeout=0.001)
            self.reset()
        except Empty:
            pass
        try:
            self.calibration_ref = self.calibration_ref_queue.get(
                timeout=0.001
            )
        except Empty:
            pass

    def reset(self):
        self.first_volume = True
        self.i_plane = 0
