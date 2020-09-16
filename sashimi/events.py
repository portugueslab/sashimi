from enum import Enum, auto
from multiprocessing import Event
from typing import Optional


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class SashimiEvents(AutoName):
    WAITING_FOR_TRIGGER = auto()
    TRIGGER_STYTRA = auto()
    IS_SAVING = auto()
    NOISE_SUBTRACTION_ACTIVE = auto()
    SAVING_STOPPED = auto()
    CLOSE_ALL = auto()
    RESTART_SCANNING = auto()


class LoggedEvent:
    def __init__(self, logger, name: SashimiEvents, event: Optional[Event] = None):
        super().__init__()
        if event is None:
            self.event = Event()
        else:
            self.event = event
        self.logger = logger
        self.name = name
        self.was_set = False

    def new_reference(self, logger):
        return LoggedEvent(logger, self.name, self.event)

    def set(self):
        self.event.set()
        if not self.was_set:
            self.logger.log_event(self.name, True, True)
        self.was_set = True

    def clear(self):
        self.event.clear()
        if self.was_set:
            self.logger.log_event(self.name, True, False)
        self.was_set = False

    def is_set(self):
        res = self.event.is_set()
        if res and not self.was_set:
            self.logger.log_event(self.name, False, True)
        if not res and self.was_set:
            self.logger.log_event(self.name, False, False)
        self.was_set = res
        return res
