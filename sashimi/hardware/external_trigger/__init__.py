from typing import Optional


class AbstractComm:
    def trigger_and_receive_duration(self, config) -> Optional[float]:
        return None
