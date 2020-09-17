from multiprocessing import Queue, Event
from copy import deepcopy

from sashimi.hardware.scanning.scanloops import (
    ScanningState,
    ScanParameters,
    PlanarScanLoop,
    VolumetricScanLoop,
)
from sashimi.hardware.scanning.interface import ScanningError
from sashimi.hardware.scanning.mock import open_mockboard

try:
    from sashimi.hardware.scanning.ni import open_niboard

    NI_AVAILABLE = True
except ImportError:
    NI_AVAILABLE = False

from warnings import warn
from arrayqueues.shared_arrays import ArrayQueue

from sashimi.utilities import get_last_parameters
from sashimi.config import read_config
from sashimi.processes.logging import LoggingProcess
from sashimi.events import LoggedEvent, SashimiEvents


conf = read_config()

scan_conf_dict = dict(mock=open_mockboard)

if NI_AVAILABLE:
    scan_conf_dict["ni"] = open_niboard


class Scanner(LoggingProcess):
    def __init__(
        self,
        stop_event: LoggedEvent,
        waiting_event: LoggedEvent,
        restart_event: LoggedEvent,
        start_experiment_from_scanner=False,
        n_samples_waveform=10000,
        sample_rate=40000,
    ):
        super().__init__(name="scanner")

        self.stop_event = stop_event.new_reference(self.logger)
        self.restart_event = restart_event.new_reference(self.logger)
        self.wait_signal = waiting_event.new_reference(self.logger)

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
        configurator = scan_conf_dict[conf["scanning"]]
        first_volume_run = True
        while not self.stop_event.is_set():
            if self.parameters.state == ScanningState.PAUSED:
                self.retrieve_parameters()
                continue
            with configurator(self.sample_rate, self.n_samples, conf) as board:
                if self.parameters.state == ScanningState.PLANAR:
                    loop = PlanarScanLoop
                elif self.parameters.state == ScanningState.VOLUMETRIC:
                    loop = VolumetricScanLoop

                scanloop = loop(
                    board,
                    self.stop_event,
                    self.restart_event,
                    self.parameters,
                    self.parameter_queue,
                    self.n_samples,
                    self.sample_rate,
                    self.waveform_queue,
                    self.wait_signal,
                    self.logger,
                    self.start_experiment_from_scanner,
                )
                try:
                    # A hack to skip the first time the volumetric scan loop is run
                    scanloop.loop(
                        first_volume_run
                        if issubclass(loop, VolumetricScanLoop)
                        else False
                    )
                    if issubclass(loop, VolumetricScanLoop):
                        first_volume_run = False
                except ScanningError as e:
                    warn("NI error " + e.__repr__())
                    scanloop.initialize()
                self.parameters = deepcopy(
                    scanloop.parameters
                )  # set the parameters to the last ones received in the loop
        self.close_log()
