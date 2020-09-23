from sashimi.hardware.external_trigger.interface import AbstractComm


class MockComm(AbstractComm):
    def __init__(self):
        super().__init__(address=None)

    def trigger_and_receive_duration(self, config):
        return None
