from multiprocessing import Queue, Event
from copy import deepcopy

from sashimi.hardware.scanning.scanloops import (
    ScanningState,
    ScanParameters,
    PlanarScanLoop,
    VolumetricScanLoop,
)
from warnings import warn
from arrayqueues.shared_arrays import ArrayQueue

from sashimi.utilities import get_last_parameters
from sashimi.config import read_config
from sashimi.processes.logging import LoggingProcess
from sashimi.events import LoggedEvent, SashimiEvents

from sashimi.hardware.scanning import ni

conf = read_config()


if not conf["scopeless"]:
    from nidaqmx.task import Task
    from nidaqmx.constants import Edge, AcquisitionType
    from nidaqmx.errors import DaqError

else:
    from scopecuisine.theknights.constants import Edge, AcquisitionType
    from scopecuisine.theknights.task import Task
    from scopecuisine.theknights.errors import DaqError


class Scanner(LoggingProcess):
    def __init__(
        self,
        stop_event: LoggedEvent,
        experiment_start_event: LoggedEvent,
        start_experiment_from_scanner=False,
        n_samples_waveform=10000,
        sample_rate=40000,
    ):
        super().__init__(name="scanner")

        self.stop_event = stop_event.new_reference(self.logger)
        self.experiment_start_event = experiment_start_event.new_reference(self.logger)
        self.wait_signal = LoggedEvent(
            self.logger, SashimiEvents.WAITING_FOR_TRIGGER, Event()
        )

        self.parameter_queue = Queue()

        self.waveform_queue = ArrayQueue(max_mbytes=100)
        self.n_samples = n_samples_waveform
        self.sample_rate = sample_rate

        self.parameters = ScanParameters()
        self.start_experiment_from_scanner = start_experiment_from_scanner

    def retrieve_parameters(self):
        new_params = get_last_parameters(self.parameter_queue)
        if new_params is not None:
            self.parameters = new_params

    def run(self):
        self.logger.log_message("started")
        while not self.stop_event.is_set():
            if self.parameters.state == ScanningState.PAUSED:
                self.retrieve_parameters()
                continue
            with ni.NIScanConfigurator(self.n_samples, conf) as board:
                if self.parameters.state == ScanningState.PLANAR:
                    loop = PlanarScanLoop
                elif self.parameters.state == ScanningState.VOLUMETRIC:
                    loop = VolumetricScanLoop

                scanloop = loop(
                    board,
                    self.stop_event,
                    self.parameters,
                    self.parameter_queue,
                    self.n_samples,
                    self.sample_rate,
                    self.waveform_queue,
                    self.experiment_start_event,
                    self.wait_signal,
                    self.logger,
                    self.start_experiment_from_scanner,
                )
                try:
                    scanloop.loop()
                except DaqError as e:
                    warn("NI error " + e.__repr__())
                    scanloop.initialize()
                self.parameters = deepcopy(
                    scanloop.parameters
                )  # set the parameters to the last ones received in the loop
        self.close_log()
