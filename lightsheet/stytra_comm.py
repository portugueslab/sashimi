from multiprocessing import Process, Queue, Event
from queue import Empty
import zmq
from dataclasses import asdict
from enum import Enum


def clean_json(d):
    if isinstance(d, dict):
        cleaned = dict()
        for key, value in d.items():
            cleaned = clean_json(value)
        return cleaned
    elif isinstance(d, Enum):
        return d.name
    else:
        return d


class StytraCom(Process):
    def __init__(
        self,
        stop_event: Event,
        experiment_start_event: Event,
        stytra_address="tcp://O1-589:5555",
    ):
        super().__init__()
        self.current_settings_queue = Queue()
        self.current_settings = None
        self.start_stytra = experiment_start_event
        self.stop_event = stop_event
        self.zmq_tcp_address = stytra_address
        self.stytra_data_queue = Queue()

    def run(self):

        while not self.stop_event.is_set():
            while True:
                try:
                    self.current_settings = self.current_settings_queue.get(
                        timeout=0.00001
                    )
                except Empty:
                    break
            if self.start_stytra.is_set():
                zmq_context = zmq.Context()
                with zmq_context.socket(zmq.REQ) as zmq_socket:
                    zmq_socket.connect(self.zmq_tcp_address)
                    zmq_socket.send_json(clean_json(asdict(self.current_settings)))
                    poller = zmq.Poller()
                    poller.register(zmq_socket, zmq.POLLIN)
                    duration = None
                    if poller.poll(1000):
                        duration = zmq_socket.recv_json()
                    self.stytra_data_queue.put(duration)
                    zmq_socket.close()
                    zmq_context.destroy()
                self.start_stytra.clear()
