from multiprocessing import Process
from multiprocessing import Queue, Event
from dataclasses import dataclass
from enum import Enum
from queue import Empty

from arrayqueues.shared_arrays import ArrayQueue
import numpy as np

from typing import Union, Tuple

from lightsheet.waveforms import (
    TriangleWaveform,
    ImpulseWaveform,
    SawtoothWaveform,
    RecordedWaveform,
)

try:
    import nidaqmx
    from nidaqmx.stream_readers import AnalogMultiChannelReader
    from nidaqmx.stream_writers import AnalogMultiChannelWriter
    from nidaqmx.constants import Edge, AcquisitionType, LineGrouping

    dry_run = False
except ImportError:
    dry_run = True


class ScanningState(Enum):
    PAUSED = 1
    PLANAR = 2
    VOLUMETRIC = 3


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
    lateral: float = 0
    frontal: float = 0
    piezo: float = 0


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


@dataclass
class ScanParameters:
    state: ScanningState = ScanningState.PAUSED
    z: Union[ZScanning, ZManual, ZSynced] = ZManual()
    xy: PlanarScanning = PlanarScanning()
    triggering: TriggeringParameters = TriggeringParameters


class ScanLoop:
    def __init__(
        self,
        read_task,
        write_task_z,
        write_task_xy,
        stop_event,
        settings_queue: Queue,
        n_samples,
        sample_rate,
    ):

        self.sample_rate = sample_rate
        self.n_samples = n_samples

        self.read_task = read_task
        self.write_task_z = write_task_z
        self.write_task_xy = write_task_xy

        self.z_writer = AnalogMultiChannelWriter(write_task_z.out_stream)
        self.xy_writer = AnalogMultiChannelWriter(write_task_xy.out_stream)
        self.z_reader = AnalogMultiChannelReader(read_task.in_stream)

        self.stop_event = stop_event

        self.read_array = np.zeros(n_samples)
        self.write_arrays = np.zeros(
            (6, n_samples)
        )  # piezo, z lateral, frontal, camera, xy lateral frontal

        self.settings_queue = settings_queue

        self.settings = ScanParameters()

        self.started = False
        self.n_acquired = 0

        self.lateral_waveform = TriangleWaveform(**self.settings.xy.lateral.asdict())
        self.frontal_waveform = TriangleWaveform(**self.settings.xy.lateral.asdict())

        self.time = np.arange(self.n_samples) / self.sample_rate
        self.shifted_time = self.time.copy()
        self.i_sample = 0

    def update_settings(self):
        try:
            self.settings = self.settings_queue.get(timeout=0.001)
        except Empty:
            pass
        self.lateral_waveform = TriangleWaveform(**self.settings.xy.lateral.asdict())
        self.frontal_waveform = TriangleWaveform(**self.settings.xy.lateral.asdict())

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
            self.read_array, number_of_samples_per_channel=self.n_samples_in, timeout=1,
        )

    def loop(self):
        while self.loop_condition():
            self.fill_arrays()
            self.write()
            self.check_start()
            self.read()
            self.i_sample += self.n_samples
            self.n_acquired += 0


def calc_sync(z, sync_coef):
    return sync_coef[0] + sync_coef[1] * z


class PlanarScanLoop(ScanLoop):
    def fill_arrays(self):
        # Fill the z values
        self.write_arrays[0, :] = self.settings.z.piezo
        if isinstance(self.settings.z, ZManual):
            self.write_arrays[1, :] = self.settings.z.lateral
            self.write_arrays[2, :] = self.settings.z.frontal
        elif isinstance(self.settings.z, ZSynced):
            self.write_arrays[1, :] = calc_sync(
                self.settings.z.piezo, self.settings.z.lateral_sync
            )
            self.write_arrays[2, :] = calc_sync(
                self.settings.z.piezo, self.settings.z.frontal_sync
            )
        super().fill_arrays()


class VolumetricScanLoop(ScanLoop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.z_waveform = SawtoothWaveform()


class Scanner(Process):
    def __init__(self, n_samples_waveform=8000, sample_rate=40000):
        super().__init__()

        self.stop_event = Event()

        self.parameter_queue = Queue()

        self.waveform_queue = ArrayQueue()
        self.n_samples = n_samples_waveform
        self.sample_rate = sample_rate

        self.scanning_state = ScanningState.PAUSED

    def setup_tasks(self, read_task, write_task_z, write_task_xy):
        # Configure the channels

        # read channel is only the piezo position on board 1
        read_task.ai_channels.add_ai_voltage_chan("Dev1/ai0:1", min_val=0, max_val=10)

        # write channels are on board 1: piezo and z galvos
        write_task_z.ao_channels.add_ao_voltage_chan(
            "Dev1/ao0:3", min_val=-5, max_val=10
        )

        # on board 2: lateral galvos
        write_task_xy.ao_channels.add_ao_voltage_chan(
            "Dev2/ao0:1", min_val=-5, max_val=10
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
            "/Dev1/ao/StartTrigger", Edge.RISING
        )

    def retrieve_parameters(self):
        pass

    def run(self):
        while not self.stop_event.is_set():
            if self.scanning_state == ScanningState.PAUSED:
                self.retrieve_parameters()
                continue

            with nidaqmx.Task() as read_task, nidaqmx.Task() as write_task_z, nidaqmx.Task() as write_task_xy:
                self.setup_tasks(read_task, write_task_z, write_task_xy)
                if self.scanning_state == ScanningState.PLANAR:
                    loop = PlanarScanLoop
                elif self.scanning_state == ScanningState.VOLUMETRIC:
                    loop = VolumetricScanLoop

                l = loop(
                    read_task,
                    write_task_z,
                    write_task_xy,
                    self.stop_event,
                    self.parameter_queue,
                    self.n_samples,
                    self.sample_rate,
                )
                l.loop()
