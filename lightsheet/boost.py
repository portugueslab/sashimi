from multiprocessing import Process, Queue, Event
from queue import Empty, Full
from arrayqueues .shared_arrays import ArrayQueue
from lightsheet.utilities import neg_dif


class FrameDispatcher(Process):
    def __init__(
            self,
            stop_event: Event,
            saving_signal: Event,
            camera_queue: ArrayQueue,
            saver_queue: ArrayQueue
    ):
        super().__init__()
        self.stop_event = stop_event
        self.saving_signal = saving_signal
        self.camera_queue = camera_queue
        self.saver_queue = saver_queue
        self.viewer_queue = ArrayQueue()
        self.calibration_ref_queue = ArrayQueue()
        self.current_image = None
        self.calibration_ref = None

    def run(self):
        while not self.stop_event.is_set():
            self.current_image = self.get_image()
            if self.current_image is not None:
                self.send_receive()
                self.current_image = None

    def get_image(self):
        try:
            image = self.camera_queue.get(timeout=0.001)
            if self.calibration_ref is not None:
                image = neg_dif(image, self.calibration_ref)
            if self.saving_signal.is_set():
                self.saver_queue.put(image)
            return image
        except Empty:
            return None

    def send_receive(self):
        try:
            self.viewer_queue.put(self.current_image)
        except Full:
            self.viewer_queue.clear()
        try:
            self.calibration_ref = self.calibration_ref_queue.get(timeout=0.001)
        except Empty:
            pass

