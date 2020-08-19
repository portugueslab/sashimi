from multiprocessing import Process
from multiprocessing import Queue, Event
from dataclasses import dataclass
from dataclasses import asdict
from enum import Enum
from copy import deepcopy
from sashimi.rolling_buffer import RollingBuffer, FillingRollingBuffer
from warnings import warn
from arrayqueues.shared_arrays import ArrayQueue
import numpy as np

from typing import Union, Tuple

from sashimi.utilities import lcm, get_last_parameters
from sashimi.waveforms import TriangleWaveform, SawtoothWaveform, set_impulses
from sashimi.config import read_config

conf = read_config()


if not conf["scopeless"]:
    from nidaqmx.task import Task
    from nidaqmx.stream_readers import AnalogSingleChannelReader
    from nidaqmx.stream_writers import AnalogMultiChannelWriter
    from nidaqmx.constants import Edge, AcquisitionType
    from nidaqmx.errors import DaqError

else:
    from scopecuisine.theknights.stream_readers import AnalogSingleChannelReader
    from scopecuisine.theknights.stream_writers import AnalogMultiChannelWriter
    from scopecuisine.theknights.constants import Edge, AcquisitionType
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
class XYScanning:
    vmin: float = 1
    vmax: float = 0
    frequency: float = 800


@dataclass
class PlanarScanning:
    lateral: XYScanning = XYScanning()
    frontal: XYScanning = XYScanning()


@dataclass
class ZManual:
    piezo: float = 0
    lateral: float = 0
    frontal: float = 0


@dataclass
class ZSynced:
    piezo: float = 0
    lateral_sync: Tuple[float, float] = (0.0, 0.0)
    frontal_sync: Tuple[float, float] = (0.0, 0.0)


@dataclass
class ZScanning:
    piezo_min: float = 0
    piezo_max: float = 0
    frequency: float = 1
    lateral_sync: Tuple[float, float] = (0.0, 0.0)
    frontal_sync: Tuple[float, float] = (0.0, 0.0)


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
    z: Union[ZScanning, ZManual, ZSynced] = ZManual()
    xy: PlanarScanning = PlanarScanning()
    triggering: TriggeringParameters = TriggeringParameters()


class ScanLoop:
    def __init__(
        self,
        read_task,
        write_task_z,
        write_task_xy,
        stop_event,
        initial_parameters: ScanParameters,
        parameter_queue: Queue,
        n_samples,
        sample_rate,
        waveform_queue: ArrayQueue,
        experiment_start_signal: Event,
        wait_signal: Event,
    ):

        self.sample_rate = sample_rate
        self.n_samples = n_samples

        self.read_task = read_task
        self.write_task_z = write_task_z
        self.write_task_xy = write_task_xy

        self.z_writer = AnalogMultiChannelWriter(write_task_z.out_stream)
        self.xy_writer = AnalogMultiChannelWriter(write_task_xy.out_stream)
        self.z_reader = AnalogSingleChannelReader(read_task.in_stream)

        self.stop_event = stop_event

        self.read_array = np.zeros(n_samples)
        self.write_arrays = np.zeros(
            (6, n_samples)
        )  # piezo, z lateral, frontal, camera, xy lateral frontal

        self.parameter_queue = parameter_queue
        self.waveform_queue = waveform_queue
        self.experiment_start_event = experiment_start_signal

        self.parameters = initial_parameters
        self.old_parameters = initial_parameters

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

    def fill_arrays(self):
        self.shifted_time[:] = self.time + self.i_sample / self.sample_rate
        self.write_arrays[4, :] = self.lateral_waveform.values(self.shifted_time)
        self.write_arrays[5, :] = self.frontal_waveform.values(self.shifted_time)

    def write(self):
        self.z_writer.write_many_sample(self.write_arrays[:4])
        self.xy_writer.write_many_sample(self.write_arrays[4:])

    def read(self):
        self.z_reader.read_many_sample(
            self.read_array, number_of_samples_per_channel=self.n_samples, timeout=1,
        )
        self.n_samples_read += self.write_arrays.shape[1]
        self.read_array[:] = self.read_array / PIEZO_SCALE

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


def calc_sync(z, sync_coef):
    return sync_coef[0] + sync_coef[1] * z


class PlanarScanLoop(ScanLoop):
    def loop_condition(self):
        return (
            super().loop_condition() and self.parameters.state == ScanningState.PLANAR
        )

    def n_samples_period(self):
        if (
            self.parameters.triggering.frequency is None
            or self.parameters.triggering.frequency == 0
        ):
            return super().n_samples_period()
        else:
            n_samples_trigger = int(
                round(self.sample_rate / self.parameters.triggering.frequency)
            )
            return lcm(n_samples_trigger, super().n_samples_period())

    def fill_arrays(self):
        # Fill the z values
        self.write_arrays[0, :] = self.parameters.z.piezo * PIEZO_SCALE
        if isinstance(self.parameters.z, ZManual):
            self.write_arrays[1, :] = self.parameters.z.lateral
            self.write_arrays[2, :] = self.parameters.z.frontal
        elif isinstance(self.parameters.z, ZSynced):
            self.write_arrays[1, :] = calc_sync(
                self.parameters.z.piezo, self.parameters.z.lateral_sync
            )
            self.write_arrays[2, :] = calc_sync(
                self.parameters.z.piezo, self.parameters.z.frontal_sync
            )
        super().fill_arrays()


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

        if self.parameters != self.old_parameters:
            if self.parameters.z.frequency > 0.1:
                full_period = int(round(self.sample_rate / self.parameters.z.frequency))
                self.recorded_signal = FillingRollingBuffer(full_period)
                self.camera_pulses = RollingBuffer(full_period)
                self.initialize()

        set_impulses(
            self.camera_pulses.buffer,
            self.parameters.triggering.n_planes,
            n_skip_start=self.parameters.triggering.n_skip_start,
            n_skip_end=self.parameters.triggering.n_skip_end,
        )

        self.z_waveform = SawtoothWaveform(
            frequency=self.parameters.z.frequency,
            vmin=self.parameters.z.piezo_min,
            vmax=self.parameters.z.piezo_max,
        )

        if not self.camera_on and self.n_samples_read > self.n_samples_period():
            self.camera_on = True
            self.i_sample = 0  # puts it at the beginning of the cycle
            self.n_samples_read = 0
            self.wait_signal.clear()
            self.trigger_exp_start = True
        elif not self.camera_on:
            self.wait_signal.set()
        return True

    def read(self):
        super().read()
        i_insert = (self.i_sample - self.n_samples) % len(self.recorded_signal.buffer)
        self.recorded_signal.write(
            self.read_array[
                : min(len(self.recorded_signal.buffer), len(self.read_array))
            ],
            i_insert,
        )
        self.waveform_queue.put(self.recorded_signal.buffer)

    def fill_arrays(self):
        super().fill_arrays()
        self.write_arrays[0, :] = (
            self.z_waveform.values(self.shifted_time) * PIEZO_SCALE
        )
        i_sample = self.i_sample % len(self.recorded_signal.buffer)
        if self.recorded_signal.is_complete():
            wave_part = self.recorded_signal.read(i_sample, self.n_samples)
            max_wave, min_wave = (np.max(wave_part), np.min(wave_part))
            if (
                -2 < calc_sync(min_wave, self.parameters.z.lateral_sync) < 2
                and -2 < calc_sync(max_wave, self.parameters.z.lateral_sync) < 2
            ):
                self.write_arrays[1, :] = calc_sync(
                    wave_part, self.parameters.z.lateral_sync
                )
            if (
                -2 < calc_sync(min_wave, self.parameters.z.frontal_sync) < 2
                and -2 < calc_sync(max_wave, self.parameters.z.frontal_sync) < 2
            ):
                self.write_arrays[2, :] = calc_sync(
                    wave_part, self.parameters.z.frontal_sync
                )
        if self.camera_on:
            self.write_arrays[3, :] = self.camera_pulses.read(i_sample, self.n_samples)
        else:
            self.write_arrays[3, :] = 0


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

        self.waveform_queue = ArrayQueue(max_mbytes=100)
        self.n_samples = n_samples_waveform
        self.sample_rate = sample_rate

        self.parameters = ScanParameters()

    def setup_tasks(self, read_task, write_task_z, write_task_xy):
        # Configure the channels

        # read channel is only the piezo position on board 1
        read_task.ai_channels.add_ai_voltage_chan(
            conf["piezo"]["position_read"]["pos_chan"],
            min_val=conf["piezo"]["position_read"]["min_val"],
            max_val=conf["piezo"]["position_read"]["max_val"],
        )

        # write channels are on board 1: piezo and z galvos
        write_task_z.ao_channels.add_ao_voltage_chan(
            conf["piezo"]["position_write"]["pos_chan"],
            min_val=conf["piezo"]["position_write"]["min_val"],
            max_val=conf["piezo"]["position_write"]["max_val"],
        )

        # on board 2: lateral galvos
        write_task_xy.ao_channels.add_ao_voltage_chan(
            conf["galvo_lateral"]["write_position"]["pos_chan"],
            min_val=conf["galvo_lateral"]["write_position"]["min_val"],
            max_val=conf["galvo_lateral"]["write_position"]["max_val"],
        )

        # Set the timing of both to the onboard clock so that they are synchronised
        read_task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            source="OnboardClock",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.n_samples,
        )
        write_task_z.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            source="OnboardClock",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.n_samples,
        )

        write_task_xy.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            source="OnboardClock",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.n_samples,
        )

        # This is necessary to synchronise reading and writing
        read_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            conf["piezo"]["synchronization"]["pos_chan"], Edge.RISING
        )

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
                self.setup_tasks(read_task, write_task_z, write_task_xy)
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
                    self.waveform_queue,
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




class MockScanner(Process):
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

        self.waveform_queue = ArrayQueue(max_mbytes=100)
        self.n_samples = n_samples_waveform
        self.sample_rate = sample_rate

        self.parameters = ScanParameters()

    def setup_tasks(self, read_task, write_task_z, write_task_xy):
        # Configure the channels
        pass

    def retrieve_parameters(self):
        pass

    def run(self):
        pass