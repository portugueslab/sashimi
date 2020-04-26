from multiprocessing import Process
from multiprocessing import Queue
from arrayqueues.shared_arrays import ArrayQueue
from lightparam import Parametrized

import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.constants import Edge, AcquisitionType, LineGrouping


class Piezo(Parametrized):
    def __init__(self):
        pass


class Scanner(Process):
    def __init__(self, n_samples_waveform=8000, sample_rate=40000):
        super().__init__()
        self.control_queue = Queue()
        self.waveform_queue = ArrayQueue()
        self.n_samples = n_samples_waveform
        self.sample_rate = sample_rate

    def setup_tasks(self, read_task, write_task_1, write_task_2):
        # Configure the channels

        # read channel is only the piezo position on board 1
        read_task.ai_channels.add_ai_voltage_chan("Dev1/ai0:1", min_val=0, max_val=10)

        # write channels are on board 1: piezo and z galvos
        write_task_1.ao_channels.add_ao_voltage_chan(
            "Dev1/ao0:3", min_val=-5, max_val=10
        )

        # on board 2: lateral galvos
        write_task_2.ao_channels.add_ao_voltage_chan(
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
        write_task_1.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            source="OnboardClock",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.n_samples,
        )

        write_task_2.timing.cfg_samp_clk_timing(
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
