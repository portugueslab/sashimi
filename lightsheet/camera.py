from multiprocessing import Process, Queue, Event
from enum import Enum
from threading import Thread
from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.hardware.hamamatsu_camera import *
from dataclasses import dataclass, fields
import time
import numpy as np


class CameraProcessState(Enum):
    FREE = 0
    TRIGGERED = 1


@dataclass
class CameraParams:
    exposure_time: float = 0.06
    subarray_hsize: int = 2048
    subarray_vsize: int = 2048
    subarray_hpos: int = 0
    subarray_vpos: int = 0
    # TODO: Restrict binning to possible values: 1x1 (1), 2x2 (2) or 4x4 (4)
    binning: dict = 1


@dataclass
class ScanParameters:
    run_mode: CameraProcessState = CameraProcessState.FREE
    image_params: CameraParams = CameraParams()


class CameraProcess(Thread):
    def __init__(self, camera_id=0, max_queue_size=500):
        super().__init__()
        self.stop_event = Event()
        self.image_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.camera_id = camera_id
        self.camera = None
        self.info = None
        self.parameters = ScanParameters

    def set_params(self):
        # FIXME: Access subclass
        for param in fields(self.parameters.image_params):
            self.camera.setPropertyValue(param.name, param.value)

    # TODO: Get param info
    def get_param_value(self):
        # FIXME: Access subclass
        for param in fields(self.parameters.image_params):
            newparams = self.camera.getPropertyValue(param.name)[0]

    def initialize_camera(self):
        self.camera = HamamatsuCameraMR(camera_id=self.camera_id)
        self.info = self.camera.getModelInfo(self.camera_id)
        # TODO: figure out what is this
        self.camera.setPropertyValue("defect_correct_mode", 1)

    # TODO: Figure out how to trigger each camera frame
    def run(self):
        self.initialize_camera()
        self.camera.setACQMode("run_till_abort")
        self.camera.setPropertyValue('binning', 2)
        self.camera.setPropertyValue('subarray_hsize', 2000)
        self.camera.setPropertyValue('subarray_vsize', 2000)
        self.camera.setPropertyValue('exposure_time', 0.5)
        print('internal_frame_rate: ', self.camera.getPropertyValue('internal_frame_rate')[0])
        self.camera.startAcquisition()
        if self.parameters.run_mode == CameraProcessState.FREE:
            while not self.stop_event.is_set():
                frames = self.camera.getFrames()
                for frame in frames:
                    frame = np.reshape(frame.getData(), (1000, 1000))
                    self.image_queue.put(frame)
            self.camera.stopAcquisition()
        if self.parameters.run_mode == CameraProcessState.TRIGGERED:
            # FIXME: Set trigger
            while not self.stop_event.is_set():
                frames = self.camera.getFrames()
                self.image_queue.put(frames)

    def close_camera(self):
        self.camera.shutdown()
