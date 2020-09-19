from multiprocessing import Process, Queue
from enum import Enum
from arrayqueues.shared_arrays import ArrayQueue
from dataclasses import dataclass
import numpy as np
from copy import copy
from queue import Empty
import time
from datetime import datetime
from sashimi.hardware import camera_class_dict
from sashimi.config import read_config

conf = read_config()


class CameraMode(Enum):
    PREVIEW = 1
    TRIGGERED = 2
    EXPERIMENT_RUNNING = 3
    PAUSED = 4
    ABORT = 5


class TriggerMode(Enum):
    FREE = 1
    EXTERNAL_TRIGGER = 2


@dataclass
class CamParameters:
    exposure_time: float = 60
    binning: int = 2
    roi: tuple = (
        0,
        0,
        1024,
        1024,
    )  # order of params here is [hpos, vpos, hsize, vsize,]
    image_height: int = 2048
    image_width: int = 2048
    frame_shape: tuple = (1024, 1024)
    internal_frame_rate: float = 60
    trigger_mode: TriggerMode = TriggerMode.FREE
    camera_mode: CameraMode = CameraMode.PAUSED


class FramerateRecorder:
    def __init__(self, n_fps_frames=10):
        # Set framerate calculation parameters
        self.n_fps_frames = n_fps_frames
        self.i_fps = 0
        self.previous_time_fps = None
        self.current_framerate = None

        # Store current time timestamp:
        self.current_time = datetime.now()
        self.starting_time = datetime.now()

    def update_framerate(self):
        """Calculate the framerate every n_fps_frames frames."""
        # If number of frames for updating is reached:
        if self.i_fps == self.n_fps_frames - 1:
            self.current_time = datetime.now()
            if self.previous_time_fps is not None:
                try:
                    self.current_framerate = (
                        self.n_fps_frames
                        / (self.current_time - self.previous_time_fps).total_seconds()
                    )
                except ZeroDivisionError:
                    self.current_framerate = 0

            self.previous_time_fps = self.current_time
        # Reset i after every n frames
        self.i_fps = (self.i_fps + 1) % self.n_fps_frames


class CameraProcess(Process):
    def __init__(
        self,
        experiment_start_event,
        stop_event,
        camera_id=0,
        max_queue_size=1200,
        n_fps_frames=20,
    ):
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
        self.framerate_rec = FramerateRecorder(n_fps_frames=n_fps_frames)

    def cast_parameters(self):
        params = self.parameters
        params.roi = list(params.roi)
        return params

    def initialize_camera(self):
        self.camera_status_queue.put(self.cast_parameters())
        if conf["scopeless"]:
            self.camera = camera_class_dict["test"]()
        else:
            self.camera = camera_class_dict[conf["camera"]["name"]]()

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
            self.update_parameters()
            self.camera_status_queue.put(self.cast_parameters())
            if self.parameters.camera_mode == CameraMode.PAUSED:
                self.pause_loop()
            else:
                self.camera.start_acquisition()
                self.camera_loop()

    def camera_loop(self):
        while not self.stop_event.is_set():
            frames = self.camera.get_frames()
            if frames:
                for frame in frames:
                    self.image_queue.put(frame)
                    self.update_framerate()
            try:
                self.new_parameters = self.parameter_queue.get(timeout=0.001)
                if self.parameters.camera_mode == CameraMode.ABORT or (
                    self.new_parameters != self.parameters
                ):
                    self.camera.stop_acquisition()
                    break
            except Empty:
                pass

    def update_parameters(self):
        self.parameters = self.new_parameters
        for attribute in ["exposure_time", "binning", "roi", "trigger_mode"]:
            setattr(self.camera, attribute, getattr(self.parameters, attribute))
        # the following is to match internals of the camera as some cameras are restricted (e.g. only multiples of 4)
        self.parameters.frame_shape = self.camera.frame_shape

    def update_framerate(self):
        self.framerate_rec.update_framerate()
        if self.framerate_rec.i_fps == 0:
            self.triggered_frame_rate_queue.put(self.framerate_rec.current_framerate)

    def close_camera(self):
        self.camera.shutdown()
