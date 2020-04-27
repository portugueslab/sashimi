from multiprocessing import Process
from multiprocessing import Queue
from dataclasses import dataclass
from enum import Enum

from arrayqueues.shared_arrays import ArrayQueue
from lightparam import Parametrized

try:
    import nidaqmx
    from nidaqmx.stream_readers import AnalogMultiChannelReader
    from nidaqmx.stream_writers import AnalogMultiChannelWriter
    from nidaqmx.constants import Edge, AcquisitionType, LineGrouping

    dry_run = False
except ImportError:
    dry_run = True


class Waveform(Enum):
    sine = 1
    triangle = 2


@dataclass
class XYScanning:
    vmin: float = 1
    vmax: float = 0
    frequency: float = 800
    waveform: Waveform = Waveform.sine


@dataclass
class PlanarScanning:
    lateral: XYScanning
    frontal: XYScanning


@dataclass
class ZScanning:
    lateral: float = 0
    frontal: float = 0
    piezo: float = 0


class Scanner(Process):
    def __init__(self, n_samples_waveform=8000, sample_rate=40000):
        super().__init__()
        self.control_queue = Queue()
        self.waveform_queue = ArrayQueue()
        self.n_samples = n_samples_waveform
        self.sample_rate = sample_rate

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

    def run(self):
        pass
