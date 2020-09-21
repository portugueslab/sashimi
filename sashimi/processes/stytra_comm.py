from multiprocessing import Queue
from sashimi.processes.logging import LoggingProcess
from sashimi.events import LoggedEvent
from queue import Empty
import zmq
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Optional


def clean_json(d):
    if isinstance(d, dict):
        cleaned = dict()
        for key, value in d.items():
            cleaned[key] = clean_json(value)
        return cleaned
    elif isinstance(d, Enum):
        return d.name
    elif is_dataclass(d):
        return clean_json(asdict(d))
    else:
        return d


class AbstractComm:
    def trigger_and_receive_duration(self, config) -> Optional[float]:
        return None


class StytraComm(AbstractComm):
    def __init__(self, computer_adderss):
        self.zmq_tcp_address = computer_adderss

    def trigger_and_receive_duration(self, config) -> Optional[float]:
        zmq_context = zmq.Context()
        with zmq_context.socket(zmq.REQ) as zmq_socket:
            zmq_socket.connect(self.zmq_tcp_address)
            zmq_socket.send_json(config)
            poller = zmq.Poller()
            poller.register(zmq_socket, zmq.POLLIN)
            duration = None
            if poller.poll(1000):
                duration = zmq_socket.recv_json()

        zmq_context.destroy()
        return duration


class ExternalComm(LoggingProcess):
    def __init__(
        self,
        stop_event: LoggedEvent,
        experiment_start_event: LoggedEvent,
        is_saving_event: LoggedEvent,
        is_waiting_event: LoggedEvent,
        stytra_address="tcp://O1-589:5555",
        scanning_trigger=True,
    ):
        super().__init__(name="stytracomm")
        self.current_settings_queue = Queue()
        self.current_settings = None
        self.start_stytra = experiment_start_event.new_reference(self.logger)
        self.stop_event = stop_event.new_reference(self.logger)
        self.saving_event = is_saving_event.new_reference(self.logger)
        self.duration_queue = Queue()
        self.comm = StytraComm(stytra_address)
        self.scanning_trigger = scanning_trigger
        if self.scanning_trigger:
            self.waiting_event = is_waiting_event.new_reference(self.logger)

    def trigger_condition(self):
        if self.scanning_trigger:
            return (
                self.start_stytra.is_set()
                and self.saving_event.is_set()
                and not self.waiting_event.is_set()
            )

    def run(self):
        self.logger.log_message("started")
        while not self.stop_event.is_set():
            while True:
                try:
                    self.current_settings = self.current_settings_queue.get(
                        timeout=0.00001
                    )
                    current_config = dict(lightsheet=clean_json(self.current_settings))
                except Empty:
                    break
            if self.trigger_condition():
                duration = self.comm.trigger_and_receive_duration(current_config)
                if duration is not None:
                    self.duration_queue.put(duration)
                self.logger.log_message("sent communication")
                self.start_stytra.clear()
        self.close_log()
