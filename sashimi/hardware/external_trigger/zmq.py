from sashimi.hardware.external_trigger.interface import AbstractComm
import zmq
from typing import Optional


class ZmqComm(AbstractComm):
    def trigger_and_receive_duration(self, config) -> Optional[float]:
        zmq_context = zmq.Context()
        with zmq_context.socket(zmq.REQ) as zmq_socket:
            zmq_socket.connect(self.address)
            zmq_socket.send_json(config)
            poller = zmq.Poller()
            poller.register(zmq_socket, zmq.POLLIN)
            duration = None
            if poller.poll(1000):
                duration = zmq_socket.recv_json()

        zmq_context.destroy()
        return duration
