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
    EXTERNAL_TRIGGER = 1
    INTERNAL_TRIGGER = 2


@dataclass
class HamamatsuCameraParams:
    exposure_time: float = 60
    subarray_hsize: int = 2048
    subarray_vsize: int = 2048
    subarray_hpos: int = 0
    subarray_vpos: int = 0
    binning: int = 2
    image_height: int = 2048
    image_width: int = 2048
    frame_shape: tuple = (2048, 2048)
    internal_frame_rate: float = None


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
    def __init__(self, camera_id=0, max_queue_size=1000):
        super().__init__()
        self.stop_event = Event()
        self.external_trigger_mode_event = Event()
        self.internal_trigger_mode_event = Event()
        self.image_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.parameter_queue = Queue()
        self.reverse_parameter_queue = Queue()
        self.camera_id = camera_id
        self.camera = None
        self.parameters = CamParameters

        self.initialize_camera()

    def update_settings(self):
        new_params: CamParameters

        new_params = get_last_parameters(self.parameter_queue)
        if new_params is not None:

            if self.parameters.image_params.binning != new_params.image_params.binning:
                self.stop_event.set()
                self.stop_event.clear()

            if self.parameters.image_params.exposure_time != new_params.image_params.exposure_time:
                self.stop_event.set()
                self.stop_event.clear()

            if (self.parameters.image_params.subarray_vsize != new_params.image_params.subarray_vsize) or\
                    (self.parameters.image_params.subarray_hsize != new_params.image_params.subarray_hsize) or\
                    (self.parameters.image_params.subarray_vpos != new_params.image_params.subarray_vpos) or\
                    (self.parameters.image_params.subarray_hpos != new_params.image_params.subarray_hpos):

                self.stop_event.set()

                # this is because SDK functions in C# for these variables go on steps of 4

                new_params.image_params.subarray_vsize =\
                    new_params.image_params.subarray_vsize -(new_params.image_params.subarray_vsize % 4)
                new_params.image_params.subarray_hsize = \
                    new_params.image_params.subarray_hsize - (new_params.image_params.subarray_hsize % 4)
                new_params.image_params.subarray_vpos = \
                    new_params.image_params.subarray_vpos - (new_params.image_params.subarray_vpos % 4)
                new_params.image_params.subarray_hpos = \
                    new_params.image_params.subarray_hpos - (new_params.image_params.subarray_hpos % 4)

                self.stop_event.clear()

            if self.external_trigger_mode_event.is_set():
                self.stop_event.set()
                self.stop_event.clear()

            self.parameters = new_params
            self.run()

    def initialize_camera(self):
        self.camera = HamamatsuCameraMR(camera_id=self.camera_id)

    def Hamamatsu_send_receive_properties(self):
        self.camera.setPropertyValue('binning', self.parameters.image_params.binning)
        self.camera.setPropertyValue('exposure_time', 0.001 * self.parameters.image_params.exposure_time)
        self.camera.setPropertyValue('subarray_vpos', self.parameters.image_params.subarray_vpos)
        self.camera.setPropertyValue('subarray_hpos', self.parameters.image_params.subarray_hpos)
        self.camera.setPropertyValue('subarray_vsize', self.parameters.image_params.subarray_vsize)
        self.camera.setPropertyValue('subarray_hsize', self.parameters.image_params.subarray_hsize)

        self.parameters.image_params.internal_frame_rate = self.camera.getPropertyValue("internal_frame_rate")[0]
        self.parameters.image_params.frame_shape = (
            int(self.camera.getPropertyValue("subarray_hsize")[0] / self.camera.getPropertyValue("binning")[0]),
            int(self.camera.getPropertyValue("subarray_vsize")[0] / self.camera.getPropertyValue("binning")[0])
        )

        self.reverse_parameter_queue.put(self.parameters)

    def set_Hamamatsu_running_mode(self):
        self.camera.setACQMode("run_till_abort")
        self.camera.setSubArrayMode()

    def run(self):
        self.set_Hamamatsu_running_mode()
        self.Hamamatsu_send_receive_properties()

        if self.external_trigger_mode_event.is_set():
            self.parameters.run_mode = CameraProcessState.EXTERNAL_TRIGGER
            self.external_trigger_mode_event.clear()

        if self.internal_trigger_mode_event.is_set():
            self.parameters.run_mode = CameraProcessState.INTERNAL_TRIGGER
            self.internal_trigger_mode_event.clear()

        if self.parameters.run_mode == CameraProcessState.FREE:
            self.camera.setPropertyValue("trigger_source", 1)
            self.camera.startAcquisition()
            while not self.stop_event.is_set():
                self.update_settings()
                frames = self.camera.getFrames()
                if frames is not None:
                    for frame in frames:
                        frame = np.reshape(frame.getData(), self.parameters.image_params.frame_shape)
                        self.image_queue.put(frame)
            self.camera.stopAcquisition()

        if self.parameters.run_mode == CameraProcessState.EXTERNAL_TRIGGER:
            self.camera.setPropertyValue("trigger_source", 2)
            while not self.stop_event.is_set():
                self.camera.startAcquisition()
                while not self.stop_event.is_set():
                    self.update_settings()
                    frames = self.camera.getFrames()
                    if frames is not None:
                        for frame in frames:
                            frame = np.reshape(frame.getData(), self.parameters.image_params.frame_shape)
                            self.image_queue.put(frame)
                self.camera.stopAcquisition()

        # FIXME: Internal trigger for plane mode or synchronize, somehow, with Stytra
        if self.parameters.run_mode == CameraProcessState.INTERNAL_TRIGGER:
            self.camera.setPropertyValue("trigger_source", 1)
            while not self.stop_event.is_set():
                self.camera.startAcquisition()
                while not self.stop_event.is_set():
                    self.update_settings()
                    frames = self.camera.getFrames()
                    if frames is not None:
                        for frame in frames:
                            frame = np.reshape(frame.getData(), self.parameters.image_params.frame_shape)
                            self.image_queue.put(frame)
                self.camera.stopAcquisition()

    def close_camera(self):
        self.camera.shutdown()
