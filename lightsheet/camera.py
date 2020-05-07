from multiprocessing import Process, Queue, Event
from enum import Enum

from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.hardware.hamamatsu_camera import HamamatsuCamera


class CameraProcessState(Enum):
    FREE = 0
    TRIGGERED = 1


class CameraProcess(Process):
    def __init__(self, stop_event: Event, max_mbytes_queue=500):
        super().__init__()
        self.stop_event = stop_event
        self.image_queue = ArrayQueue(max_mbytes=max_mbytes_queue)
        self.camera = None

    def initialize_camera(self):
        self.camera = HamamatsuCamera()

    def run(self):
        self.initialize_camera()
        while not self.stop_event.is_set():
            pass

    def close_camera(self):
        pass