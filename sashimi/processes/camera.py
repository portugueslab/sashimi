from multiprocessing import Queue
from enum import Enum
from dataclasses import dataclass
from queue import Empty
from datetime import datetime
from arrayqueues.shared_arrays import ArrayQueue

from sashimi.processes.logging import LoggingProcess
from sashimi.events import LoggedEvent
from sashimi.hardware.cameras import camera_class_dict
from sashimi.config import read_config
from sashimi.utilities import get_last_parameters

conf = read_config()

FULL_SIZE = [
    r / conf["camera"]["default_binning"]
    for r in conf["camera"]["max_sensor_resolution"]
]


class CameraMode(Enum):
    PREVIEW = 1
    #TRIGGERED = 2
    #EXPERIMENT_RUNNING = 3
    PAUSED = 4
    ABORT = 5


class TriggerMode(Enum):
    FREE = 1
    EXTERNAL_TRIGGER = 2


@dataclass
class CamParameters:
    exposure_time: float = conf["camera"]["default_exposure"]
    binning: int = 2
    roi: tuple = (
        0,
        0,
        FULL_SIZE[0],
        FULL_SIZE[1],
    )  # order is [hpos, vpos, hsize, vsize]
    image_height: int = FULL_SIZE[0]
    image_width: int = FULL_SIZE[1]
    frame_shape: tuple = (FULL_SIZE[0], FULL_SIZE[1])
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

    def restart(self):
        self.current_framerate = None


class CameraProcess(LoggingProcess):
    """Process that handles the setting of new parameters to and the acquisition of
    frames from the camera.

    Parameters
    ----------
    stop_event
    wait_event
    exp_trigger_event
    camera_id
    max_queue_size
    n_fps_frames
    """

    def __init__(
        self,
        stop_event: LoggedEvent,
        wait_event: LoggedEvent,
        exp_trigger_event: LoggedEvent,
        camera_id=0,
        max_queue_size=1200,
        n_fps_frames=20,
    ):
        super().__init__(name="camera")
        # Queue to communicate
        self.triggered_frame_rate_queue = Queue()
        self.parameter_queue = Queue()

        self.stop_event = stop_event.new_reference(self.logger)
        self.wait_event = wait_event.new_reference(self.logger)
        self.experiment_trigger_event = exp_trigger_event.new_reference(self.logger)
        self.image_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.camera_id = camera_id
        self.camera = None
        self.parameters = CamParameters()
        self.framerate_rec = FramerateRecorder(n_fps_frames=n_fps_frames)
        self.was_waiting = False

    def initialize_camera(self):
        if conf["scopeless"]:
            self.camera = camera_class_dict["mock"]()
        else:
            self.camera = camera_class_dict[conf["camera"]["name"]](
                camera_id=conf["camera"]["id"],
                max_sensor_resolution=tuple(conf["camera"]["max_sensor_resolution"]),
            )

    def run(self):
        self.logger.log_message("started")
        self.initialize_camera()
        self.run_camera()
        self.camera.shutdown()
        self.logger.close()

    def run_camera(self):
        """Main run for the camera. Depending on whether the camera mode is PAUSED or not,
        either the self.pause_loop or self.camera_loop are executed.
        """
        while not self.stop_event.is_set():
            print ('camera mode', self.parameters.camera_mode)
            if self.parameters.camera_mode == CameraMode.PAUSED:
                print ("paused camera mode")
                self.pause_loop()
                print ('ran pauseed looop')
            else:
                print ('im here now')
                self.camera.start_acquisition()
                self.logger.log_message("Started acquisition")
                self.camera_loop()

    def pause_loop(self):
        """Camera idle loop, just wait until parameters are updated. Check them, and if
        CameraMode.PAUSED is still set, return here.
        """
        while not self.stop_event.is_set():
            try:
                new_parameters = self.parameter_queue.get(timeout=0.001)
                if new_parameters != self.parameters:
                    self.update_parameters(new_parameters, stop_start=False)
                    if self.parameters.camera_mode != CameraMode.PAUSED:
                        print ('pause loop broken', self.parameters.camera_mode, new_parameters.camera_mode)
                        break
            except Empty:
                pass

    def camera_loop(self):
        """Camera running loop, grab frames and set new parameters if available."""
        while not self.stop_event.is_set():
            is_waiting = self.wait_event.is_set()
            frames = self.camera.get_frames()

            # if no frames are received (either this loop is in between frames
            # or we are in the waining period)
            if frames:

                for frame in frames:
                    self.logger.log_message(
                        "received frame of shape " + str(frame.shape)
                    )
                    # this means this is the first frame received since
                    # the waiting period is over, the signal has to be sent that
                    # saving can start
                    if self.was_waiting and not is_waiting:
                        self.experiment_trigger_event.set()
                        # TODO do not crash here if queue is full
                    self.image_queue.put(frame)
                    self.was_waiting = is_waiting
                    self.update_framerate()

            # Empty parameters queue and set new parameters with the most recent value
            new_parameters = get_last_parameters(self.parameter_queue, timeout=0.001)

            if new_parameters is not None:
                if new_parameters.camera_mode == CameraMode.ABORT or (
                    new_parameters != self.parameters
                ):
                    self.update_parameters(new_parameters)

    def update_parameters(self, new_parameters, stop_start=True):
        """ "Set new parameters and stop and start the camera to make sure all changes take place."""
        self.parameters = new_parameters

        if stop_start:
            self.camera.stop_acquisition()

        # In general, ROI and binning are a bit funny in their interactions, and need to be handled
        # carefully in the specific camera interfaces.
        for attribute in ["binning", "roi", "exposure_time", "trigger_mode"]:
            setattr(self.camera, attribute, getattr(self.parameters, attribute))

        if stop_start:
            self.camera.start_acquisition()
        self.framerate_rec.restart()
        self.logger.log_message("Updated parameters " + str(self.parameters))

    def update_framerate(self):
        self.framerate_rec.update_framerate()
        if self.framerate_rec.i_fps == 0:
            self.triggered_frame_rate_queue.put(self.framerate_rec.current_framerate)

    def close_camera(self):
        self.camera.shutdown()
