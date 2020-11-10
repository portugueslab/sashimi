from sashimi.hardware.scanning.interface import AbstractScanInterface

from contextlib import contextmanager

from nidaqmx.task import Task
from nidaqmx.constants import Edge, AcquisitionType
from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter

import numpy as np


@contextmanager
def open_niboard(sample_rate, n_samples, conf):
    with Task() as read_task, Task() as write_task_z, Task() as write_task_xy:
        try:
            yield NIBoards(
                sample_rate,
                n_samples,
                conf,
                read_task=read_task,
                write_task_z=write_task_z,
                write_task_xy=write_task_xy,
            )
        finally:
            pass


class NIBoards(AbstractScanInterface):
    def __init__(self, *args, read_task, write_task_z, write_task_xy):
        super().__init__(*args)
        self.read_task = read_task
        self.write_task_xy = write_task_xy
        self.write_task_z = write_task_z

        self.z_writer = AnalogMultiChannelWriter(write_task_z.out_stream)
        self.xy_writer = AnalogMultiChannelWriter(write_task_xy.out_stream)
        self.z_reader = AnalogSingleChannelReader(read_task.in_stream)

        self.xy_array = np.zeros((2, self.n_samples))
        self.z_array = np.zeros((4, self.n_samples))

        self.read_array = np.zeros(self.n_samples)

        self.setup_tasks()

    def setup_tasks(self):
        # Configure the channels

        # read channel is only the piezo position on board 1
        self.read_task.ai_channels.add_ai_voltage_chan(
            self.conf["z_board"]["read"]["channel"],
            min_val=self.conf["z_board"]["read"]["min_val"],
            max_val=self.conf["z_board"]["read"]["max_val"],
        )

        # write channels are on board 1: piezo and z galvos
        self.write_task_z.ao_channels.add_ao_voltage_chan(
            self.conf["z_board"]["write"]["channel"],
            min_val=self.conf["z_board"]["write"]["min_val"],
            max_val=self.conf["z_board"]["write"]["max_val"],
        )

        # on board 2: lateral galvos
        self.write_task_xy.ao_channels.add_ao_voltage_chan(
            self.conf["xy_board"]["write"]["channel"],
            min_val=self.conf["xy_board"]["write"]["min_val"],
            max_val=self.conf["xy_board"]["write"]["max_val"],
        )

        # Set the timing of both to the onboard clock so that they are synchronised
        self.read_task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            source="OnboardClock",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.n_samples,
        )
        self.write_task_z.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            source="OnboardClock",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.n_samples,
        )

        self.write_task_xy.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            source="OnboardClock",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.n_samples,
        )

        # This is necessary to synchronise reading and writing
        self.read_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            self.conf["z_board"]["sync"]["channel"], Edge.RISING
        )

    def start(self):
        self.read_task.start()
        self.write_task_xy.start()
        self.write_task_z.start()

    def write(self):
        self.z_writer.write_many_sample(self.z_array)
        self.xy_writer.write_many_sample(self.xy_array)

    def read(self):
        self.z_reader.read_many_sample(
            self.read_array, number_of_samples_per_channel=self.n_samples, timeout=1,
        )
        self.read_array[:] = self.read_array

    @property
    def z_piezo(self):
        return self.read_array / self.conf["piezo"]["scale"]

    @z_piezo.setter
    def z_piezo(self, waveform):
        self.z_array[0, :] = waveform * self.conf["piezo"]["scale"]

    @property
    def z_lateral(self):
        return self.z_array[1, :]

    @property
    def z_frontal(self):
        return self.z_array[2, :]

    @z_lateral.setter
    def z_lateral(self, waveform):
        self.z_array[1, :] = waveform

    @z_frontal.setter
    def z_frontal(self, waveform):
        self.z_array[2, :] = waveform

    @property
    def camera_trigger(self):
        return self.z_array[3, :]

    @camera_trigger.setter
    def camera_trigger(self, waveform):
        self.z_array[3, :] = waveform

    @property
    def xy_frontal(self):
        return self.xy_array[1, :]

    @xy_frontal.setter
    def xy_frontal(self, waveform):
        self.xy_array[1, :] = waveform

    @property
    def xy_lateral(self):
        return self.xy_array[0, :]

    @xy_lateral.setter
    def xy_lateral(self, waveform):
        self.xy_array[0, :] = waveform
