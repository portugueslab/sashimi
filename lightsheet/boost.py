from multiprocessing import Process, Queue, Event
from queue import Empty


class FrameDispatcher(Process):
    def __init__(self, stop_event: Event):
        super().__init__()
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            pass

    def get_image(self):
        try:
            image = self.camera.image_queue.get(timeout=0.001)
            if self.calibration_ref is not None:
                image = neg_dif(image, self.calibration_ref)
            if self.saver.saving_signal.is_set():
                if self.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED:
                    self.saver.save_queue.put(image)
            return image
        except Empty:
            return None


