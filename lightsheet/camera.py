from multiprocessing import Process, Queue
from enum import Enum
from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.hardware.hamamatsu_camera import HamamatsuCameraMR, DCamAPI
from dataclasses import dataclass
from time import sleep
import numpy as np
from copy import copy
from queue import Empty
import time


class CameraMode(Enum):
    PREVIEW = 1
    TRIGGERED = 2
    EXPERIMENT_RUNNING = 3
    PAUSED = 3
    ABORT = 4


class TriggerMode(Enum):
    FREE = 1
    EXTERNAL_TRIGGER = 2


@dataclass
class CamParameters:
    exposure_time: float = 60
    binning: int = 2
    subarray: tuple = (0, 0, 1024, 1024)  # order of params here is [hpos, vpos, hsize, vsize,]
    image_height: int = 2048
    image_width: int = 2048
    frame_shape: tuple = (1024, 1024)
    internal_frame_rate: float = 60
    trigger_mode: TriggerMode = TriggerMode.FREE
    camera_mode: CameraMode = CameraMode.PAUSED


class CameraProcess(Process):
    def __init__(self, experiment_start_event, stop_event, camera_id=0, max_queue_size=1200):
        super().__init__()
        self.experiment_start_event = experiment_start_event
        self.stop_event = stop_event
        self.image_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.parameter_queue = Queue()
        self.camera_id = camera_id
        self.camera = None
        self.parameters = CamParameters()
        self.new_parameters = copy(self.parameters)
        self.camera_status_queue = Queue()
        self.triggered_frame_rate_queue = Queue()

    def cast_parameters(self):
        params = self.parameters
        params.subarray = list(params.subarray)
        return params

    # TODO: Move last two rows to API
    def initialize_camera(self):
        self.camera_status_queue.put(self.cast_parameters())
        self.dcam_api = DCamAPI()
        self.camera = HamamatsuCameraMR(self.dcam_api.dcam, camera_id=self.camera_id)

        self.camera.setACQMode("run_till_abort")
        self.camera.setSubArrayMode()

    def pause_loop(self):
        while not self.stop_event.is_set():
            try:
                self.new_parameters = self.parameter_queue.get(timeout=0.001)
                if self.new_parameters != self.parameters:
                    break
            except Empty:
                pass

    def run(self):
        self.initialize_camera()
        self.run_camera()
        self.camera.shutdown()

    def run_camera(self):
        while not self.stop_event.is_set():
            self.parameters = self.new_parameters
            self.apply_parameters()
            self.camera_status_queue.put(self.cast_parameters())
            if self.parameters.camera_mode == CameraMode.PAUSED:
                self.pause_loop()
            else:
                self.camera.startAcquisition()
                self.camera_loop()

    def camera_loop(self):
        i_acquired = 0
        cumulative_time = 0
        while not self.stop_event.is_set():
            start_time = time.perf_counter()  # TODO switch to time ns, and have a little update_framerate function
            frames = self.camera.getFrames()
            if frames:
                for frame in frames:
                    elapsed = time.perf_counter() - start_time
                    self.image_queue.put(np.reshape(frame.getData(), self.parameters.frame_shape))
                    i_acquired += 1
                    cumulative_time += elapsed
                    if cumulative_time >= 1:
                        triggered_frame_rate = i_acquired/cumulative_time
                        self.triggered_frame_rate_queue.put(triggered_frame_rate)
                        cumulative_time = 0
                        i_acquired = 0
            try:
                self.new_parameters = self.parameter_queue.get(timeout=0.001)
                if self.parameters.camera_mode == CameraMode.ABORT or \
                        (self.new_parameters != self.parameters):
                    self.camera.stopAcquisition()
                    break
            except Empty:
                pass

    # TODO: Move this to API
    def apply_parameters(self):
        subarray = self.parameters.subarray
        # quantizing the ROI dims in multiples of 4
        subarray = [min((i * self.parameters.binning // 4) * 4, 2048) for i in subarray]
        # this can be simplified by making the API nice
        self.camera.setPropertyValue('binning', self.parameters.binning)
        self.camera.setPropertyValue('exposure_time', 0.001 * self.parameters.exposure_time)
        self.camera.setPropertyValue('subarray_vpos', subarray[1])
        self.camera.setPropertyValue('subarray_hpos', subarray[0])
        self.camera.setPropertyValue('subarray_vsize', subarray[3])
        self.camera.setPropertyValue('subarray_hsize', subarray[2])
        self.camera.setPropertyValue('trigger_source', self.parameters.trigger_mode.value)

        # This is not sent to the camera but has to be updated with camera info directly (because of multiples of 4)
        self.parameters.frame_shape = (
            self.camera.getPropertyValue('subarray_vsize')[0] // self.parameters.binning,
            self.camera.getPropertyValue('subarray_hsize')[0] // self.parameters.binning
        )

        self.parameters.internal_frame_rate = self.camera.getPropertyValue("internal_frame_rate")[0]

    def close_camera(self):
        self.camera.shutdown()
