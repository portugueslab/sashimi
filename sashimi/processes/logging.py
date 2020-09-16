from multiprocessing import Process
import time
from pathlib import Path
from typing import Optional, TextIO
from enum import Enum

from sashimi import config


class ConcurrenceLogger:
    def __init__(self, process_name):
        self.file: Optional[TextIO] = None
        self.process_name = process_name
        configuration = config.read_config()
        self.root = Path(configuration["default_paths"]["log"])

    def write_entry(self, event_type, event_id, is_sender, event_value):
        if self.file is None:
            self.file = open(self.root / (self.process_name + ".txt"), "w")
        self.file.write(
            f"{time.time_ns()},{event_type},{event_id},{'1' if is_sender else '0'},{event_value}\n"
        )

    def log_message(self, message):
        self.write_entry("LOG", message, False, 0)

    def log_event(self, event_name: Enum, is_sender: bool, event_value: bool):
        self.write_entry(
            "EVENT", event_name.name, is_sender, "1" if event_value else "0"
        )

    def log_queue(self, queue_name, is_sender):
        self.write_entry("QUEUE", queue_name.name, is_sender, "1")

    def close(self):
        if self.file is not None:
            self.file.flush()
            self.file.close()


class LoggingProcess(Process):
    def __init__(self, *args, name, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ConcurrenceLogger(name)

    def close_log(self):
        self.logger.close()
