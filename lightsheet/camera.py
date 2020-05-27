from multiprocessing import Process, Queue, Event
from enum import Enum
from threading import Thread
from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.hardware.hamamatsu_camera import *
from dataclasses import dataclass, fields
import time
import numpy as np
from queue import Empty

class CameraProcessState(Enum):
    FREE = 0
    TRIGGERED = 1


@dataclass
class HamamatsuCameraParams:
    # min 0.002 max... 1?
    exposure_time: float = 0.060
    # max 2048
    subarray_hsize: int = 2000
    subarray_vsize: int = 2000
    subarray_hpos: int = 0
    subarray_vpos: int = 0
    binning: int = 2
    # image_height: int = 2048
    # image_width: int = 2048


@dataclass
class CamParameters:
    run_mode: CameraProcessState = CameraProcessState.FREE
    image_params: HamamatsuCameraParams = HamamatsuCameraParams()


def get_last_parameters(parameter_queue, timeout=0.001):
    params = None
    while True:
        try:
            params = parameter_queue.get(timeout=timeout)
        except Empty:
            break
    return params


class CameraProcess(Thread):
    def __init__(self, camera_id=0, max_queue_size=500):
        super().__init__()
        self.stop_event = Event()
        self.image_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.parameter_queue = Queue()
        self.camera_id = camera_id
        self.camera = None
        self.info = None
        self.parameters = CamParameters

    def set_params(self):
        # FIXME: Access subclass
        for param in fields(self.parameters.image_params):
            self.camera.setPropertyValue(param.name, param.value)

    # TODO: Get param info
    def get_param_value(self):
        # FIXME: Access subclass
        for param in fields(self.parameters.image_params):
            newparams = self.camera.getPropertyValue(param.name)[0]

    def update_settings(self):
        new_params = get_last_parameters(self.parameter_queue)
        if new_params is not None:
            self.parameters = new_params


    def initialize_camera(self):
        self.camera = HamamatsuCameraMR(camera_id=self.camera_id)
        self.info = self.camera.getModelInfo(self.camera_id)
        # TODO: figure out what is this
        self.camera.setPropertyValue("defect_correct_mode", 1)

    # TODO: Figure out how to trigger each camera frame
    def run(self):
        self.initialize_camera()
        self.camera.setACQMode("run_till_abort")
        self.camera.setPropertyValue('binning', self.parameters.image_params.binning)
        self.camera.setSubArrayMode()
        self.camera.setPropertyValue('subarray_hsize', self.parameters.image_params.subarray_hsize)
        self.camera.setPropertyValue('subarray_vsize', self.parameters.image_params.subarray_vsize)
        self.camera.setPropertyValue('exposure_time', self.parameters.image_params.exposure_time)
        print('internal_frame_rate: ', self.camera.getPropertyValue('internal_frame_rate')[0])
        self.camera.startAcquisition()
        self.subarray_size = (int(self.camera.getPropertyValue("subarray_hsize")[0] / self.camera.getPropertyValue("binning")[0]),
                              int(self.camera.getPropertyValue("subarray_vsize")[0] / self.camera.getPropertyValue("binning")[0]))
        if self.parameters.run_mode == CameraProcessState.FREE:
            while not self.stop_event.is_set():
               # new_params = get_last_parameters(self.parameter_queue)
                #if new_params is not None:
                 #   self.parameters = new_params
                frames = self.camera.getFrames()
                for frame in frames:
                    frame = np.reshape(frame.getData(), self.subarray_size)
                    self.image_queue.put(frame)
            self.camera.stopAcquisition()
        if self.parameters.run_mode == CameraProcessState.TRIGGERED:
            # FIXME: Set trigger
            while not self.stop_event.is_set():
                pass

    def close_camera(self):
        self.camera.shutdown()


# TODO: Get rid of this once camera works properly

class FakeCameraProcess(Thread):
    '''
    This class is for debugging (e.g. when camera is not connected to computer)
    '''
    def __init__(self, camera_id=0, max_queue_size=500):
        super().__init__()
        self.stop_event = Event()
        self.image_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.camera_id = camera_id
        self.camera = None
        self.info = None
        self.parameters = ScanParameters

    def initialize_camera(self):
        pass

    def run(self):
        self.initialize_camera()
        if self.parameters.run_mode == CameraProcessState.FREE:
            while not self.stop_event.is_set():
                time.sleep(0.1)
                frame = np.random.random(size=(500, 500))
                self.image_queue.put(frame)
