from multiprocessing import Queue, Event
from queue import Empty
from arrayqueues.shared_arrays import ArrayQueue
from sashimi.utilities import neg_dif
from sashimi.processes.logging import LoggingProcess
from sashimi.events import LoggedEvent
import numpy as np

from sashimi.utilities import get_last_parameters

TIMEOUT_S = 0.001


class VolumeDispatcher(LoggingProcess):
    """

    Parameters
    ----------
    stop_event
    saving_signal
    wait_signal
    noise_subtraction_on
    camera_queue
    saver_queue
    max_queue_size

    """

    def __init__(
        self,
        stop_event: LoggedEvent,
        saving_signal: LoggedEvent,
        wait_signal: LoggedEvent,
        noise_subtraction_on: Event,
        camera_queue: ArrayQueue,
        saver_queue: ArrayQueue,
        max_queue_size=1200,
    ):
        super().__init__(name="dispatcher")
        self.stop_event = stop_event
        self.saving_signal = saving_signal.new_reference(self.logger)
        self.wait_signal = wait_signal.new_reference(self.logger)
        self.noise_subtraction_active = noise_subtraction_on.new_reference(self.logger)

        self.camera_queue = camera_queue
        self.saver_queue = saver_queue
        self.n_planes_queue = Queue()
        self.viewer_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.calibration_ref_queue = ArrayQueue()

        self.volume_buffer = None
        self.calibration_ref = None

        self.n_planes = 1
        self.i_plane = 0
        self.first_volume = True

    def run(self):
        self.logger.log_message("started")
        while not self.stop_event.is_set():
            self.receive_options()
            self.get_frame()
        self.close_log()

    def process_frame(self, current_frame):
        if self.calibration_ref is not None and self.noise_subtraction_active.is_set():
            current_frame = neg_dif(current_frame, self.calibration_ref)

        if self.first_volume or self.volume_buffer.shape[1:3] != current_frame.shape:
            self.volume_buffer = np.empty(
                (self.n_planes, *current_frame.shape), dtype=np.uint16
            )
            self.first_volume = False

        self.logger.log_message(f"received plane {self.i_plane}")
        self.volume_buffer[self.i_plane, :, :] = current_frame
        self.i_plane += 1
        if self.i_plane == self.n_planes:
            self.fill_queues()
            self.i_plane = 0

    def fill_queues(self):
        if self.viewer_queue.queue.qsize() < 3:
            self.viewer_queue.put(self.volume_buffer)
        else:
            pass  # volume has been dropped from the viewer
        if self.saving_signal.is_set():
            self.saver_queue.put(self.volume_buffer)

    def get_frame(self):
        if self.wait_signal.is_set():
            self.logger.log_message("wait starting")
            self.saver_queue.clear()
            while self.wait_signal.is_set():
                try:
                    _ = self.camera_queue.get(timeout=TIMEOUT_S)
                except Empty:
                    pass
            self.logger.log_message("wait over")
            self.i_plane = 0
        try:
            current_frame = self.camera_queue.get(timeout=TIMEOUT_S)
            self.process_frame(current_frame)
        except Empty:
            pass

    def receive_options(self):
        # Get number of planes:
        n_planes = get_last_parameters(self.n_planes_queue, timeout=TIMEOUT_S)

        if n_planes is not None:
            self.n_planes = n_planes
            self.reset()

        # Get flat noise image to subtract:
        calibration_ref = get_last_parameters(
            self.calibration_ref_queue, timeout=TIMEOUT_S
        )
        if calibration_ref is not None:
            self.calibration_ref = calibration_ref

    def reset(self):
        self.first_volume = True
        self.i_plane = 0
