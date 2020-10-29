from multiprocessing import Process, Event, Queue
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from queue import Empty
import flammkuchen as fl
import numpy as np
import shutil
import json
from arrayqueues.shared_arrays import ArrayQueue
import yagmail
from sashimi.config import read_config
conf = read_config()
import datetime

@dataclass
class SavingParameters:
    output_dir: Path = conf["default_paths"]["data"]
    n_planes: int = 1
    n_volumes: int = 10000
    chunk_size: int =  20
    optimal_chunk_MB_RAM: int = conf[
        "array_ram_MB"
    ]  # Experimental value, might be different for different machines.
    notification_email: str = "None"
    volumerate: float = 1
    voxel_size: tuple = (1, 1, 1)


@dataclass
class SavingStatus:
    target_params: SavingParameters
    i_in_chunk: int = 0
    i_volume: int = 0
    i_chunk: int = 0


class StackSaver(Process):
    def __init__(self, stop_event, duration_queue, triggered_frame_rate_queue_copy, max_queue_size=2000):
        super().__init__()
        self.stop_event = stop_event
        self.save_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.saving_signal = Event()
        self.saver_stopped_signal = Event()
        self.saving = False
        self.saving_parameter_queue = Queue()
        self.save_parameters: Optional[SavingParameters] = SavingParameters()
        self.i_in_chunk = 0
        self.i_chunk = 0
        self.i_plane = 0
        self.i_volume = 0
        self.current_data = None
        self.saved_status_queue = Queue()
        self.frame_shape = None
        self.dtype = np.uint16
        self.duration_queue = duration_queue
        self.conf = read_config()
        self.triggered_frame_rate_queue_copy =triggered_frame_rate_queue_copy
        self.frame_rate = None

    def run(self):
        while not self.stop_event.is_set():
            if self.saving_signal.is_set() and self.save_parameters is not None:
                self.save_loop()
            else:
                self.receive_save_parameters()

    def save_loop(self):
        # remove files if some are found at the save location
        Path(self.save_parameters.output_dir).mkdir(parents=True, exist_ok=True)
        if (
            Path(self.save_parameters.output_dir) / "original" / "stack_metadata.json"
        ).is_file():
            shutil.rmtree(Path(self.save_parameters.output_dir) / "original")

        (Path(self.save_parameters.output_dir) / "original").mkdir(
            parents=True, exist_ok=True
        )
        self.i_in_chunk = 0
        self.i_chunk = 0
        self.i_volume = 0
        self.current_data = None
        start = datetime.datetime.now()

        while (
                self.i_volume < self.save_parameters.n_volumes
                and self.saving_signal.is_set()
                and not self.stop_event.is_set()
        ):
            self.receive_save_parameters()

            try:
                frame = self.save_queue.get(timeout=0.01)
                self.fill_dataset(frame)
            except Empty:
                pass

        if self.i_volume > 0:
            if self.i_in_chunk != 0:
                self.save_chunk()
            self.update_saved_status_queue()
            self.finalize_dataset()
            self.current_data = None
            if self.saving_signal.is_set():
                print("Done: ", datetime.datetime.now() - start)
                    # self.send_email_end()

        self.saving_signal.clear()
        self.save_parameters = None
        self.saver_stopped_signal.set()

    def send_email_end(self):
        sender_email = conf["email"]["user"]  # TODO this should go to thecolonel
        # TODO: Send email every x minutes with image like in 2P
        receiver_email = self.save_parameters.notification_email
        subject = "Your lightsheet experiment is complete"
        sender_password = conf["email"]["password"]

        yag = yagmail.SMTP(user=sender_email, password=sender_password)

        body = [
            "Hey!",
            "\n",
            "Your lightsheet experiment has finished and was a success! Come pick up your little fish",
            "\n" "fishgitbot",
        ]
        try:
            yag.send(
                to=receiver_email, subject=subject, contents=body,
            )
        except (
            yagmail.error.YagAddressError,
            yagmail.error.YagConnectionClosed,
            yagmail.error.YagInvalidEmailAddress,
        ):
            pass

    def fill_dataset(self, volume):
        if self.current_data is None:
            self.calculate_optimal_size(volume)
            self.current_data = np.empty(
                (self.save_parameters.chunk_size, *volume.shape), dtype=self.dtype,
            )

        self.current_data[self.i_in_chunk, :, :, :] = volume

        self.i_volume += 1
        self.i_in_chunk += 1
        self.update_saved_status_queue()

        if self.i_in_chunk == self.save_parameters.chunk_size:
            self.save_chunk()

    def update_saved_status_queue(self):
        self.saved_status_queue.put(
            SavingStatus(
                target_params=self.save_parameters,
                i_in_chunk=self.i_in_chunk,
                i_chunk=self.i_chunk,
                i_volume=self.i_volume,
            )
        )


    def finalize_dataset(self):
        with open(
            (
                Path(self.save_parameters.output_dir)
                / "original"
                / "stack_metadata.json"
            ),
            "w",
        ) as f:
            json.dump(
                {
                    "shape_full": (
                        self.save_parameters.n_volumes,
                        *self.current_data.shape[1:],
                    ),
                    "shape_block": (
                        self.save_parameters.chunk_size,
                        *self.current_data.shape[1:],
                    ),
                    "crop_start": [0, 0, 0, 0],
                    "crop_end": [0, 0, 0, 0],
                    "padding": [0, 0, 0, 0],
                    "voxel_size": self.save_parameters.voxel_size,
                },
                f,
            )

    def save_chunk(self):
        fl.save(
            Path(self.save_parameters.output_dir)
            / "original/{:04d}.h5".format(self.i_chunk),
            {"stack_4D": self.current_data[: self.i_in_chunk, :, :, :]},
            compression="blosc",
        )
        self.i_in_chunk = 0
        self.i_chunk += 1

    def calculate_optimal_size(self, volume):
        if self.dtype == np.uint16:
            array_megabytes = (
                2 * volume.shape[0] * volume.shape[1] * volume.shape[2] / 1048576
            )
        else:
            raise TypeError("Saving data type not supported. Only uint16 is supported")
        self.save_parameters.chunk_size = int(
            self.save_parameters.optimal_chunk_MB_RAM / array_megabytes
        )

    def receive_save_parameters(self):
        try:
            self.frame_rate = self.triggered_frame_rate_queue_copy.get(timeout=0.001)
        except Empty:
            pass
        try:
            self.save_parameters = self.saving_parameter_queue.get(timeout=0.001)
        except Empty:
            pass
        try:
            new_duration = self.duration_queue.get(timeout=0.001)
            # if self.conf["chirashi"]:
            #     self.save_parameters.n_volumes = int(round(
            #         np.ceil(int(self.frame_rate) * new_duration)))
            # else:
            self.save_parameters.n_volumes = int(
                np.ceil(self.save_parameters.volumerate * new_duration)
            )
        except Empty:
            pass
