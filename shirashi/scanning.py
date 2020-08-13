from multiprocessing import Process
from multiprocessing import Queue, Event
from dataclasses import dataclass
from dataclasses import asdict
from enum import Enum
from copy import deepcopy
from warnings import warn
from arrayqueues.shared_arrays import ArrayQueue
import numpy as np

from typing import Union, Tuple

from shirashi.utilities import lcm, get_last_parameters
from shirashi.config import read_config

conf = read_config()


if not conf["scopeless"]:
    from nidaqmx.task import Task
    from nidaqmx.errors import DaqError

else:
    from scopecuisine.theknights.task import Task
    from scopecuisine.theknights.errors import DaqError

PIEZO_SCALE = conf["piezo"]["synchronization"]["scale"]


class ScanningState(Enum):
    PAUSED = 1
    PLANAR = 2
    VOLUMETRIC = 3


class ExperimentPrepareState(Enum):
    PREVIEW = 1
    NO_TRIGGER = 2
    EXPERIMENT_STARTED = 3
    ABORT = 4


@dataclass
class TriggeringParameters:
    n_planes: int = 0
    n_skip_start: int = 0
    n_skip_end: int = 0
    frequency: Union[None, float] = None


@dataclass
class ScanParameters:
    state: ScanningState = ScanningState.PAUSED
    experiment_state: ExperimentPrepareState = ExperimentPrepareState.PREVIEW
    triggering: TriggeringParameters = TriggeringParameters()


class ScanLoop:
    def __init__(
        self,
        stop_event,
        initial_parameters: ScanParameters,
        parameter_queue: Queue,
        n_samples,
        sample_rate,
        experiment_start_signal: Event,
        wait_signal: Event,
    ):

        self.sample_rate = sample_rate
        self.n_samples = n_samples

        self.stop_event = stop_event

        self.started = False
        self.n_acquired = 0
        self.first_update = True
        self.i_sample = 0
        self.n_samples_read = 0

        self.lateral_waveform = TriangleWaveform(**asdict(self.parameters.xy.lateral))
        self.frontal_waveform = TriangleWaveform(**asdict(self.parameters.xy.lateral))

        self.time = np.arange(self.n_samples) / self.sample_rate
        self.shifted_time = self.time.copy()

        self.wait_signal = wait_signal

    def initialize(self):
        self.n_acquired = 0
        self.first_update = True
        self.i_sample = 0
        self.n_samples_read = 0

    def n_samples_period(self):
        ns_lateral = int(round(self.sample_rate / self.lateral_waveform.frequency))
        ns_frontal = int(round(self.sample_rate / self.frontal_waveform.frequency))
        return lcm(ns_lateral, ns_frontal)

    def update_settings(self):
        new_params = get_last_parameters(self.parameter_queue)
        if new_params is not None:
            self.parameters = new_params
            self.lateral_waveform = TriangleWaveform(
                **asdict(self.parameters.xy.lateral)
            )
            self.frontal_waveform = TriangleWaveform(
                **asdict(self.parameters.xy.frontal)
            )
            self.first_update = False
            return True
        return False

    def loop_condition(self):
        return not self.stop_event.is_set()

    def check_start(self):
        if not self.started:
            self.read_task.start()
            self.write_task_xy.start()
            self.write_task_z.start()
            self.started = True

    def loop(self):
        while True:
            self.update_settings()
            self.old_parameters = deepcopy(self.parameters)
            if not self.loop_condition():
                break
            self.fill_arrays()
            self.write()
            self.check_start()
            self.read()
            self.i_sample = (self.i_sample + self.n_samples) % self.n_samples_period()
            self.n_acquired += 1


class PlanarScanLoop(ScanLoop):
    def __init__(self, *args, **kwargs):
        self.camera_on = False

    def loop_condition(self):
        return (
            super().loop_condition()
            and self.parameters.state == ScanningState.PLANAR
        )


class VolumetricScanLoop(ScanLoop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.z_waveform = SawtoothWaveform()
        buffer_len = int(round(self.sample_rate / self.parameters.z.frequency))
        self.recorded_signal = FillingRollingBuffer(buffer_len)
        self.camera_pulses = RollingBuffer(buffer_len)
        self.current_frequency = self.parameters.z.frequency
        self.camera_on = False
        self.trigger_exp_start = False
        self.wait_signal.set()

    def initialize(self):
        super().initialize()
        self.camera_on = False
        self.wait_signal.set()

    def loop_condition(self):
        return (
            super().loop_condition()
            and self.parameters.state == ScanningState.VOLUMETRIC
        )

    def check_start(self):
        super().check_start()
        if self.trigger_exp_start:
            self.experiment_start_event.set()
            self.trigger_exp_start = False

        if (
            self.parameters.experiment_state
            == ExperimentPrepareState.EXPERIMENT_STARTED
        ):
            self.parameters.experiment_state = ExperimentPrepareState.PREVIEW

    def n_samples_period(self):
        n_samples_trigger = int(round(self.sample_rate / self.parameters.z.frequency))
        return lcm(n_samples_trigger, super().n_samples_period())

    def update_settings(self):
        updated = super().update_settings()
        if not updated and not self.first_update:
            return False

        if self.parameters.state != ScanningState.VOLUMETRIC:
            return True




class Scanner(Process):
    def __init__(
        self,
        stop_event: Event,
        experiment_start_event,
        n_samples_waveform=10000,
        sample_rate=40000,
    ):
        super().__init__()

        self.stop_event = stop_event
        self.experiment_start_event = experiment_start_event
        self.wait_signal = Event()

        self.parameter_queue = Queue()

        self.n_samples = n_samples_waveform
        self.sample_rate = sample_rate

        self.parameters = ScanParameters()

    def retrieve_parameters(self):
        new_params = get_last_parameters(self.parameter_queue)
        if new_params is not None:
            self.parameters = new_params

    def run(self):
        while not self.stop_event.is_set():
            if self.parameters.state == ScanningState.PAUSED:
                self.retrieve_parameters()
                continue

            with Task() as read_task, Task() as write_task_z, Task() as write_task_xy:
                if self.parameters.state == ScanningState.PLANAR:
                    loop = PlanarScanLoop
                elif self.parameters.state == ScanningState.VOLUMETRIC:
                    loop = VolumetricScanLoop

                scanloop = loop(
                    read_task,
                    write_task_z,
                    write_task_xy,
                    self.stop_event,
                    self.parameters,
                    self.parameter_queue,
                    self.n_samples,
                    self.sample_rate,
                    self.experiment_start_event,
                    self.wait_signal,
                )
                try:
                    scanloop.loop()
                except DaqError as e:
                    warn("NI error " + e.__repr__())
                    scanloop.initialize()
                self.parameters = deepcopy(
                    scanloop.parameters
                )  # set the parameters to the last ones received in the loop
