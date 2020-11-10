from typing import Optional


class AbstractComm:
    def __init__(self, address=None, **kwargs):
        self.address = address

    def trigger_and_receive_duration(self, config) -> Optional[float]:
        return None
