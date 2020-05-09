from multiprocessing import Process, Queue, Event
from enum import Enum

from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.hardware.hamamatsu_camera import HamamatsuCameraMR


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
        self.camera = HamamatsuCameraMR(camera_id=0)

    def run(self):
        self.initialize_camera()
        self.camera.setACQMode("run_till_abort")
        while not self.stop_event.is_set():
            pass

    def stop(self):
        self.camera.stopAcquisition()


    def close_camera(self):
        self.camera.shutdown()