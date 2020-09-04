from sashimi.hardware.scanning.interface import (
    AbstractScanInterface,
    AbstractScanConfigurator,
)

from nidaqmx.task import Task
from nidaqmx.constants import Edge, AcquisitionType
from nidaqmx.errors import DaqError
from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter

import numpy as np


class NIScanConfigurator(AbstractScanConfigurator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __enter__(self):
        with Task() as read_task, Task() as write_task_z, Task() as write_task_xy:
            return NIBoards(
                self.n_samples, self.conf, read_task, write_task_z, write_task_xy
            )


class NIBoards(AbstractScanInterface):
    def __init__(self, n_samples, conf, read_task, write_task_z, write_task_xy):
        super().__init__(n_samples, conf)
        self.read_task = read_task
        self.write_task_xy = write_task_xy
        self.write_task_z = write_task_z

        self.z_writer = AnalogMultiChannelWriter(write_task_z.out_stream)
        self.xy_writer = AnalogMultiChannelWriter(write_task_xy.out_stream)
        self.z_reader = AnalogSingleChannelReader(read_task.in_stream)

        self.xy_array = np.zeros((2, n_samples))
        self.z_array = np.zeros((2, n_samples))

        self.read_array = np.zeros(n_samples)

        self.setup_tasks()

    def setup_tasks(self):
        # Configure the channels

        # read channel is only the piezo position on board 1
        self.read_task.ai_channels.add_ai_voltage_chan(
            self.conf["piezo"]["position_read"]["pos_chan"],
            min_val=self.conf["piezo"]["position_read"]["min_val"],
            max_val=self.conf["piezo"]["position_read"]["max_val"],
        )

        # write channels are on board 1: piezo and z galvos
        self.write_task_z.ao_channels.add_ao_voltage_chan(
            self.conf["piezo"]["position_write"]["pos_chan"],
            min_val=self.conf["piezo"]["position_write"]["min_val"],
            max_val=self.conf["piezo"]["position_write"]["max_val"],
        )

        # on board 2: lateral galvos
        self.write_task_xy.ao_channels.add_ao_voltage_chan(
            self.conf["galvo_lateral"]["write_position"]["pos_chan"],
            min_val=self.conf["galvo_lateral"]["write_position"]["min_val"],
            max_val=self.conf["galvo_lateral"]["write_position"]["max_val"],
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
            self.conf["piezo"]["synchronization"]["pos_chan"], Edge.RISING
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
        self.read_array[:] = (
            self.read_array / self.conf["piezo"]["synchronization"]["scale"]
        )

    @property
    def z_piezo(self):
        return self.read_array

    @z_piezo.setter
    def z_piezo(self, waveform):
        self.z_array[0, :] = waveform * self.conf["piezo"]["synchronization"]["scale"]

    @z_lateral.setter
    def z_lateral(self, waveform):
        self.z_array[1, :] = waveform

    @z_frontal.setter
    def z_frontal(self, waveform):
        self.z_array[2, :] = waveform

    @camera_trigger.setter
    def camera_trigger(self, waveform):
        self.z_array[3, :] = waveform
