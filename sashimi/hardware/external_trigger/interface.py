from typing import Optional
from abc import ABC, abstractmethod


class AbstractComm(ABC):
    def __init__(self, address):
        self.address = address

    @abstractmethod
    def trigger_and_receive_duration(self, config) -> Optional[float]:
        return None
