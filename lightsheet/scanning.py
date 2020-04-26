from multiprocessing import Process
from multiprocessing import Queue
from arrayqueues.shared_arrays import ArrayQueue
from lightparam import Parametrized


class Piezo(Parametrized):
    def __init__(self):
        pass

class ScanningProcess(Process):
    def __init__(self):
        super().__init__()
        self.control_queue = Queue()
        self.waveform_queue = ArrayQueue()

    def run(self):
        pass