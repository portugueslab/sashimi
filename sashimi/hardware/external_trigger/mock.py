from sashimi.hardware.external_trigger.interface import AbstractComm


class MockComm(AbstractComm):
    def trigger_and_receive_duration(self, config):
        return None
