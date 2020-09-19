from typing import Optional


class AbstractComm:
    def __init__(self, address):
        self.address = address

    def trigger_and_receive_duration(self, config) -> Optional[float]:
        return None
