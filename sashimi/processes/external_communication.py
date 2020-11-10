from multiprocessing import Queue
from sashimi.processes.logging import LoggingProcess
from sashimi.utilities import clean_json
from sashimi.events import LoggedEvent
from sashimi.config import read_config
from sashimi.hardware.external_trigger import external_comm_class_dict
from queue import Empty


conf = read_config()


class ExternalComm(LoggingProcess):
    def __init__(
        self,
        stop_event: LoggedEvent,
        experiment_start_event: LoggedEvent,
        is_saving_event: LoggedEvent,
        is_waiting_event: LoggedEvent,
        scanning_trigger=True,
    ):
        super().__init__(name="external_comm")
        self.current_settings_queue = Queue()
        self.current_settings = None
        self.start_comm = experiment_start_event.new_reference(self.logger)
        self.stop_event = stop_event.new_reference(self.logger)
        self.saving_event = is_saving_event.new_reference(self.logger)
        self.duration_queue = Queue()

        # Set up external communication from conf file
        external_trigger_conf = conf.pop("external_communication")
        external_trigger_name = external_trigger_conf.pop("name")

        self.comm = external_comm_class_dict[external_trigger_name](**external_trigger_conf)


        self.scanning_trigger = scanning_trigger
        if self.scanning_trigger:
            self.waiting_event = is_waiting_event.new_reference(self.logger)

    def trigger_condition(self):
        if self.scanning_trigger:
            return (
                self.start_comm.is_set()
                and self.saving_event.is_set()
                and not self.waiting_event.is_set()
            )

    def run(self):
        self.logger.log_message("started")
        while not self.stop_event.is_set():
            while True:
                try:
                    self.current_settings = self.current_settings_queue.get(
                        timeout=0.00001
                    )
                    current_config = dict(lightsheet=clean_json(self.current_settings))
                except Empty:
                    break
            if self.trigger_condition():
                duration = self.comm.trigger_and_receive_duration(current_config)
                if duration is not None:
                    self.duration_queue.put(duration)
                self.logger.log_message("sent communication")
                self.start_comm.clear()
        self.close_log()
