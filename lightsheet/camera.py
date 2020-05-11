from multiprocessing import Process, Queue, Event
from enum import Enum

from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.hardware.hamamatsu_camera import HamamatsuCameraMR
from dataclasses import dataclass


class CameraProcessState(Enum):
    FREE = 0
    TRIGGERED = 1


@dataclass
class ScanParameters:
    run_mode: CameraProcessState = CameraProcessState.FREE


class CameraProcess(Process):
    def __init__(self, stop_event: Event, initial_parameters: ScanParameters, max_mbytes_queue=500, camera_id=0):
        super().__init__()
        self.stop_event = stop_event
        self.image_queue = ArrayQueue(max_mbytes=max_mbytes_queue)
        self.camera_id = camera_id
        self.camera = None
        self.info = None
        self.parameters = initial_parameters

    def initialize_camera(self):
        self.camera = HamamatsuCameraMR(camera_id=self.camera_id)
        self.info = self.camera.getModelInfo(self.camera_id)

    def run(self):
        self.initialize_camera()
        self.camera.setACQMode("run_till_abort")
        self.camera.startAcquisition()
        while not self.stop_event.is_set():
            frames = self.camera.getFrames()
            self.image_queue.put(frames)
        self.camera.stopAcquisition()

    def close_camera(self):
        self.camera.shutdown()
