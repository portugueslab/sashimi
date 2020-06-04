from multiprocessing import Process, Queue, Event
from enum import Enum
from arrayqueues.shared_arrays import ArrayQueue
from lightsheet.hardware.hamamatsu_camera import HamamatsuCameraMR, DCamAPI
from dataclasses import dataclass, fields
from time import sleep
import numpy as np
from copy import copy
from queue import Empty
from math import ceil


class CameraMode(Enum):
    PREVIEW = 1
    EXPERIMENT_RUNNING = 2
    PAUSED = 3


class TriggerMode(Enum):
    FREE = 1
    EXTERNAL_TRIGGER = 2


@dataclass
class CamParameters:
    exposure_time: float = 60
    binning: int = 2
    subarray: tuple = (0, 0, 2048, 2048)  # order of params here is [hpos, vpos, hsize, vsize,]
    image_height: int = 2048
    image_width: int = 2048
    frame_shape: tuple = (2048, 2048)
    internal_frame_rate: float = None
    triggered_frame_rate: int = 60
    trigger_mode: TriggerMode = TriggerMode.FREE
    camera_mode: CameraMode = CameraMode.PREVIEW
    n_frames_duration: int = 0


class CameraProcess(Process):
    def __init__(self, experiment_start_event, stop_event, camera_id=0, max_queue_size=500):
        super().__init__()
        self.experiment_start_event = experiment_start_event
        self.stop_event = stop_event
        self.image_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.parameter_queue = Queue()
        self.reverse_parameter_queue = Queue()
        self.duration_queue = Queue()
        self.camera_id = camera_id
        self.camera = None
        self.parameters = CamParameters()
        self.new_parameters = copy(self.parameters)
        self.frame_duration = None

    def initialize_camera(self):
        self.camera.setACQMode("run_till_abort")
        self.camera.setSubArrayMode()

        self.dcam_api = DCamAPI()
        self.camera = HamamatsuCameraMR(self.dcam_api, camera_id=self.camera_id)

    def pause_loop(self):
        while not self.stop_event.is_set():
            try:
                self.new_parameters = self.parameter_queue.get(timeout=0.001)
                if self.new_parameters != self.parameters and (
                        self.parameters.camera_mode != CameraMode.EXPERIMENT_RUNNING or
                        self.new_parameters.camera_mode == CameraMode.PREVIEW
                ):
                    self.camera.stopAcquisition()
                    break
            except Empty:
                pass

    def check_start_signal(self):
        '''
        It only runs when the experiment is in prepared state awaiting for experiment trigger signal
        '''
        if self.parameters.camera_mode == CameraMode.EXPERIMENT_RUNNING:
            while not self.experiment_start_event.is_set():
                sleep(0.00001)

    def calculate_duration(self):
        try:
            duration = self.duration_queue.get(timeout=0.0001)
            self.parameters.n_frames_duration = (
                    int(ceil(duration * self.parameters.triggered_frame_rate)) + 1
            )
        except Empty:
            pass

    def run(self):
        self.initialize_camera()
        self.run_camera()

    def run_camera(self):
        while not self.stop_event.is_set():
            self.parameters = self.new_parameters
            self.update_reverse_parameter_queue()
            self.calculate_duration()
            self.apply_parameters()
            if self.parameters.camera_mode == CameraMode.PAUSED:
                self.pause_loop()
            else:
                self.camera.startAcquisition()
                self.camera_loop()

    def camera_loop(self):
        i_acquired = 0
        while not self.stop_event.is_set():
            if i_acquired == 0:
                self.check_start_signal()
                # FIXME: Clean the camera buffer before start of experiment! Or only get the last frame/drop frames?
            frames = self.camera.getFrames()
            if frames:
                for frame in frames:
                    self.image_queue.put(np.reshape(frame.getData(), self.parameters.frame_shape))
                    i_acquired += 1
            try:
                self.new_parameters = self.parameter_queue.get(timeout=0.001)
                if self.new_parameters != self.parameters and (
                        self.parameters.camera_mode != CameraMode.EXPERIMENT_RUNNING or
                        self.new_parameters.camera_mode == CameraMode.PREVIEW
                ):
                    self.camera.stopAcquisition()
                    break
            except Empty:
                pass

            self.calculate_duration()

    def apply_parameters(self):
        subarray = self.parameters.subarray
        # quantizing the ROI dims in multiples of 4
        subarray = [(i // 4) * 4 for i in subarray]
        # this can be simplified by making the API nice
        self.camera.setPropertyValue('binning', self.parameters.binning)
        self.camera.setPropertyValue('exposure_time', 0.001 * self.parameters.exposure_time)
        self.camera.setPropertyValue('subarray_vpos', subarray[0])
        self.camera.setPropertyValue('subarray_hpos', subarray[1])
        self.camera.setPropertyValue('subarray_vsize', subarray[2])
        self.camera.setPropertyValue('subarray_hsize', subarray[3])
        self.camera.setPropertyValue('trigger_source', self.parameters.trigger_mode.value)

        # This is not sent to the camera but has to be updated with camera info directly (because of multiples of 4)
        self.parameters.frame_shape = (
            self.camera.getPropertyValue('subarray_hsize') // self.parameters.binning,
            self.camera.getPropertyValue('subarray_vsize') // self.parameters.binning
        )

    def update_reverse_parameter_queue(self):
        self.parameters.internal_frame_rate = self.camera.getPropertyValue("internal_frame_rate")[0]
        self.reverse_parameter_queue.put(self.parameters)

    def close_camera(self):
        self.camera.shutdown()
