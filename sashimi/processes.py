from multiprocessing import Process
import time
from pathlib import Path
from typing import Optional, TextIO


class ConcurrenceLogger:
    def __init__(self, process_name):
        self.file: Optional[TextIO] = None
        self.process_name = process_name
        self.root = Path("C:/Users/Vilim/logs")  # TODO use config
        # TODO log things into a list and only write it out on program end

    def log_event(self, event_name):
        if self.file is None:
            self.file = open(self.root / (self.process_name + ".txt"), "w")
        self.file.write(f"{time.time_ns()},{event_name}\n")

    def close(self):
        if self.file is not None:
            self.file.close()


class LoggingProcess(Process):
    def __init__(self, *args, name, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ConcurrenceLogger(name)

    def close_log(self):
        self.logger.close()
